"""PulseGuard-AI Telemetry Schemas.

Defines Pydantic models for incoming raw telemetry ticks matching Section 3.1
field constraints and enriched processed telemetry ticks.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class TelemetryTick(BaseModel):
    """Pydantic TelemetryTick schema matching Section 3.1 field constraints.

    Section 3.1 Constraints:
    - bed_id: string, regex ^bed-(0[1-9]|10)$
    - ts: ISO-8601 UTC timestamp, millisecond precision
    - hr: integer, valid range [0, 300] bpm
    - spo2: integer, valid range [0, 100] %
    - bp_sys: integer, systolic [0, 300] mmHg
    - bp_dia: integer, diastolic [0, 200] mmHg
    - ecg_lead_ok: boolean, hardware electrode impedance status
    - seq: integer, strictly monotonic counter incremented by monitor hardware
    """

    bed_id: str = Field(
        ...,
        pattern=r"^bed-(0[1-9]|10)$",
        description="Bed identifier matching ^bed-(0[1-9]|10)$",
    )
    ts: datetime = Field(..., description="ISO-8601 UTC timestamp")
    hr: Optional[int] = Field(
        None, ge=0, le=300, description="Heart rate in bpm [0, 300]"
    )
    spo2: Optional[int] = Field(
        None, ge=0, le=100, description="SpO2 percentage [0, 100]"
    )
    bp_sys: Optional[int] = Field(
        None, ge=0, le=300, description="Systolic blood pressure in mmHg [0, 300]"
    )
    bp_dia: Optional[int] = Field(
        None, ge=0, le=200, description="Diastolic blood pressure in mmHg [0, 200]"
    )
    temp: Optional[float] = Field(
        None, ge=20.0, le=45.0, description="Body temperature in Celsius [20.0, 45.0]"
    )
    ecg_lead_ok: bool = Field(
        True, description="Hardware electrode impedance status"
    )
    seq: int = Field(..., ge=0, description="Monotonic sequence counter")

    @field_validator("ts", mode="before")
    def parse_iso_timestamp(cls, v: object) -> datetime:
        """Parse ISO-8601 string or numeric timestamp to timezone-aware datetime."""
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(v, tz=timezone.utc)
        if isinstance(v, str):
            val = v.replace("Z", "+00:00") if v.endswith("Z") else v
            dt = datetime.fromisoformat(val)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        if isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v
        raise ValueError(f"Invalid timestamp format: {v}")

    @field_validator("bp_dia")
    def validate_bp_relationship(cls, v: Optional[int], info) -> Optional[int]:
        """Validate diastolic pressure does not exceed systolic pressure when both exist."""
        if v is not None and "bp_sys" in info.data and info.data["bp_sys"] is not None:
            sys_val = info.data["bp_sys"]
            if v > sys_val:
                raise ValueError(
                    f"Diastolic BP ({v}) cannot exceed Systolic BP ({sys_val})"
                )
        return v


class ProcessedTelemetryTick(BaseModel):
    """Normalized, forward-filled, and SQI-evaluated telemetry tick."""

    bed_id: str
    ts: datetime
    seq: int
    hr: float
    spo2: float
    bp_sys: float
    bp_dia: float
    temp: Optional[float] = None
    ecg_lead_ok: bool = True
    drift_flag: Literal["none", "drift", "tamper"] = "none"
    seq_gap_flag: bool = False
    seq_gap_size: int = 0
    staleness_ms: Dict[str, float] = Field(default_factory=dict)
