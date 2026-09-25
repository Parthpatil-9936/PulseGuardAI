import datetime
import logging
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.assignment import PatientAssignment
from app.models.emergency_access import EmergencyAccess
from app.services.audit_service import append_audit_log

logger = logging.getLogger("pulseguard.authz")


async def check_patient_access(user: User, patient_id: str, session: AsyncSession) -> bool:
    """
    Evaluates fine-grained authorization to access patient records/telemetry.
    Enforces RBAC + Primary Assignment + Break-Glass Emergency Access with request-time auto-expiry.
    """
    role = user.role.lower()

    # Admin: Unit-wide oversight and audit access
    if role == "admin":
        return True

    # Nurse: Ward-wide bedside monitoring access across all ward beds
    if role == "nurse":
        return True

    # Doctor: Requires active assignment OR valid emergency break-glass grant
    if role == "doctor":
        # 1. Check active, non-revoked primary patient assignment
        stmt_assign = select(PatientAssignment).where(
            and_(
                PatientAssignment.patient_id == patient_id,
                PatientAssignment.doctor_id == user.id,
                PatientAssignment.status == "active"
            )
        )
        res_assign = await session.execute(stmt_assign)
        active_assignment = res_assign.scalars().first()

        if active_assignment:
            return True

        # 2. Check emergency access grants (request-time auto-denial after expires_at)
        now = datetime.datetime.utcnow()
        stmt_emerg = select(EmergencyAccess).where(
            and_(
                EmergencyAccess.patient_id == patient_id,
                EmergencyAccess.clinician_id == user.id,
                EmergencyAccess.status == "active"
            )
        )
        res_emerg = await session.execute(stmt_emerg)
        emergency_grant = res_emerg.scalars().first()

        if emergency_grant:
            # Enforce request-time expiration check
            if emergency_grant.expires_at <= now:
                emergency_grant.status = "expired"
                await session.commit()

                # Write audit event the first time an expired grant is hit
                await append_audit_log(
                    session=session,
                    action="EMERGENCY_ACCESS_AUTO_EXPIRED",
                    bed_id=None,
                    clinician_id=user.id,
                    metadata={
                        "patient_id": patient_id,
                        "grant_id": emergency_grant.id,
                        "expired_at": emergency_grant.expires_at.isoformat()
                    }
                )
                logger.info(f"Emergency grant {emergency_grant.id} expired at request time for Dr. {user.id}.")
                return False

            # Active, non-expired emergency grant
            return True

    # Revoked assignments or unassigned clinicians fail authorization
    return False
