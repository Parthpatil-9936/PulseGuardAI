import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.emergency_access import EmergencyAccess
from app.models.user import User
from app.schemas.alert import EmergencyAccessCreate, EmergencyAccessOut, AuditLogOut
from app.schemas.auth import UserOut, UserCreate
from app.core.dependencies import get_current_user, require_role
from app.core.security import get_password_hash
from app.services.audit_service import append_audit_log, verify_chain

router = APIRouter(tags=["Admin Operations, Audit & Emergency Access"])


# 1. Cryptographic Audit Ledger
@router.get("/audit-logs")
async def list_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AuditLog).order_by(AuditLog.seq_id.desc()).limit(limit)
    res = await db.execute(stmt)
    logs = res.scalars().all()

    return [
        {
            "seq_id": log.seq_id,
            "timestamp": log.timestamp.isoformat(),
            "action": log.action,
            "bed_id": log.bed_id,
            "clinician_id": log.clinician_id,
            "previous_hash": log.previous_hash,
            "hash": log.hash,
            "metadata": log.metadata_json,
            "gap_marker": log.gap_marker,
        }
        for log in logs
    ]


@router.get("/audit-logs/verify")
@router.post("/audit-logs/verify")
async def verify_audit_chain(
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Walks entire audit ledger and verifies SHA-256 cryptographic chain integrity.
    """
    result = await verify_chain(db)
    return result


# 2. Emergency "Break-Glass" Access
@router.post("/emergency-access", response_model=EmergencyAccessOut, status_code=status.HTTP_201_CREATED)
async def grant_emergency_access(
    req: EmergencyAccessCreate,
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    now = datetime.datetime.utcnow()
    duration_mins = max(1, min(req.duration_minutes, 480))  # Max 8h
    expires_at = now + datetime.timedelta(minutes=duration_mins)

    grant_id = f"bg_{uuid.uuid4().hex[:12]}"
    grant = EmergencyAccess(
        id=grant_id,
        patient_id=req.patient_id,
        clinician_id=req.clinician_id,
        reason=req.reason,
        starts_at=now,
        expires_at=expires_at,
        status="active"
    )
    db.add(grant)

    await append_audit_log(
        session=db,
        action="EMERGENCY_ACCESS_GRANTED",
        bed_id=None,
        clinician_id=req.clinician_id,
        metadata={
            "grant_id": grant_id,
            "patient_id": req.patient_id,
            "duration_minutes": duration_mins,
            "reason": req.reason,
            "granted_by": current_user.id
        }
    )

    await db.commit()
    await db.refresh(grant)
    return grant


@router.get("/emergency-access", response_model=List[EmergencyAccessOut])
async def list_emergency_grants(
    current_user: User = Depends(require_role(["admin", "doctor"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(EmergencyAccess).order_by(EmergencyAccess.starts_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.delete("/emergency-access/{id}", response_model=EmergencyAccessOut)
async def revoke_emergency_access(
    id: str,
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(EmergencyAccess).where(EmergencyAccess.id == id)
    res = await db.execute(stmt)
    grant = res.scalars().first()

    if not grant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Emergency grant not found")

    grant.status = "revoked"
    grant.revoked_at = datetime.datetime.utcnow()

    await append_audit_log(
        session=db,
        action="EMERGENCY_ACCESS_REVOKED",
        bed_id=None,
        clinician_id=grant.clinician_id,
        metadata={"grant_id": grant.id, "revoked_by": current_user.id}
    )

    await db.commit()
    await db.refresh(grant)
    return grant


# 3. Staff User Management
@router.get("/users", response_model=List[UserOut])
async def list_users(
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).order_by(User.name.asc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    req: UserCreate,
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    # Check if email exists
    stmt_check = select(User).where(User.email == req.email.lower().strip())
    res_check = await db.execute(stmt_check)
    if res_check.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    user = User(
        id=user_id,
        name=req.name,
        email=req.email.lower().strip(),
        role=req.role.lower(),
        status="active",
        credentials_ref=get_password_hash(req.password),
        created_at=datetime.datetime.utcnow()
    )
    db.add(user)

    await append_audit_log(
        session=db,
        action="USER_PROVISIONED",
        bed_id=None,
        clinician_id=current_user.id,
        metadata={"new_user_id": user_id, "role": req.role}
    )

    await db.commit()
    await db.refresh(user)
    return user
