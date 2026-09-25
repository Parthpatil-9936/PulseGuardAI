import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.transfer import TransferRequest
from app.models.user import User
from app.models.patient import Patient
from app.schemas.transfer import TransferCreate, TransferOut, TransferRejectRequest
from app.core.dependencies import get_current_user, require_role
from app.services.transfer_service import approve_patient_transfer, reject_patient_transfer
from app.services.audit_service import append_audit_log

router = APIRouter(prefix="/transfers", tags=["Doctor Patient Transfers"])


@router.post("", response_model=TransferOut, status_code=status.HTTP_201_CREATED)
async def create_transfer_request(
    req: TransferCreate,
    current_user: User = Depends(require_role(["doctor", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    # Verify patient exists
    stmt_p = select(Patient).where(Patient.id == req.patient_id)
    res_p = await db.execute(stmt_p)
    patient = res_p.scalars().first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    # Verify target doctor exists
    stmt_d = select(User).where(User.id == req.to_doctor_id)
    res_d = await db.execute(stmt_d)
    to_doctor = res_d.scalars().first()
    if not to_doctor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target destination doctor not found")

    transfer_id = f"tr_{uuid.uuid4().hex[:12]}"
    transfer = TransferRequest(
        id=transfer_id,
        patient_id=req.patient_id,
        from_doctor_id=current_user.id,
        to_doctor_id=req.to_doctor_id,
        reason=req.reason,
        priority=req.priority or "Routine",
        status="pending",
        created_at=datetime.datetime.utcnow()
    )
    db.add(transfer)

    await append_audit_log(
        session=db,
        action="TRANSFER_REQUEST_SUBMITTED",
        bed_id=None,
        clinician_id=current_user.id,
        metadata={
            "transfer_id": transfer_id,
            "patient_id": req.patient_id,
            "to_doctor_id": req.to_doctor_id,
            "priority": req.priority,
        }
    )

    await db.commit()
    await db.refresh(transfer)
    return transfer


@router.get("", response_model=List[TransferOut])
async def list_transfers(
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(TransferRequest).order_by(TransferRequest.created_at.desc())
    if status:
        stmt = stmt.where(TransferRequest.status == status.lower())

    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/{id}/approve", response_model=TransferOut)
async def approve_transfer(
    id: str,
    current_user: User = Depends(require_role(["admin", "doctor"])),
    db: AsyncSession = Depends(get_db)
):
    transfer = await approve_patient_transfer(
        transfer_id=id,
        decided_by=current_user,
        session=db
    )
    return transfer


@router.post("/{id}/reject", response_model=TransferOut)
async def reject_transfer(
    id: str,
    req: TransferRejectRequest,
    current_user: User = Depends(require_role(["admin", "doctor"])),
    db: AsyncSession = Depends(get_db)
):
    if not req.reason.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A clinical rejection reason is mandatory."
        )

    transfer = await reject_patient_transfer(
        transfer_id=id,
        rejection_reason=req.reason.strip(),
        decided_by=current_user,
        session=db
    )
    return transfer
