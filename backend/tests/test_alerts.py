import pytest
from httpx import AsyncClient
from app.services.alert_service import evaluate_alert


def test_deterministic_hard_threshold_or_logic():
    # Invariant: SpO2 < 85% must trigger Tier 1 even if ML score is 0.0
    tier, factors = evaluate_alert({"spo2": 82.0, "hr": 75.0, "bp_sys": 120.0, "bp_dia": 80.0}, ml_score=0.0)
    assert tier == "tier1"
    assert any("SpO2 < 85%" in f for f in factors)

    # Invariant: Extreme tachycardia (HR >= 140) must trigger Tier 1
    tier_hr, factors_hr = evaluate_alert({"spo2": 98.0, "hr": 144.0, "bp_sys": 120.0, "bp_dia": 80.0}, ml_score=0.0)
    assert tier_hr == "tier1"
    assert any("tachycardia" in f.lower() for f in factors_hr)

    # Invariant: ML can elevate to Tier 1 even when vitals are currently within hard bounds
    tier_ml, factors_ml = evaluate_alert({"spo2": 97.0, "hr": 80.0, "bp_sys": 120.0, "bp_dia": 80.0}, ml_score=0.92)
    assert tier_ml == "tier1"
    assert any("ML anomaly score critical" in f for f in factors_ml)

    # Warning band: SpO2 < 90% -> Tier 2
    tier_warn, _ = evaluate_alert({"spo2": 88.0, "hr": 75.0, "bp_sys": 120.0, "bp_dia": 80.0}, ml_score=0.1)
    assert tier_warn == "tier2"


@pytest.mark.asyncio
async def test_mute_duration_server_hard_clamp(client: AsyncClient, auth_headers):
    headers = auth_headers("nurse_1", "nurse")

    # Client attempts to request 600 seconds (10 minutes) mute
    resp = await client.post("/mute", headers=headers, json={"bed_id": "01", "duration_seconds": 600})
    assert resp.status_code == 200
    data = resp.json()

    # Server MUST clamp to exactly 300 seconds maximum
    assert data["requested_duration_seconds"] == 600
    assert data["clamped_duration_seconds"] == 300
    assert data["active"] is True
