"""
ML Triage Engine — Stub Implementation
======================================
This module provides the swappable inference interface for PulseGuard-AI.
Hard physiological thresholds operate alongside this score with strict OR logic.

Swapping this stub with a production model is isolated to this file:
replace get_anomaly_score() with tensor inference over the rolling window.
"""

from typing import List, Dict, Any, Tuple
import statistics

# Admin-visible ML status flag exposed via /health endpoint
ML_ENGINE_STATUS = {
    "status": "stubbed",
    "model_name": "1D-CNN Autoencoder + Isolation Forest (Placeholder)",
    "version": "stub-v1.0",
    "degraded": True,
    "description": "Rule-based variance approximation active. Production weights unmounted."
}


def get_anomaly_score(window: List[Dict[str, Any]]) -> float:
    """
    Computes an anomaly score [0.0 - 1.0] from a 10-second rolling telemetry window.
    
    # TODO: Replace with trained 1D-CNN Autoencoder + Isolation Forest.
    # Production architecture takes a normalized (100, 3) matrix of [HR, SpO2, MAP]
    # and returns reconstruction error + isolation tree path depth score.
    """
    if not window or len(window) < 3:
        return 0.0

    try:
        # Extract vital streams
        spo2_vals = [sample.get("spo2", 98.0) for sample in window if sample.get("spo2") is not None]
        hr_vals = [sample.get("hr", 75.0) for sample in window if sample.get("hr") is not None]

        score = 0.0

        # Heuristic 1: SpO2 decline rate over window
        if spo2_vals and len(spo2_vals) >= 2:
            latest_spo2 = spo2_vals[-1]
            first_spo2 = spo2_vals[0]
            spo2_drop = first_spo2 - latest_spo2
            if spo2_drop > 3.0:
                score += min(0.4, (spo2_drop / 10.0) * 0.4)

        # Heuristic 2: HR variance
        if hr_vals and len(hr_vals) >= 4:
            hr_variance = statistics.variance(hr_vals)
            if hr_variance > 25.0:
                score += min(0.3, (hr_variance / 100.0) * 0.3)

        # Heuristic 3: SpO2 baseline proximity to warning band
        if spo2_vals:
            curr_spo2 = spo2_vals[-1]
            if curr_spo2 < 90.0:
                score += 0.3
            elif curr_spo2 < 94.0:
                score += 0.15

        return round(min(1.0, max(0.0, score)), 2)

    except Exception:
        # Fail safe to 0.0; hard thresholds operate independently
        return 0.0


def extract_explainability_factors(window: List[Dict[str, Any]], anomaly_score: float) -> List[str]:
    """
    Extracts 2-4 human-readable clinical contributing factors from the window.
    """
    factors = []
    if not window:
        return ["Telemetry baseline stable"]

    latest = window[-1]
    hr = latest.get("hr", 75)
    spo2 = latest.get("spo2", 98)
    bp_sys = latest.get("bp_sys", 120)
    bp_dia = latest.get("bp_dia", 80)

    if spo2 < 85.0:
        factors.append(f"SpO2 < 85% deterministic safety threshold breach ({spo2}%)")
    elif spo2 < 92.0:
        factors.append(f"SpO2 declining ({spo2}% current)")

    if len(window) >= 5:
        spo2_delta = window[0].get("spo2", spo2) - spo2
        if spo2_delta > 2.0:
            factors.append(f"Acute desaturation: -{spo2_delta:.1f}% over rolling window")

    if hr > 130:
        factors.append(f"Extreme tachycardia: HR {hr} bpm")
    elif hr > 105:
        factors.append(f"Tachycardic divergence: HR {hr} bpm")
    elif hr < 50:
        factors.append(f"Bradycardia: HR {hr} bpm")

    if bp_sys < 90 or bp_dia < 60:
        factors.append(f"Hypotensive pressure collapse ({bp_sys}/{bp_dia} mmHg)")

    if hr > 115 and (bp_sys < 95 or (bp_sys and bp_sys < 100)):
        factors.append("HR/BP covariance diverging (HR ↑, MAP ↓)")

    if not factors:
        if anomaly_score > 0.4:
            factors.append("Multi-vital covariance drift detected by autoencoder")
        else:
            factors.append("Sinus rhythm and oxygen saturation stable within normal limits")

    return factors[:4]
