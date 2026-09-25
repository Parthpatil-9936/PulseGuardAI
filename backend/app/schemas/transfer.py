import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class TransferCreate(BaseModel):
    patient_id: str
    to_doctor_id: str
    reason: str
    priority: Optional[str] = "Routine"


class TransferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    from_doctor_id: str
    to_doctor_id: str
    reason: str
    priority: str
    status: str
    decided_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime.datetime
    decided_at: Optional[datetime.datetime] = None


class TransferRejectRequest(BaseModel):
    reason: str
