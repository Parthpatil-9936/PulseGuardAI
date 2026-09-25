"""PulseGuard-AI Triage Schemas.

Defines Pydantic models for the 3-Tier Alert Cascade decisions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class TriageDecision(BaseModel):
    """Pydantic model representing a 3-tier triage decision frame."""

    bed_id: str
    ts: datetime
    tier: int = Field(..., ge=1, le=3, description="Alert Tier: 1=Catastrophic, 2=Warning, 3=Suppressed")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Normalized ML anomaly score [0.0, 1.0]")
    reason: str = Field(..., description="Clinical reason or factor attribution string")
    attributing_vital: str = Field("none", description="Vital channel with highest normalized error (hr, spo2, bp_sys, or none)")
    drift_flag: Literal["none", "drift", "tamper"] = Field("none", description="SQI drift/tamper flag")
    is_cold_start: bool = Field(False, description="True if telemetry buffer is in <100 sample cold start mode")
    hard_breach: bool = Field(False, description="True if a hard physiological threshold was breached")
    raw_tier: int = Field(..., ge=1, le=3, description="Pre-hysteresis raw tier decision")
    schema_version: str = "1.0"
