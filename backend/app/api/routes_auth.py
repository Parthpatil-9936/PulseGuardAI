from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import uuid
from app.db.session import get_db
from app.models.user import User
from app.models.assignment import PatientAssignment
from app.schemas.auth import LoginRequest, TokenResponse, UserOut, UserCreate
from app.core.security import verify_password, create_access_token, get_password_hash
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


@router.post("/register", response_model=TokenResponse)
async def register(req: UserCreate, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == req.email.lower().strip())
    res = await db.execute(stmt)
    if res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    user_id = f"usr_{uuid.uuid4().hex[:8]}"
    hashed_pwd = get_password_hash(req.password)
    
    new_user = User(
        id=user_id,
        name=req.name,
        email=req.email.lower().strip(),
        role=req.role.lower(),
        credentials_ref=hashed_pwd,
        status="active"
    )
    db.add(new_user)
    await db.commit()
    
    # Append audit log for registration
    await append_audit_log(
        session=db,
        action="USER_REGISTERED",
        bed_id=None,
        clinician_id=new_user.id,
        metadata={"role": new_user.role, "email": new_user.email}
    )

    access_token = create_access_token(subject=new_user.id, role=new_user.role)
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        role=new_user.role,
        user_id=new_user.id,
        name=new_user.name
    )


@router.post("/google", response_model=TokenResponse)
async def google_auth(req: dict, db: AsyncSession = Depends(get_db)):
    email = req.get("email", "").lower().strip()
    name = req.get("name", "Google User")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
        
    stmt = select(User).where(User.email == email)
    res = await db.execute(stmt)
    user = res.scalars().first()
    
    if not user:
        # Auto-register google user
        user_id = f"usr_google_{uuid.uuid4().hex[:8]}"
        user = User(
            id=user_id,
            name=name,
            email=email,
            role="doctor", # Default role
            credentials_ref="google_oauth",
            status="active"
        )
        db.add(user)
        await db.commit()
        
        await append_audit_log(
            session=db,
            action="USER_REGISTERED_GOOGLE",
            bed_id=None,
            clinician_id=user.id,
            metadata={"role": user.role, "email": user.email}
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    await append_audit_log(
        session=db,
        action="LOGIN_GOOGLE",
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


@router.get("/users")
async def list_users_for_ui(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns a list of all active users (id, name, role, status only — no credentials).
    Accessible to any authenticated user so the frontend can populate doctor dropdowns.
    """
    stmt = select(User).order_by(User.name.asc())
    res = await db.execute(stmt)
    return [
        {"id": u.id, "name": u.name, "role": u.role, "status": u.status, "email": u.email}
        for u in res.scalars().all()
    ]
