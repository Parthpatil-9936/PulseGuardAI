import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from app.db.session import Base


class EmergencyAccess(Base):
    __tablename__ = "emergency_access"

    id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(64), ForeignKey("patients.id"), nullable=False, index=True)
    clinician_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    starts_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    status = Column(String(32), default="active", nullable=False)  # 'active', 'expired', 'revoked'
    revoked_at = Column(DateTime, nullable=True)
