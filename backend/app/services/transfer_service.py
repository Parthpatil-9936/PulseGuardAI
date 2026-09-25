import datetime
import uuid
import logging
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.transfer import TransferRequest
from app.models.assignment import PatientAssignment
from app.models.notification import Notification
from app.models.user import User
from app.services.audit_service import append_audit_log

logger = logging.getLogger("pulseguard.transfers")


async def approve_patient_transfer(
    transfer_id: str,
    decided_by: User,
    session: AsyncSession
) -> TransferRequest:
    """
    Executes atomic doctor patient transfer handover inside a single DB transaction.
    INVARIANT: Revoke old assignment -> Create new assignment -> Commit.
    Rolls back entirely on any failure, preventing split-brain assignments.
    Writes audit event and notifications.
    """
    try:
        stmt = select(TransferRequest).where(TransferRequest.id == transfer_id)
        res = await session.execute(stmt)
        transfer = res.scalars().first()

        if not transfer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer request not found")

        if transfer.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transfer request is already resolved ({transfer.status})"
            )

        now = datetime.datetime.utcnow()

        # Step 1: Revoke existing active assignments for this patient
        stmt_active = select(PatientAssignment).where(
            and_(
                PatientAssignment.patient_id == transfer.patient_id,
                PatientAssignment.status == "active"
            )
        )
        res_active = await session.execute(stmt_active)
        current_assignments = res_active.scalars().all()

        for old_assign in current_assignments:
            old_assign.status = "revoked"
            old_assign.revoked_at = now

        # Step 2: Create new active primary assignment for destination doctor
        new_assignment_id = f"asgn_{uuid.uuid4().hex[:12]}"
        new_assignment = PatientAssignment(
            id=new_assignment_id,
            patient_id=transfer.patient_id,
            doctor_id=transfer.to_doctor_id,
            status="active",
            assigned_at=now,
        )
        session.add(new_assignment)

        # Step 3: Update transfer record
        transfer.status = "approved"
        transfer.decided_by = decided_by.id
        transfer.decided_at = now

        # Step 4: Add notifications for both doctors
        notif_from = Notification(
            id=f"notif_{uuid.uuid4().hex[:12]}",
            user_id=transfer.from_doctor_id,
            event_type="TRANSFER_APPROVED",
            payload_ref=f"Handover of patient {transfer.patient_id} to Dr. {transfer.to_doctor_id} approved.",
            status="unread",
            created_at=now
        )
        notif_to = Notification(
            id=f"notif_{uuid.uuid4().hex[:12]}",
            user_id=transfer.to_doctor_id,
            event_type="TRANSFER_RECEIVED",
            payload_ref=f"You are now primary attending for patient {transfer.patient_id}.",
            status="unread",
            created_at=now
        )
        session.add(notif_from)
        session.add(notif_to)

        # Step 5: Append audit log entry
        await append_audit_log(
            session=session,
            action="TRANSFER_APPROVED",
            bed_id=None,
            clinician_id=decided_by.id,
            metadata={
                "transfer_id": transfer.id,
                "patient_id": transfer.patient_id,
                "from_doctor": transfer.from_doctor_id,
                "to_doctor": transfer.to_doctor_id,
                "new_assignment_id": new_assignment_id,
            }
        )

        # Commit single atomic transaction
        await session.commit()
        await session.refresh(transfer)
        logger.info(f"Transfer {transfer_id} approved atomically: {transfer.from_doctor_id} -> {transfer.to_doctor_id}")
        return transfer

    except Exception as e:
        await session.rollback()
        logger.error(f"Transfer approval failed. Transaction rolled back completely: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transfer atomic transaction failed: {str(e)}"
        )


async def reject_patient_transfer(
    transfer_id: str,
    rejection_reason: str,
    decided_by: User,
    session: AsyncSession
) -> TransferRequest:
    stmt = select(TransferRequest).where(TransferRequest.id == transfer_id)
    res = await session.execute(stmt)
    transfer = res.scalars().first()

    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer request not found")

    if transfer.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transfer request is already resolved ({transfer.status})"
        )

    now = datetime.datetime.utcnow()
    transfer.status = "rejected"
    transfer.decided_by = decided_by.id
    transfer.decided_at = now
    transfer.rejection_reason = rejection_reason

    notif = Notification(
        id=f"notif_{uuid.uuid4().hex[:12]}",
        user_id=transfer.from_doctor_id,
        event_type="TRANSFER_REJECTED",
        payload_ref=f"Transfer for patient {transfer.patient_id} rejected: {rejection_reason}",
        status="unread",
        created_at=now
    )
    session.add(notif)

    await append_audit_log(
        session=session,
        action="TRANSFER_REJECTED",
        bed_id=None,
        clinician_id=decided_by.id,
        metadata={
            "transfer_id": transfer.id,
            "patient_id": transfer.patient_id,
            "reason": rejection_reason,
        }
    )

    await session.commit()
    await session.refresh(transfer)
    return transfer
