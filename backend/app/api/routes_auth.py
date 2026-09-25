from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.models.assignment import PatientAssignment
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.core.security import verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.services.audit_service import append_audit_log

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == req.email.lower().strip())
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user or not verify_password(req.password, user.credentials_ref):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect staff email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    # Append audit log for authentication
    await append_audit_log(
        session=db,
        action="LOGIN",
        bed_id=None,
        clinician_id=user.id,
        metadata={"role": user.role, "email": user.email}
    )

    access_token = create_access_token(subject=user.id, role=user.role)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        name=user.name
    )


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Fetch active assigned patients for doctor
    assigned_patients = []
    if current_user.role.lower() == "doctor":
        stmt = select(PatientAssignment).where(
            PatientAssignment.doctor_id == current_user.id,
            PatientAssignment.status == "active"
        )
        res = await db.execute(stmt)
        assigned_patients = [a.patient_id for a in res.scalars().all()]

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "status": current_user.status,
        "assigned_patients": assigned_patients,
    }
