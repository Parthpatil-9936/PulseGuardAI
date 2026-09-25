import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from app.db.session import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)  # 'TRANSFER_REQUESTED', 'TRANSFER_DECIDED', 'TIER1_ALERT'
    payload_ref = Column(Text, nullable=False)  # JSON or reference ID
    status = Column(String(32), default="unread", nullable=False)  # 'unread', 'read'
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    read_at = Column(DateTime, nullable=True)
