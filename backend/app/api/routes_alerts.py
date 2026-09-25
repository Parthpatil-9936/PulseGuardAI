import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertOut, AlertAcknowledgeRequest, MuteRequest
from app.core.dependencies import get_current_user, require_role
from app.services.audit_service import append_audit_log
from app.services.mute_service import mute_manager

router = APIRouter(tags=["Alerts & Siren Mute"])


@router.get("/alerts", response_model=List[AlertOut])
async def list_alerts(
    status: Optional[str] = Query(None, description="Filter by status: active, acknowledged, resolved"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Alert).order_by(Alert.created_at.desc())
    if status:
        stmt = stmt.where(Alert.status == status.lower())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/alerts/{id}/acknowledge", response_model=AlertOut)
async def acknowledge_alert(
    id: str,
    req: AlertAcknowledgeRequest,
    current_user: User = Depends(require_role(["doctor", "nurse", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Alert).where(Alert.id == id)
    res = await db.execute(stmt)
    alert = res.scalars().first()

    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    now = datetime.datetime.utcnow()
    alert.status = "acknowledged"
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = now
    alert.ack_note = req.note

    # Write mandatory audit event
    await append_audit_log(
        session=db,
        action="ALERT_ACKNOWLEDGED",
        bed_id=alert.bed_id,
        clinician_id=current_user.id,
        metadata={
            "alert_id": alert.id,
            "tier": alert.tier,
            "patient_id": alert.patient_id,
            "note": req.note,
        }
    )

    await db.commit()
    await db.refresh(alert)
    return alert


@router.post("/mute")
async def request_alarm_mute(
    req: MuteRequest,
    current_user: User = Depends(require_role(["doctor", "nurse", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Siren Mute endpoint with server-enforced anti-tamper clamp.
    Any requested duration is clamped to <= 300 seconds (5 minutes).
    """
    mute_status = mute_manager.request_mute(
        bed_id=req.bed_id,
        requested_duration_seconds=req.duration_seconds
    )

    # Append audit log recording requested vs clamped duration
    await append_audit_log(
        session=db,
        action="ALARM_MUTE_CLAMPED_300S",
        bed_id=req.bed_id,
        clinician_id=current_user.id,
        metadata=mute_status
    )

    return mute_status
