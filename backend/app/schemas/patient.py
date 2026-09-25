import datetime
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional, List


class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    external_ref: str
    demographics: Dict[str, Any]
    status: str
    created_at: datetime.datetime


class BedOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ward: str
    device_id: str
    status: str
    patient_id: Optional[str] = None
    vitals: Optional[Dict[str, Any]] = None


class MedicalNoteCreate(BaseModel):
    note_type: str = "doctor_note"  # 'doctor_note' or 'nurse_observation'
    content: str


class MedicalNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    author_id: str
    note_type: str
    content: str
    created_at: datetime.datetime


class VitalSample(BaseModel):
    bed_id: str
    seq: int
    timestamp: float
    hr: float
    spo2: float
    bp_sys: float
    bp_dia: float
    rr: Optional[float] = 16.0
    temp: Optional[float] = 36.8
    tier: str
    anomaly_score: float
    factors: List[str]
