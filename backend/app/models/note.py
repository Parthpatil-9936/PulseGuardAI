import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from app.db.session import Base


class MedicalNote(Base):
    __tablename__ = "medical_notes"

    id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(64), ForeignKey("patients.id"), nullable=False, index=True)
    author_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    note_type = Column(String(32), nullable=False)  # 'doctor_note', 'consultation', 'handover'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, nullable=True)
