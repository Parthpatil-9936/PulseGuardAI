import datetime
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.patient import Patient, Bed
from app.models.assignment import PatientAssignment
from app.core.security import get_password_hash

logger = logging.getLogger("pulseguard.seed")


async def seed_initial_data(session: AsyncSession):
    # 1. Seed Users if not present
    stmt = select(User).limit(1)
    res = await session.execute(stmt)
    if res.scalars().first():
        return  # Already seeded

    logger.info("Seeding initial clinical demo dataset...")

    users = [
        User(
            id="usr_doc_01",
            name="Dr. Sarah Chen, MD",
            email="dr.chen@pulseguard.icu",
            role="doctor",
            status="active",
            credentials_ref=get_password_hash("doctor123"),
            created_at=datetime.datetime.utcnow()
        ),
        User(
            id="usr_doc_02",
            name="Dr. Marcus Vance, MD",
            email="dr.vance@pulseguard.icu",
            role="doctor",
            status="active",
            credentials_ref=get_password_hash("doctor123"),
            created_at=datetime.datetime.utcnow()
        ),
        User(
            id="usr_nur_01",
            name="Priya Patel, RN",
            email="priya.rn@pulseguard.icu",
            role="nurse",
            status="active",
            credentials_ref=get_password_hash("nurse123"),
            created_at=datetime.datetime.utcnow()
        ),
        User(
            id="usr_adm_01",
            name="Alex Rivera",
            email="admin.rivera@pulseguard.icu",
            role="admin",
            status="active",
            credentials_ref=get_password_hash("admin123"),
            created_at=datetime.datetime.utcnow()
        )
    ]
    for u in users:
        session.add(u)

    # 2. Seed Patients and Beds (10 beds)
    patients_data = [
        ("pat_01", "01", "Eleanor Vance", "EV", 72, "Female", "Post-CABG (Coronary Artery Bypass)", "usr_doc_01"),
        ("pat_02", "02", "Marcus Sterling", "MS", 58, "Male", "Acute Decompensated Heart Failure", "usr_doc_01"),
        ("pat_03", "03", "Harold Gomez", "HG", 64, "Male", "Bilateral Pneumonia / ARDS", "usr_doc_02"),
        ("pat_04", "04", "Julian Drake", "JD", 69, "Male", "Septic Shock / Hypoxemia", "usr_doc_01"),
        ("pat_05", "05", "Rosa Martinez", "RM", 45, "Female", "Post-operative Cholecystectomy", "usr_doc_02"),
        ("pat_06", "06", "Thomas Wright", "TW", 81, "Male", "Severe COPD Exacerbation", "usr_doc_02"),
        ("pat_07", "07", "Aaliyah Khan", "AK", 33, "Female", "Diabetic Ketoacidosis (DKA)", "usr_doc_01"),
        ("pat_08", "08", "Robert Lang", "RL", 59, "Male", "Observation / Telemetry artifact", "usr_doc_02"),
        ("pat_09", "09", "Clara Oswald", "CO", 61, "Female", "Subdural Hematoma (Neuro ICU)", "usr_doc_02"),
        ("pat_10", "10", "David Zhang", "DZ", 50, "Male", "Anterior STEMI s/p Stenting", "usr_doc_01"),
    ]

    for p_id, bed_id, name, initials, age, gender, diag, doc_id in patients_data:
        patient = Patient(
            id=p_id,
            external_ref=f"MRN-{bed_id}982",
            demographics={
                "name": name,
                "initials": initials,
                "age": age,
                "gender": gender,
                "diagnosis": diag,
                "code_status": "Full Code"
            },
            status="admitted",
            created_at=datetime.datetime.utcnow()
        )
        session.add(patient)

        bed = Bed(
            id=bed_id,
            ward="Critical Care Unit 4",
            device_id=f"IOT-MON-B{bed_id}",
            status="occupied",
            patient_id=p_id
        )
        session.add(bed)

        assignment = PatientAssignment(
            id=f"asgn_{bed_id}",
            patient_id=p_id,
            doctor_id=doc_id,
            status="active",
            assigned_at=datetime.datetime.utcnow()
        )
        session.add(assignment)

    await session.commit()
    logger.info("Successfully seeded 4 users, 10 patients, 10 beds, and active physician assignments.")
