import datetime
import logging
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.patient import Patient, Bed
from app.models.assignment import PatientAssignment
from app.models.transfer import TransferRequest
from app.models.emergency_access import EmergencyAccess
from app.models.note import MedicalNote
from app.models.alert import Alert
from app.models.audit import AuditLog
from app.core.security import get_password_hash
from app.services.audit_service import calculate_hash, GENESIS_HASH

logger = logging.getLogger("pulseguard.seed")


async def seed_initial_data(session: AsyncSession, force: bool = False):
    # Check if already seeded (unless force is True)
    if not force:
        stmt = select(User).limit(1)
        res = await session.execute(stmt)
        if res.scalars().first():
            # Check if transfers are also seeded
            t_stmt = select(TransferRequest).limit(1)
            t_res = await session.execute(t_stmt)
            if t_res.scalars().first():
                return  # Fully seeded

    logger.info("Seeding comprehensive clinical demo dataset (Zero Nurse, Rich Synthetic Data)...")

    # If force, clean up existing data
    if force:
        for model in [AuditLog, Alert, MedicalNote, EmergencyAccess, TransferRequest, PatientAssignment, Bed, Patient, User]:
            await session.execute(delete(model))
        await session.commit()

    now = datetime.datetime.utcnow()

    # 1. Seed Users (Doctor and Admin roles only - Zero Nurse)
    users = [
        User(
            id="usr_doc_01",
            name="Dr. Sarah Chen, MD",
            email="dr.chen@pulseguard.icu",
            role="doctor",
            status="active",
            credentials_ref=get_password_hash("doctor123"),
            created_at=now - datetime.timedelta(days=7)
        ),
        User(
            id="usr_doc_02",
            name="Dr. Marcus Vance, MD",
            email="dr.vance@pulseguard.icu",
            role="doctor",
            status="active",
            credentials_ref=get_password_hash("doctor123"),
            created_at=now - datetime.timedelta(days=7)
        ),
        User(
            id="usr_doc_03",
            name="Dr. Elena Rostova, MD",
            email="dr.rostova@pulseguard.icu",
            role="doctor",
            status="active",
            credentials_ref=get_password_hash("doctor123"),
            created_at=now - datetime.timedelta(days=5)
        ),
        User(
            id="usr_adm_01",
            name="Alex Rivera",
            email="admin.rivera@pulseguard.icu",
            role="admin",
            status="active",
            credentials_ref=get_password_hash("admin123"),
            created_at=now - datetime.timedelta(days=30)
        )
    ]
    for u in users:
        session.add(u)

    # 2. Seed Patients and Beds (10 beds in Critical Care Unit 4)
    patients_data = [
        ("pat_01", "01", "Eleanor Vance", "EV", 72, "Female", "Post-CABG (Coronary Artery Bypass)", "usr_doc_01"),
        ("pat_02", "02", "Marcus Sterling", "MS", 58, "Male", "Acute Decompensated Heart Failure", "usr_doc_01"),
        ("pat_03", "03", "Harold Gomez", "HG", 64, "Male", "Bilateral Pneumonia / ARDS", "usr_doc_02"),
        ("pat_04", "04", "Julian Drake", "JD", 69, "Male", "Septic Shock / Hypoxemia", "usr_doc_01"),
        ("pat_05", "05", "Rosa Martinez", "RM", 45, "Female", "Post-operative Cholecystectomy", "usr_doc_02"),
        ("pat_06", "06", "Thomas Wright", "TW", 81, "Male", "Severe COPD Exacerbation", "usr_doc_02"),
        ("pat_07", "07", "Aaliyah Khan", "AK", 33, "Female", "Diabetic Ketoacidosis (DKA)", "usr_doc_01"),
        ("pat_08", "08", "Robert Lang", "RL", 59, "Male", "Observation / Telemetry artifact", "usr_doc_02"),
        ("pat_09", "09", "Clara Oswald", "CO", 61, "Female", "Subdural Hematoma (Neuro ICU)", "usr_doc_03"),
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
            created_at=now - datetime.timedelta(days=3)
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
            assigned_at=now - datetime.timedelta(days=2)
        )
        session.add(assignment)

    # 3. Seed Doctor-to-Doctor Transfer Requests
    transfers = [
        TransferRequest(
            id="tr_101",
            patient_id="pat_04",
            from_doctor_id="usr_doc_01",
            to_doctor_id="usr_doc_02",
            reason="Rapidly deteriorating ARDS secondary to septic shock. Requires urgent pulmonology step-up and evaluation for veno-venous ECMO cannulation.",
            priority="Urgent",
            status="pending",
            created_at=now - datetime.timedelta(minutes=45)
        ),
        TransferRequest(
            id="tr_102",
            patient_id="pat_09",
            from_doctor_id="usr_doc_03",
            to_doctor_id="usr_doc_02",
            reason="Intracranial pressure normalized post-burr hole evacuation. Step-down transfer to medical ICU for pulmonary weaning and extubation protocol.",
            priority="Routine",
            status="pending",
            created_at=now - datetime.timedelta(hours=2)
        ),
        TransferRequest(
            id="tr_100",
            patient_id="pat_01",
            from_doctor_id="usr_doc_02",
            to_doctor_id="usr_doc_01",
            reason="Post-CABG hemodynamic stabilization achieved. Primary cardiology step-down handover.",
            priority="Routine",
            status="approved",
            decided_by="usr_adm_01",
            created_at=now - datetime.timedelta(days=1),
            decided_at=now - datetime.timedelta(hours=20)
        ),
        TransferRequest(
            id="tr_099",
            patient_id="pat_06",
            from_doctor_id="usr_doc_02",
            to_doctor_id="usr_doc_01",
            reason="Transfer request to general cardiology service.",
            priority="Routine",
            status="rejected",
            decided_by="usr_adm_01",
            rejection_reason="Patient remains hypercapnic on BiPAP; arterial blood gas pH 7.28. Must remain in respiratory ICU.",
            created_at=now - datetime.timedelta(days=2),
            decided_at=now - datetime.timedelta(days=1, hours=12)
        )
    ]
    for tr in transfers:
        session.add(tr)

    # 4. Seed Emergency "Break-Glass" Access Grants
    emergency_grants = [
        EmergencyAccess(
            id="bg_901",
            patient_id="pat_03",
            clinician_id="usr_doc_01",
            reason="Emergency cross-coverage code call: Acute SVT while primary attending scrubbed in OR.",
            starts_at=now - datetime.timedelta(minutes=25),
            expires_at=now + datetime.timedelta(minutes=35),
            status="active"
        ),
        EmergencyAccess(
            id="bg_902",
            patient_id="pat_02",
            clinician_id="usr_doc_02",
            reason="STAT bedside thoracentesis consultation during acute pulmonary edema crisis.",
            starts_at=now - datetime.timedelta(hours=6),
            expires_at=now - datetime.timedelta(hours=4),
            status="expired"
        )
    ]
    for bg in emergency_grants:
        session.add(bg)

    # 5. Seed Medical Notes (Doctor Progress Notes, Consultations, Handovers)
    medical_notes = [
        MedicalNote(
            id="note_01",
            patient_id="pat_04",
            author_id="usr_doc_01",
            note_type="doctor_note",
            content="Patient in septic shock refractory to fluid resuscitation. PaO2/FiO2 ratio 118, consistent with severe ARDS. Norepinephrine running at 0.14 mcg/kg/min. Urgent transfer requested to Pulmonology for ECMO assessment.",
            created_at=now - datetime.timedelta(minutes=50)
        ),
        MedicalNote(
            id="note_02",
            patient_id="pat_04",
            author_id="usr_doc_02",
            note_type="consultation",
            content="Pulmonology bedside evaluation completed. Agree with prone positioning protocol (16h prone / 8h supine). ABG scheduled for 14:00. Will accept transfer upon administrative authorization.",
            created_at=now - datetime.timedelta(minutes=30)
        ),
        MedicalNote(
            id="note_03",
            patient_id="pat_02",
            author_id="usr_doc_01",
            note_type="doctor_note",
            content="Acute decompensated heart failure with bilateral lower extremity edema 3+. Furosemide continuous infusion increased to 12 mg/hr. Strict I&O monitoring in place.",
            created_at=now - datetime.timedelta(hours=3)
        ),
        MedicalNote(
            id="note_04",
            patient_id="pat_01",
            author_id="usr_doc_01",
            note_type="handover",
            content="Post-op Day 3 CABG x3. Hemodynamically stable on room air. Mediastinal chest tube site clean and dry. Ambulated 60 feet without desaturation. Planned transfer to telemetry step-down.",
            created_at=now - datetime.timedelta(days=1)
        ),
        MedicalNote(
            id="note_05",
            patient_id="pat_06",
            author_id="usr_doc_02",
            note_type="doctor_note",
            content="Severe COPD exacerbation on BiPAP 14/6 cmH2O. Serial ABGs show improving pH from 7.25 to 7.33. Continue Duoneb nebulizers q4h.",
            created_at=now - datetime.timedelta(hours=5)
        )
    ]
    for mn in medical_notes:
        session.add(mn)

    # 6. Seed Alerts (Tier 1 Critical, Tier 2 Warning, Tier 3 Noise)
    alerts = [
        Alert(
            id="alt_101",
            patient_id="pat_04",
            bed_id="04",
            tier="tier1",
            anomaly_score=0.95,
            factors=[
                "SpO2 < 85% deterministic safety threshold breach (SpO2: 78%)",
                "Extreme tachycardic divergence: HR 144 bpm",
                "Multi-vital composite collapse"
            ],
            status="active",
            created_at=now - datetime.timedelta(minutes=20)
        ),
        Alert(
            id="alt_102",
            patient_id="pat_02",
            bed_id="02",
            tier="tier2",
            anomaly_score=0.64,
            factors=[
                "Multivariate drift: SpO2 decline (-4% over 180s) coupled with SBP surge (164 mmHg)",
                "Respiratory rate drifting upward to 24 bpm"
            ],
            status="acknowledged",
            acknowledged_by="usr_doc_01",
            acknowledged_at=now - datetime.timedelta(minutes=10),
            ack_note="Bedside evaluation performed. Adjusted oxygen to 4L via nasal cannula. Vasodilator titrated.",
            created_at=now - datetime.timedelta(minutes=45)
        ),
        Alert(
            id="alt_103",
            patient_id="pat_07",
            bed_id="07",
            tier="tier2",
            anomaly_score=0.58,
            factors=[
                "Sinus tachycardia trend: HR drifting from 86 to 114 bpm",
                "Metabolic tachypnea detected: RR 28 bpm"
            ],
            status="active",
            created_at=now - datetime.timedelta(minutes=30)
        ),
        Alert(
            id="alt_104",
            patient_id="pat_08",
            bed_id="08",
            tier="tier3",
            anomaly_score=0.30,
            factors=[
                "Isolated single-sample SpO2 artifact (90%) with immediate 99% rebound",
                "Motion artifact on ECG Lead II"
            ],
            status="resolved",
            created_at=now - datetime.timedelta(hours=2)
        )
    ]
    for al in alerts:
        session.add(al)

    # 7. Seed Cryptographically Chained SHA-256 Audit Trail
    audit_events = [
        ("SYSTEM_BOOTSTRAP", None, "usr_adm_01", {"version": "3.0", "action": "ward_initialized"}, now - datetime.timedelta(days=2)),
        ("USER_LOGIN", None, "usr_adm_01", {"client": "admin_panel"}, now - datetime.timedelta(days=2, hours=-1)),
        ("PATIENT_ADMISSION", "01", "usr_doc_01", {"patient_id": "pat_01", "mrn": "MRN-01982"}, now - datetime.timedelta(days=2, hours=-2)),
        ("TRANSFER_REQUEST_SUBMITTED", "06", "usr_doc_02", {"transfer_id": "tr_099", "patient_id": "pat_06", "to_doctor_id": "usr_doc_01"}, now - datetime.timedelta(days=2)),
        ("TRANSFER_REJECTED", "06", "usr_adm_01", {"transfer_id": "tr_099", "reason": "Patient remains hypercapnic"}, now - datetime.timedelta(days=1, hours=12)),
        ("TRANSFER_REQUEST_SUBMITTED", "01", "usr_doc_02", {"transfer_id": "tr_100", "patient_id": "pat_01", "to_doctor_id": "usr_doc_01"}, now - datetime.timedelta(days=1)),
        ("TRANSFER_APPROVED", "01", "usr_adm_01", {"transfer_id": "tr_100", "patient_id": "pat_01", "new_doctor_id": "usr_doc_01"}, now - datetime.timedelta(hours=20)),
        ("EMERGENCY_ACCESS_GRANTED", "02", "usr_adm_01", {"grant_id": "bg_902", "clinician_id": "usr_doc_02", "patient_id": "pat_02"}, now - datetime.timedelta(hours=6)),
        ("MEDICAL_NOTE_CREATED", "02", "usr_doc_01", {"note_id": "note_03", "type": "doctor_note"}, now - datetime.timedelta(hours=3)),
        ("TRANSFER_REQUEST_SUBMITTED", "09", "usr_doc_03", {"transfer_id": "tr_102", "patient_id": "pat_09", "to_doctor_id": "usr_doc_02"}, now - datetime.timedelta(hours=2)),
        ("MEDICAL_NOTE_CREATED", "04", "usr_doc_01", {"note_id": "note_01", "type": "doctor_note"}, now - datetime.timedelta(minutes=50)),
        ("TRANSFER_REQUEST_SUBMITTED", "04", "usr_doc_01", {"transfer_id": "tr_101", "patient_id": "pat_04", "to_doctor_id": "usr_doc_02"}, now - datetime.timedelta(minutes=45)),
        ("ALERT_EVALUATED_TIER2", "02", None, {"alert_id": "alt_102", "anomaly_score": 0.64}, now - datetime.timedelta(minutes=45)),
        ("EMERGENCY_ACCESS_GRANTED", "03", "usr_adm_01", {"grant_id": "bg_901", "clinician_id": "usr_doc_01", "patient_id": "pat_03"}, now - datetime.timedelta(minutes=25)),
        ("TIER1_ALARM_CASCADE_TRIGGERED", "04", None, {"alert_id": "alt_101", "anomaly_score": 0.95, "unsuppressable": True}, now - datetime.timedelta(minutes=20)),
        ("ALERT_ACKNOWLEDGED", "02", "usr_doc_01", {"alert_id": "alt_102", "note": "Bedside evaluation performed."}, now - datetime.timedelta(minutes=10)),
    ]

    prev_hash = GENESIS_HASH
    for seq_id, (action, bed_id, clinician_id, metadata, ts) in enumerate(audit_events, start=1):
        curr_hash = calculate_hash(
            previous_hash=prev_hash,
            timestamp=ts,
            action=action,
            bed_id=bed_id,
            clinician_id=clinician_id
        )
        log_entry = AuditLog(
            seq_id=seq_id,
            timestamp=ts,
            action=action,
            bed_id=bed_id,
            clinician_id=clinician_id,
            previous_hash=prev_hash,
            hash=curr_hash,
            metadata_json=metadata,
            gap_marker="false"
        )
        session.add(log_entry)
        prev_hash = curr_hash

    await session.commit()
    logger.info("Successfully seeded: 4 Users (Zero Nurse), 10 Patients, 10 Beds, 4 Transfers, 2 Emergency Grants, 5 Notes, 4 Alerts, 16 SHA-256 Audit Logs.")
