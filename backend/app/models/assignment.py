import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from app.db.session import Base


class PatientAssignment(Base):
    __tablename__ = "patient_assignments"

    id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(64), ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(32), default="active", nullable=False, index=True)  # 'active', 'revoked'
    assigned_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_active_assignment", "patient_id", "status"),
    )
