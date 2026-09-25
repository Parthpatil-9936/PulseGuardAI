"""Pydantic Schemas for Triage Prediction API.

Defines strict request/response data contracts, input validation bounds,
and explainability outputs for ML inference and DPDP-compliant audit logging.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class VitalsSample(BaseModel):
    """Single-tick physiological reading from bedside monitor."""

    hr: float = Field(..., ge=0.0, le=300.0, description="Heart rate in beats per minute")
    spo2: float = Field(..., ge=0.0, le=100.0, description="Blood oxygen saturation percentage")
    bp_sys: float = Field(..., ge=0.0, le=300.0, description="Systolic blood pressure in mmHg")
    bp_dia: Optional[float] = Field(None, ge=0.0, le=200.0, description="Diastolic blood pressure in mmHg")
    temp: Optional[float] = Field(None, ge=30.0, le=45.0, description="Body temperature in Celsius")
    ecg_lead_ok: bool = Field(True, description="True if ECG electrode impedance is normal")


class TriagePredictRequest(BaseModel):
    """Request payload for POST /api/v1/triage/predict.

    Can accept either:
    1. A list of 1 to 100 VitalsSample objects (chronological rolling window).
    2. A raw biological matrix of shape (3, 100) where rows correspond to [hr, spo2, bp_sys].
    3. A single vitals reading (will be broadcast to a baseline 100-sample window).
    """

    bed_id: str = Field(..., pattern=r"^bed-(0[1-9]|1[0-9]|20)$", description="Bed identifier (e.g. bed-01)")
    patient_id: Optional[str] = Field(None, description="Optional patient reference ID (never logged directly to audit)")
    ts: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of inference request")
    samples: Optional[List[VitalsSample]] = Field(None, description="List of vital samples (up to 100 @ 10 Hz)")
    raw_window: Optional[List[List[float]]] = Field(
        None,
        description="Alternative raw 2D matrix of shape (3, 100) representing [hr, spo2, bp_sys] x 100 timesteps",
    )
    single_vitals: Optional[VitalsSample] = Field(
        None,
        description="Single snapshot reading (expanded across window for point-in-time triage)",
    )

    @field_validator("raw_window")
    @classmethod
    def validate_raw_window_shape(cls, v: Optional[List[List[float]]]) -> Optional[List[List[float]]]:
        if v is None:
            return v
        if len(v) != 3:
            raise ValueError(f"raw_window must have exactly 3 channels (hr, spo2, bp_sys), got {len(v)}")
        for i, channel in enumerate(v):
            if len(channel) != 100:
                raise ValueError(
                    f"Channel {i} in raw_window must contain exactly 100 timesteps (10s @ 10 Hz), got {len(channel)}"
                )
        return v


class TriagePredictResponse(BaseModel):
    """Structured response from ML Triage inference engine."""

    bed_id: str
    tier: int = Field(..., ge=1, le=3, description="Triage Alert Tier: 1 (Catastrophic Red), 2 (Warning Yellow), 3 (Baseline Green)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Normalized ML anomaly score [0.0 - 1.0]")
    reason: str = Field(..., description="Plain-language clinical reason with vital attribution")
    attributing_vital: str = Field(..., description="Primary vital driving alert: 'hr', 'spo2', 'bp_sys', or 'none'")
    hard_breach: bool = Field(..., description="True if hard physiological safety threshold was breached unconditionally")
    channel_mse: Dict[str, float] = Field(..., description="Raw reconstruction MSE per vital channel")
    normalized_scores: Dict[str, float] = Field(..., description="Calibrated [0.0 - 1.0] anomaly scores per vital channel")
    explainability_factors: List[str] = Field(..., description="Clinical factor breakdown explaining inference output")
    cached: bool = Field(False, description="True if prediction was served from Redis cache")
    input_hash: str = Field(..., description="SHA-256 fingerprint of the input vector (logged to DPDP audit ledger)")
    latency_ms: float = Field(..., description="End-to-end inference processing time in milliseconds")
    ts: datetime = Field(..., description="Timestamp of inference execution")
    model_version: str = Field("1D-CNN-Autoencoder-v1.0", description="Active model checkpoint version")


class ModelHealthResponse(BaseModel):
    """Readiness and health status for /health/model endpoint."""

    status: str = Field(..., description="'ready', 'loading', or 'error'")
    model_name: str
    version: str
    weights_path: str
    device: str
    in_channels: int
    latent_dim: int
    is_eval_mode: bool
    description: str
