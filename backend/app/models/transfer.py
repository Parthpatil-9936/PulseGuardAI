import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from app.db.session import Base


class TransferRequest(Base):
    __tablename__ = "transfer_requests"

    id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(64), ForeignKey("patients.id"), nullable=False, index=True)
    from_doctor_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    to_doctor_id = Column(String(64), ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    priority = Column(String(32), default="Routine", nullable=False)  # 'Routine', 'Urgent', 'STAT'
    status = Column(String(32), default="pending", nullable=False, index=True)  # 'pending', 'approved', 'rejected'
    decided_by = Column(String(64), ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    decided_at = Column(DateTime, nullable=True)
