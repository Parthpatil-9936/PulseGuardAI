import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.session import get_db
from app.models.patient import Patient, Bed
from app.models.note import MedicalNote
from app.models.alert import Alert
from app.models.assignment import PatientAssignment
from app.models.user import User
from app.schemas.patient import PatientOut, BedOut, MedicalNoteCreate, MedicalNoteOut
from app.schemas.alert import AlertOut
from app.core.dependencies import get_current_user, verify_patient_access
from app.services.telemetry import telemetry_service
from app.services.audit_service import append_audit_log

router = APIRouter(tags=["Patients & Ward Beds"])


@router.get("/beds", response_model=List[BedOut])
async def list_beds(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Bed).order_by(Bed.id.asc())
    res = await db.execute(stmt)
    beds = res.scalars().all()

    out = []
    for b in beds:
        vitals = telemetry_service.current_vitals.get(b.id)
        out.append(BedOut(
            id=b.id,
            ward=b.ward,
            device_id=b.device_id,
            status="no_signal" if vitals and vitals.get("lead_status") == "disconnected" else b.status,
            patient_id=b.patient_id,
            vitals=vitals
        ))
    return out


@router.get("/patients", response_model=List[PatientOut])
async def list_patients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Patient).order_by(Patient.id.asc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/patients/{id}", response_model=PatientOut)
async def get_patient(
    id: str,
    user: User = Depends(verify_patient_access),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Patient).where(Patient.id == id)
    res = await db.execute(stmt)
    patient = res.scalars().first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


@router.get("/patients/{id}/vitals")
async def get_patient_vitals(
    id: str,
    user: User = Depends(verify_patient_access),
    db: AsyncSession = Depends(get_db)
):
    # Find patient's bed
    stmt = select(Bed).where(Bed.patient_id == id)
    res = await db.execute(stmt)
    bed = res.scalars().first()

    bed_id = bed.id if bed else id.replace("pat_", "")
    window = await telemetry_service.get_recent_window(bed_id)
    latest = telemetry_service.current_vitals.get(bed_id)

    return {
        "patient_id": id,
        "bed_id": bed_id,
        "latest": latest,
        "window": window,
    }


@router.get("/patients/{id}/alerts", response_model=List[AlertOut])
async def get_patient_alerts(
    id: str,
    user: User = Depends(verify_patient_access),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Alert).where(Alert.patient_id == id).order_by(Alert.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.get("/patients/{id}/notes", response_model=List[MedicalNoteOut])
async def get_patient_notes(
    id: str,
    user: User = Depends(verify_patient_access),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(MedicalNote).where(MedicalNote.patient_id == id).order_by(MedicalNote.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@router.post("/patients/{id}/notes", response_model=MedicalNoteOut)
async def create_patient_note(
    id: str,
    req: MedicalNoteCreate,
    current_user: User = Depends(verify_patient_access),
    db: AsyncSession = Depends(get_db)
):
    # Verify patient exists
    stmt_p = select(Patient).where(Patient.id == id)
    res_p = await db.execute(stmt_p)
    if not res_p.scalars().first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    note_id = f"note_{uuid.uuid4().hex[:12]}"
    note = MedicalNote(
        id=note_id,
        patient_id=id,
        author_id=current_user.id,
        note_type=req.note_type,
        content=req.content,
        created_at=datetime.datetime.utcnow()
    )
    db.add(note)

    await append_audit_log(
        session=db,
        action="MEDICAL_NOTE_CREATED",
        bed_id=None,
        clinician_id=current_user.id,
        metadata={"patient_id": id, "note_type": req.note_type}
    )

    await db.commit()
    await db.refresh(note)
    return note
