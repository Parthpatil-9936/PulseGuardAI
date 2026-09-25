import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from app.db.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    seq_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    action = Column(String(64), nullable=False, index=True)  # LOGIN, ACK, MUTE, TRANSFER_APPROVE, BREAK_GLASS_GRANT, etc.
    bed_id = Column(String(32), nullable=True)
    clinician_id = Column(String(64), nullable=True)
    previous_hash = Column(String(64), nullable=False)
    hash = Column(String(64), nullable=False, index=True)
    metadata_json = Column("metadata", JSON, nullable=True)
    gap_marker = Column(String(16), nullable=True)  # for resilience buffer flush: 'true' if flushed after reconnect
