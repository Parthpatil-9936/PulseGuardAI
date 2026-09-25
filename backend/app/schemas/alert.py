import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: Optional[str] = None
    bed_id: str
    tier: str
    anomaly_score: float
    factors: Optional[List[str]] = None
    status: str
    created_at: datetime.datetime
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime.datetime] = None
    ack_note: Optional[str] = None


class AlertAcknowledgeRequest(BaseModel):
    note: Optional[str] = "Bedside assessment completed"


class MuteRequest(BaseModel):
    bed_id: Optional[str] = None
    duration_seconds: int = 300  # Will be clamped to <= 300


class EmergencyAccessCreate(BaseModel):
    patient_id: str
    clinician_id: str
    duration_minutes: int = 30
    reason: str


class EmergencyAccessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    clinician_id: str
    reason: str
    starts_at: datetime.datetime
    expires_at: datetime.datetime
    status: str


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    seq_id: int
    timestamp: datetime.datetime
    action: str
    bed_id: Optional[str] = None
    clinician_id: Optional[str] = None
    previous_hash: str
    hash: str
    metadata: Optional[Dict[str, Any]] = None
    gap_marker: Optional[str] = None
