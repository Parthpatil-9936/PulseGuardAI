import pytest
from httpx import AsyncClient
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.assignment import PatientAssignment


@pytest.mark.asyncio
async def test_transfer_workflow_atomic_handover(client: AsyncClient, test_db: AsyncSession, auth_headers):
    headers_alice = auth_headers("doc_1", "doctor")
    headers_admin = auth_headers("admin_1", "admin")

    # 1. Dr. Alice creates transfer request to Dr. Bob (doc_2)
    resp_create = await client.post(
        "/transfers",
        headers=headers_alice,
        json={
            "patient_id": "pat_1",
            "to_doctor_id": "doc_2",
            "reason": "Cardiology subspecialty consultation required",
            "priority": "Urgent"
        }
    )
    assert resp_create.status_code == 201
    transfer_data = resp_create.json()
    transfer_id = transfer_data["id"]
    assert transfer_data["status"] == "pending"

    # 2. Admin approves transfer request
    resp_approve = await client.post(f"/transfers/{transfer_id}/approve", headers=headers_admin)
    assert resp_approve.status_code == 200
    assert resp_approve.json()["status"] == "approved"

    # 3. Verify single atomic transaction invariants in DB:
    # Old assignment (doc_1) must be revoked
    stmt_old = select(PatientAssignment).where(
        and_(PatientAssignment.patient_id == "pat_1", PatientAssignment.doctor_id == "doc_1")
    )
    res_old = await test_db.execute(stmt_old)
    old_assign = res_old.scalars().first()
    assert old_assign.status == "revoked"
    assert old_assign.revoked_at is not None

    # New assignment (doc_2) must be active
    stmt_new = select(PatientAssignment).where(
        and_(PatientAssignment.patient_id == "pat_1", PatientAssignment.doctor_id == "doc_2")
    )
    res_new = await test_db.execute(stmt_new)
    new_assign = res_new.scalars().first()
    assert new_assign is not None
    assert new_assign.status == "active"

    # Ensure EXACTLY ONE active assignment exists for pat_1 (no split-brain)
    stmt_all_active = select(PatientAssignment).where(
        and_(PatientAssignment.patient_id == "pat_1", PatientAssignment.status == "active")
    )
    res_active = await test_db.execute(stmt_all_active)
    active_assignments = res_active.scalars().all()
    assert len(active_assignments) == 1
    assert active_assignments[0].doctor_id == "doc_2"

    # 4. Dr. Bob now has access to pat_1; Dr. Alice is now denied
    headers_bob = auth_headers("doc_2", "doctor")
    resp_bob = await client.get("/patients/pat_1", headers=headers_bob)
    assert resp_bob.status_code == 200

    resp_alice_denied = await client.get("/patients/pat_1", headers=headers_alice)
    assert resp_alice_denied.status_code == 403
