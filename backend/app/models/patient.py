import datetime
from sqlalchemy import Column, String, DateTime, JSON, Text
from app.db.session import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(64), primary_key=True, index=True)
    external_ref = Column(String(64), unique=True, index=True, nullable=False)
    demographics = Column(JSON, nullable=False)  # { name, initials, age, gender, diagnosis, code_status }
    status = Column(String(32), default="admitted", nullable=False)  # 'admitted', 'discharged', 'transferred'
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class Bed(Base):
    __tablename__ = "beds"

    id = Column(String(32), primary_key=True, index=True)  # e.g., '01', '02', '10'
    ward = Column(String(64), default="Critical Care Unit 4", nullable=False)
    device_id = Column(String(64), unique=True, nullable=False)
    status = Column(String(32), default="occupied", nullable=False)  # 'occupied', 'available', 'no_signal'
    patient_id = Column(String(64), nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
