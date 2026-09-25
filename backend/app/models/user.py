import datetime
from sqlalchemy import Column, String, DateTime
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    role = Column(String(32), nullable=False, index=True)  # 'admin', 'doctor', 'nurse'
    status = Column(String(32), default="active", nullable=False)  # 'active', 'inactive'
    credentials_ref = Column(String(255), nullable=False)  # hashed password / secret
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
