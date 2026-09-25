import datetime
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, JSON, Text
from app.db.session import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(64), primary_key=True, index=True)
    patient_id = Column(String(64), ForeignKey("patients.id"), nullable=True, index=True)
    bed_id = Column(String(32), nullable=False, index=True)
    tier = Column(String(32), nullable=False, index=True)  # 'tier1', 'tier2', 'tier3'
    anomaly_score = Column(Float, nullable=False)
    factors = Column(JSON, nullable=True)  # contributing explainability factors
    status = Column(String(32), default="active", nullable=False, index=True)  # 'active', 'acknowledged', 'resolved'
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    acknowledged_by = Column(String(64), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    ack_note = Column(Text, nullable=True)
