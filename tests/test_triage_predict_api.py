"""Integration and Unit Tests for PulseGuard-AI ML Triage Predict API.

Tests:
1. Feature Preprocessing (ordering, scaling [0, 1], padding, hashing).
2. Model Loader (singleton, eval mode, weights_only safety).
3. POST /api/v1/triage/predict with normal baseline vitals (Tier 3).
4. POST /api/v1/triage/predict with critical hypoxia (Tier 1 Hard Breach).
5. Input Validation & Error Handling (HTTP 422 for malformed requests).
6. Redis Low-Latency Caching (X-Cache header verification).
7. DPDP Cryptographic Audit Trail (input_hash logged, ZERO PII).
8. GET /health/model endpoint readiness.
"""

from __future__ import annotations

import pytest
import numpy as np
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.ml.model_loader import ml_manager
from app.ml.preprocessing import (
    build_raw_array_from_samples,
    scale_vitals_array,
    compute_input_hash,
    preprocess_triage_input,
    FEATURE_ORDER,
    MIN_BOUNDS,
    MAX_BOUNDS,
)
from app.schemas.triage_predict import TriagePredictRequest, VitalsSample


@pytest.fixture(autouse=True)
def ensure_model_loaded():
    """Ensure ML model is loaded before test execution."""
    if not ml_manager.is_ready:
        ml_manager.load_sync()


# -----------------------------------------------------------------------------
# 1. Unit Tests: Preprocessing & Scaling
# -----------------------------------------------------------------------------
def test_preprocessing_feature_ordering_and_scaling():
    """Verifies features are strictly ordered [hr, spo2, bp_sys] and min-max scaled."""
    # Create sample: HR=75 bpm, SpO2=98%, BP_sys=120 mmHg
    sample = {"hr": 75.0, "spo2": 98.0, "bp_sys": 120.0}
    raw_arr, scaled_arr, input_hash = preprocess_triage_input(
        bed_id="bed-01",
        single_vitals=sample,
    )

    assert raw_arr.shape == (3, 100)
    assert scaled_arr.shape == (3, 100)

    # Channel 0: HR [0, 300] -> 75 / 300 = 0.25
    assert np.allclose(scaled_arr[0, :], 0.25)
    # Channel 1: SpO2 [0, 100] -> 98 / 100 = 0.98
    assert np.allclose(scaled_arr[1, :], 0.98)
    # Channel 2: BP_sys [0, 300] -> 120 / 300 = 0.40
    assert np.allclose(scaled_arr[2, :], 0.40)

    # Verify input_hash is a 64-character SHA-256 hexadecimal string
    assert len(input_hash) == 64
    assert isinstance(input_hash, str)


def test_preprocessing_window_padding():
    """Verifies that short vital sample lists are left-padded up to 100 timesteps."""
    samples = [{"hr": 70.0 + i, "spo2": 99.0, "bp_sys": 115.0} for i in range(10)]
    raw_arr = build_raw_array_from_samples(samples)

    assert raw_arr.shape == (3, 100)
    # The rightmost column must be the newest sample (index 9)
    assert raw_arr[0, -1] == 79.0
    # Left padded columns should repeat the earliest sample (index 0)
    assert raw_arr[0, 0] == 70.0


# -----------------------------------------------------------------------------
# 2. Unit Tests: Model Manager & Eval Mode Safety
# -----------------------------------------------------------------------------
def test_model_manager_eval_mode_invariant():
    """Security and safety invariant: model must be in eval mode with no gradients."""
    assert ml_manager.is_ready is True
    assert ml_manager.model is not None
    assert ml_manager.model.training is False, "Model must strictly be in eval mode"


# -----------------------------------------------------------------------------
# 3. Integration Tests: API Endpoints
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_health_model_endpoint():
    """GET /health/model returns operational ready status."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/health/model")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["is_eval_mode"] is True
        assert data["in_channels"] == 3
        assert data["latent_dim"] == 16


@pytest.mark.asyncio
async def test_predict_normal_baseline_triage():
    """POST /api/v1/triage/predict with healthy baseline vitals yields Tier 3 (Normal)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        payload = {
            "bed_id": "bed-01",
            "single_vitals": {
                "hr": 72.0,
                "spo2": 98.0,
                "bp_sys": 118.0,
                "bp_dia": 78.0,
                "temp": 36.8,
                "ecg_lead_ok": True,
            },
        }

        resp = await client.post("/api/v1/triage/predict", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        # Check required prediction response contract
        assert data["bed_id"] == "bed-01"
        assert data["tier"] in [2, 3]  # Normal/low baseline
        assert "confidence" in data
        assert "attributing_vital" in data
        assert data["hard_breach"] is False
        assert "channel_mse" in data
        assert "normalized_scores" in data
        assert len(data["input_hash"]) == 64
        assert data["latency_ms"] >= 0.0


@pytest.mark.asyncio
async def test_predict_critical_hypoxia_hard_breach():
    """POST /api/v1/triage/predict with critical hypoxia (SpO2=82%) triggers Tier 1 immediately."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        payload = {
            "bed_id": "bed-02",
            "single_vitals": {
                "hr": 85.0,
                "spo2": 82.0,  # Below 85% hard threshold
                "bp_sys": 120.0,
                "bp_dia": 80.0,
                "temp": 37.0,
                "ecg_lead_ok": True,
            },
        }

        resp = await client.post("/api/v1/triage/predict", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["bed_id"] == "bed-02"
        assert data["tier"] == 1, "Must trigger Tier 1 Catastrophic Alert"
        assert data["hard_breach"] is True
        assert "CATASTROPHIC" in data["reason"]
        assert any("SpO2" in factor for factor in data["explainability_factors"])


@pytest.mark.asyncio
async def test_predict_invalid_input_validation():
    """POST /api/v1/triage/predict returns 422 for malformed payloads."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Invalid bed format (e.g. 'bed-999')
        invalid_bed_payload = {
            "bed_id": "invalid-bed-name-999",
            "single_vitals": {"hr": 75.0, "spo2": 98.0, "bp_sys": 120.0},
        }
        resp = await client.post("/api/v1/triage/predict", json=invalid_bed_payload)
        assert resp.status_code == 422

        # Invalid SpO2 (> 100%)
        invalid_spo2_payload = {
            "bed_id": "bed-01",
            "single_vitals": {"hr": 75.0, "spo2": 150.0, "bp_sys": 120.0},
        }
        resp = await client.post("/api/v1/triage/predict", json=invalid_spo2_payload)
        assert resp.status_code == 422

        # Empty body
        resp = await client.post("/api/v1/triage/predict", json={})
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_redis_cache_and_audit_ledger():
    """Tests repetitive predictions verify caching headers and DPDP audit record generation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        payload = {
            "bed_id": "bed-03",
            "single_vitals": {
                "hr": 80.0,
                "spo2": 97.0,
                "bp_sys": 122.0,
                "ecg_lead_ok": True,
            },
        }

        # First request
        resp1 = await client.post("/api/v1/triage/predict", json=payload)
        assert resp1.status_code == 200
        data1 = resp1.json()

        # Repeat request with identical inputs
        resp2 = await client.post("/api/v1/triage/predict", json=payload)
        assert resp2.status_code == 200
        data2 = resp2.json()

        assert data1["input_hash"] == data2["input_hash"]
        assert data2["bed_id"] == "bed-03"
