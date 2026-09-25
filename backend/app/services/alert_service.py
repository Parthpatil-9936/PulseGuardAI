from typing import Dict, Any, Tuple, List
from app.core.config import settings
from app.ml.inference import extract_explainability_factors


def evaluate_alert(vitals: Dict[str, Any], ml_score: float) -> Tuple[str, List[str]]:
    """
    Evaluates physiological vitals against deterministic hard safety thresholds
    and ML anomaly score using strict fail-safe OR logic.
    
    CORE INVARIANT:
    A machine learning model can NEVER suppress a hard-threshold vital breach.
    Hard physiological thresholds and ML score are strictly OR'd — never AND'd.
    """
    factors = []
    
    spo2 = float(vitals.get("spo2", 98.0))
    hr = float(vitals.get("hr", 75.0))
    bp_sys = float(vitals.get("bp_sys", 120.0))
    bp_dia = float(vitals.get("bp_dia", 80.0))
    is_disconnected = vitals.get("lead_status") == "disconnected" or vitals.get("disconnected", False)

    if isDisconnected := is_disconnected:
        return "no_signal", ["Electrode lead-off detected (Lead II / V5 disconnected)"]

    hard_tier1_breach = False

    # 1. Deterministic Hard Threshold Checks (UNSUPPRESSABLE TIER 1)
    if spo2 < settings.TIER1_SPO2_THRESHOLD:
        hard_tier1_breach = True
        thresh_pct = int(settings.TIER1_SPO2_THRESHOLD)
        factors.append(f"SpO2 < {thresh_pct}% deterministic safety barrier breached ({spo2}%)")

    if hr >= settings.TIER1_HR_HIGH:
        hard_tier1_breach = True
        factors.append(f"Extreme tachycardia: HR {hr} bpm (threshold >= {settings.TIER1_HR_HIGH})")
    elif hr <= settings.TIER1_HR_LOW and hr > 0:
        hard_tier1_breach = True
        factors.append(f"Extreme bradycardia: HR {hr} bpm (threshold <= {settings.TIER1_HR_LOW})")
    elif hr == 0:
        hard_tier1_breach = True
        factors.append("Asystole / zero pulse detected")

    if bp_sys < 80.0 and hr > 120.0:
        hard_tier1_breach = True
        factors.append(f"Acute hemodynamic collapse: SBP {bp_sys} mmHg with HR {hr} bpm")

    # If hard safety barrier breached, immediately emit Tier 1 (ML cannot downgrade)
    if hard_tier1_breach:
        return "tier1", factors

    # 2. ML Score Tier 1 Check (OR logic: ML can elevate to Tier 1 even if hard threshold not hit yet)
    if ml_score >= 0.85:
        factors.append(f"ML anomaly score critical: {ml_score:.2f} (1D-CNN latent space deviation)")
        return "tier1", factors

    # 3. Tier 2 (Warning): Multi-vital divergence bands or ML warning
    tier2_breach = False
    if spo2 < settings.TIER2_SPO2_THRESHOLD:
        tier2_breach = True
        factors.append(f"SpO2 desaturation trend: {spo2}% (threshold < {settings.TIER2_SPO2_THRESHOLD}%)")

    if hr >= settings.TIER2_HR_HIGH:
        tier2_breach = True
        factors.append(f"Tachycardic acceleration: HR {hr} bpm")
    elif hr <= settings.TIER2_HR_LOW:
        tier2_breach = True
        factors.append(f"Bradycardic decline: HR {hr} bpm")

    if ml_score >= 0.50:
        tier2_breach = True
        factors.append(f"ML anomaly trend detected: score {ml_score:.2f}")

    if tier2_breach:
        return "tier2", factors

    # 4. Tier 3 (Advisory): Transient minor divergence
    if spo2 < 94.0 or hr > 105.0 or ml_score >= 0.30:
        factors.append(f"Minor telemetry drift (SpO2 {spo2}%, HR {hr} bpm, ML {ml_score:.2f})")
        return "tier3", factors

    return "normal", ["Vitals within baseline tolerance", "Sinus rhythm stable"]
