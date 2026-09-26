"""PulseGuard-AI ML Triage Inference Engine.

Provides:
1. `predict_triage()`: High-performance structured inference over a 10-second rolling window.
2. Hard physiological safety invariants (SpO2 < 85%, extreme HR, BP crisis, lead-off).
3. Per-vital factor attribution and explainability reporting.
4. Backwards-compatible `get_anomaly_score()` for existing telemetry pipelines.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.ml.model_loader import ml_manager
from app.ml.preprocessing import (
    FEATURE_ORDER,
    preprocess_triage_input,
)
from app.schemas.triage_predict import TriagePredictRequest, TriagePredictResponse

# Hard physiological limits
HARD_SPO2_MIN = 85.0
HARD_HR_MIN = 20.0
HARD_HR_MAX = 220.0
HARD_BP_SYS_MIN = 60.0
HARD_BP_SYS_MAX = 200.0
HARD_BP_DIA_MAX = 120.0
ECG_LEAD_DISCONNECT_REASON = "CRITICAL: ECG lead disconnected — no signal"


def check_hard_limits(raw_arr: np.ndarray, ecg_lead_ok: bool = True) -> Tuple[bool, Optional[str]]:
    """Evaluates deterministic life-safety thresholds on the latest sample of the window.

    raw_arr is shaped (3, 100) with rows [0: HR, 1: SpO2, 2: BP_sys].
    """
    latest_hr = float(raw_arr[0, -1])
    latest_spo2 = float(raw_arr[1, -1])
    latest_bp_sys = float(raw_arr[2, -1])

    breaches = []
    if not ecg_lead_ok:
        breaches.append(ECG_LEAD_DISCONNECT_REASON)
    if latest_spo2 < HARD_SPO2_MIN:
        breaches.append(f"SpO2={latest_spo2:.1f}% < {HARD_SPO2_MIN}%")
    if latest_hr < HARD_HR_MIN:
        breaches.append(f"HR={latest_hr:.0f} < {HARD_HR_MIN} bpm")
    elif latest_hr > HARD_HR_MAX:
        breaches.append(f"HR={latest_hr:.0f} > {HARD_HR_MAX} bpm")
    if latest_bp_sys < HARD_BP_SYS_MIN:
        breaches.append(f"BP_sys={latest_bp_sys:.0f} < {HARD_BP_SYS_MIN} mmHg")
    elif latest_bp_sys > HARD_BP_SYS_MAX:
        breaches.append(f"BP_sys={latest_bp_sys:.0f} > {HARD_BP_SYS_MAX} mmHg")

    if breaches:
        return True, ", ".join(breaches)
    return False, None


def extract_explainability(
    raw_arr: np.ndarray,
    attributing_vital: str,
    confidence: float,
    hard_breach: bool,
    breach_detail: Optional[str] = None,
) -> List[str]:
    """Generates 2 to 4 clinical explanation factors for the assigned clinician."""
    factors: List[str] = []

    if hard_breach and breach_detail:
        factors.append(f"Hard physiological threshold breach: {breach_detail}")

    latest_hr = float(raw_arr[0, -1])
    latest_spo2 = float(raw_arr[1, -1])
    latest_bp_sys = float(raw_arr[2, -1])

    # Trajectory drift over the 10-second window
    hr_delta = latest_hr - float(raw_arr[0, 0])
    spo2_delta = latest_spo2 - float(raw_arr[1, 0])
    bp_delta = latest_bp_sys - float(raw_arr[2, 0])

    if attributing_vital == "spo2" or abs(spo2_delta) >= 2.0:
        if spo2_delta < -2.0:
            factors.append(f"Acute desaturation: {spo2_delta:+.1f}% drop across 10s window (current: {latest_spo2:.1f}%)")
        elif latest_spo2 < 92.0:
            factors.append(f"Hypoxemic desaturation trend ({latest_spo2:.1f}%)")

    if attributing_vital == "hr" or abs(hr_delta) >= 15.0:
        if latest_hr > 120.0:
            factors.append(f"Tachycardic divergence: HR {latest_hr:.0f} bpm ({hr_delta:+.0f} bpm shift)")
        elif latest_hr < 50.0:
            factors.append(f"Bradycardic deceleration: HR {latest_hr:.0f} bpm")

    if attributing_vital == "bp_sys" or abs(bp_delta) >= 20.0:
        if latest_bp_sys < 90.0:
            factors.append(f"Hypotensive arterial collapse: BP {latest_bp_sys:.0f} mmHg")
        elif latest_bp_sys > 160.0:
            factors.append(f"Hypertensive escalation: BP {latest_bp_sys:.0f} mmHg")

    if not factors:
        if confidence > 0.4:
            factors.append(f"Multi-vital covariance drift detected by autoencoder (lead: {attributing_vital.upper()})")
        else:
            factors.append("Vitals homeostatic trajectory stable within normal physiological boundaries")

    return factors[:4]


def extract_explainability_factors(window: Any, anomaly_score: float) -> List[str]:
    """Compatibility function for alert_service extracting clinical contributing factors."""
    factors = []
    if isinstance(window, list) and not window:
        return ["Stable"]
    if isinstance(window, list):
        latest = window[-1]
    elif isinstance(window, dict):
        latest = window
    else:
        return ["Stable"]

    hr = latest.get("hr", 75)
    spo2 = latest.get("spo2", 98)
    bp_sys = latest.get("bp_sys", 120)
    bp_dia = latest.get("bp_dia", 80)

    if spo2 < 85.0:
        factors.append("Critical Hypoxia")
    elif spo2 < 92.0:
        factors.append("Hypoxia")

    if isinstance(window, list) and len(window) >= 5:
        spo2_delta = window[0].get("spo2", spo2) - spo2
        if spo2_delta > 2.0:
            factors.append("Desaturation")

    if hr > 130:
        factors.append("Severe Tachycardia")
    elif hr > 105:
        factors.append("Tachycardia")
    elif hr < 50:
        factors.append("Bradycardia")

    if bp_sys < 90 or bp_dia < 60:
        factors.append("Hypotension")

    if hr > 115 and (bp_sys < 95 or (bp_sys and bp_sys < 100)):
        factors.append("Shock Indicator")

    if not factors:
        if anomaly_score > 0.4:
            factors.append("Vital Drift")
        else:
            factors.append("Stable")

    return factors[:4]


def predict_triage(
    request: TriagePredictRequest,
    cached: bool = False,
) -> TriagePredictResponse:
    """Core prediction function taking structured Pydantic input and returning structured output.

    Executes:
    1. Preprocessing, scaling, and fingerprint hashing.
    2. Zero-grad PyTorch forward pass.
    3. Per-channel reconstruction MSE and normalized score calculation.
    4. Deterministic hard physiological safety net check.
    5. Final 3-tier categorization and clinical factor attribution.
    """
    import torch

    t0 = time.perf_counter()

    if not ml_manager.is_ready or ml_manager.model is None:
        raise RuntimeError("ML Triage Model is not ready for inference")

    # 1. Preprocess structured inputs
    samples_dict = (
        [s.model_dump() for s in request.samples] if request.samples else None
    )
    single_dict = (
        request.single_vitals.model_dump() if request.single_vitals else None
    )

    raw_arr, scaled_arr, input_hash = preprocess_triage_input(
        bed_id=request.bed_id,
        samples=samples_dict,
        raw_window=request.raw_window,
        single_vitals=single_dict,
    )

    # 2. PyTorch tensor conversion & inference pass
    model = ml_manager.model
    input_tensor = torch.from_numpy(scaled_arr).unsqueeze(0)  # Shape: (1, 3, 100)

    with torch.no_grad():
        recon_tensor = model(input_tensor)
        # Per-channel MSE over timesteps (dim 2) -> (1, 3)
        diff_sq = (input_tensor - recon_tensor) ** 2
        per_channel_mse = diff_sq.mean(dim=2).squeeze(0).cpu().numpy()  # (3,)

    # 3. Normalized anomaly scores via calibrated offset and scale
    channel_mse_dict: Dict[str, float] = {}
    normalized_scores: Dict[str, float] = {}

    for idx, cname in enumerate(FEATURE_ORDER):
        mse_val = float(per_channel_mse[idx])
        offset = ml_manager.per_channel_offset.get(cname, 0.0001)
        scale = max(1e-6, ml_manager.per_channel_scale.get(cname, 0.001))

        norm_score = float(np.clip((mse_val - offset) / scale, 0.0, 1.0))
        channel_mse_dict[cname] = round(mse_val, 6)
        normalized_scores[cname] = round(norm_score, 4)

    # Factor attribution: vital channel with highest normalized reconstruction error
    attributing_vital = max(normalized_scores, key=lambda k: normalized_scores[k])
    confidence = float(normalized_scores[attributing_vital])

    # 4. Deterministic hard threshold evaluation
    lead_ok = True
    if request.single_vitals:
        lead_ok = request.single_vitals.ecg_lead_ok
    elif request.samples:
        lead_ok = request.samples[-1].ecg_lead_ok

    hard_breach, breach_detail = check_hard_limits(raw_arr, ecg_lead_ok=lead_ok)

    # 5. Triage decision logic
    if hard_breach:
        tier = 1
        reason = f"CATASTROPHIC: Hard safety limit breach ({breach_detail})"
    elif confidence > 0.90:
        tier = 1
        reason = f"CATASTROPHIC: Severe {attributing_vital.upper()} trajectory divergence"
    elif confidence >= 0.50:
        tier = 2
        reason = f"WARNING: {attributing_vital.upper()} anomalous from baseline pattern"
    else:
        tier = 3
        reason = "Normal homeostatic baseline"

    # 6. Explainability factors
    factors = extract_explainability(
        raw_arr=raw_arr,
        attributing_vital=attributing_vital,
        confidence=confidence,
        hard_breach=hard_breach,
        breach_detail=breach_detail,
    )

    latency_ms = (time.perf_counter() - t0) * 1000.0

    return TriagePredictResponse(
        bed_id=request.bed_id,
        tier=tier,
        confidence=round(confidence, 4),
        reason=reason,
        attributing_vital=attributing_vital,
        hard_breach=hard_breach,
        channel_mse=channel_mse_dict,
        normalized_scores=normalized_scores,
        explainability_factors=factors,
        cached=cached,
        input_hash=input_hash,
        latency_ms=round(latency_ms, 2),
        ts=datetime.now(timezone.utc),
        model_version=ml_manager.model_version,
    )


# Backwards compatibility for existing telemetry streaming service
def get_anomaly_score(window: List[Dict[str, Any]]) -> float:
    """Computes anomaly score [0.0 - 1.0] from rolling telemetry window using the autoencoder."""
    if not window or len(window) < 3:
        return 0.0

    if not ml_manager.is_ready or ml_manager.model is None:
        # Fallback heuristic if model is not loaded yet
        return 0.0

    try:
        from app.schemas.triage_predict import TriagePredictRequest, VitalsSample

        clean_samples = []
        for s in window:
            clean_samples.append(
                VitalsSample(
                    hr=float(s.get("hr", 75.0)),
                    spo2=float(s.get("spo2", 98.0)),
                    bp_sys=float(s.get("bp_sys", 120.0)),
                    bp_dia=float(s.get("bp_dia", 80.0)),
                    temp=float(s.get("temp", 36.8)),
                    ecg_lead_ok=bool(s.get("ecg_lead_ok", True)),
                )
            )

        req = TriagePredictRequest(bed_id="bed-01", samples=clean_samples)
        resp = predict_triage(req)
        return resp.confidence
    except Exception:
        return 0.0


# Dynamic status for /health endpoint
def get_ml_status() -> Dict[str, Any]:
    return ml_manager.get_health_status()


# Module-level alias for main.py /health
ML_ENGINE_STATUS = get_ml_status()
