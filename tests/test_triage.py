"""Unit tests for TriageService OR'd 3-tier decision engine."""

import asyncio
from datetime import datetime, timezone
import numpy as np
import pytest

from backend.app.schemas.telemetry import ProcessedTelemetryTick
from backend.app.services.ring_buffer import TelemetryRingBuffer
from backend.app.services.triage import TriageService


def test_hard_threshold_eval_unconditional_on_cold_start():
    """Test hard physiological threshold (SpO2 < 85) evaluates unconditionally on tick 1 (cold start)."""

    async def _test():
        ring_buffer = TelemetryRingBuffer(use_fallback=True)
        triage = TriageService(ring_buffer=ring_buffer)

        # Bed-01 has empty buffer (is_ready = False)
        assert await ring_buffer.is_ready("bed-01") is False

        tick = ProcessedTelemetryTick(
            bed_id="bed-01",
            ts=datetime.now(timezone.utc),
            seq=1,
            hr=78.0,
            spo2=82.0,  # Hard breach (< 85)!
            bp_sys=120.0,
            bp_dia=80.0,
            ecg_lead_ok=True,
        )

        decision = await triage.evaluate_tick(tick)

        assert decision.tier == 1, "Hard breach must fire Tier 1 immediately"
        assert decision.hard_breach is True
        assert decision.is_cold_start is True
        assert "SpO2=82% < 85%" in decision.reason

    asyncio.run(_test())


def test_cold_start_reason_label_and_zero_ml_score():
    """Test cold start without hard breach returns ml_score=0.0 and reason='cold_start'."""

    async def _test():
        ring_buffer = TelemetryRingBuffer(use_fallback=True)
        triage = TriageService(ring_buffer=ring_buffer)

        tick = ProcessedTelemetryTick(
            bed_id="bed-02",
            ts=datetime.now(timezone.utc),
            seq=1,
            hr=75.0,
            spo2=98.0,
            bp_sys=120.0,
            bp_dia=80.0,
            ecg_lead_ok=True,
        )

        decision = await triage.evaluate_tick(tick)

        assert decision.tier == 3
        assert decision.confidence == 0.0
        assert decision.is_cold_start is True
        assert decision.reason == "cold_start", "Reason must be 'cold_start' (not 'healthy')"

    asyncio.run(_test())


def test_hysteresis_debouncing_and_hard_bypass():
    """Test non-hard tier change requires 3 consecutive ticks, while hard breach fires on tick 1."""

    async def _test():
        ring_buffer = TelemetryRingBuffer(use_fallback=True)
        triage = TriageService(ring_buffer=ring_buffer, hysteresis_count=3)
        bed_id = "bed-03"

        # Mock is_ready and get_window to simulate ready state with window
        async def mock_is_ready(b_id):
            return True
        async def mock_get_window(b_id):
            return np.zeros((3, 100), dtype=np.float32)

        ring_buffer.is_ready = mock_is_ready
        ring_buffer.get_window = mock_get_window

        # Mock _score_window to return Tier 2 warning score (0.75) attributed to SpO2
        triage._score_window = lambda win: (0.75, "spo2", {"hr": 0.1, "spo2": 0.75, "bp_sys": 0.1})

        tick = ProcessedTelemetryTick(
            bed_id=bed_id,
            ts=datetime.now(timezone.utc),
            seq=1,
            hr=75.0,
            spo2=98.0,
            bp_sys=120.0,
            bp_dia=80.0,
            ecg_lead_ok=True,
        )

        # Tick 1: candidate=2, count=1 -> confirmed_tier stays 3
        d1 = await triage.evaluate_tick(tick)
        assert d1.raw_tier == 2
        assert d1.tier == 3, "Tick 1 must not confirm Tier 2 yet"

        # Tick 2: candidate=2, count=2 -> confirmed_tier stays 3
        d2 = await triage.evaluate_tick(tick)
        assert d2.tier == 3, "Tick 2 must not confirm Tier 2 yet"

        # Tick 3: candidate=2, count=3 -> confirmed_tier becomes 2!
        d3 = await triage.evaluate_tick(tick)
        assert d3.tier == 2, "Tick 3 must confirm Tier 2"
        assert "SPO2 divergent" in d3.reason

        # Now send HARD BREACH tick (HR = 15 < 20) -> Must fire Tier 1 IMMEDIATELY on tick 1!
        hard_tick = ProcessedTelemetryTick(
            bed_id=bed_id,
            ts=datetime.now(timezone.utc),
            seq=4,
            hr=15.0,  # Hard breach
            spo2=98.0,
            bp_sys=120.0,
            bp_dia=80.0,
            ecg_lead_ok=True,
        )
        d_hard = await triage.evaluate_tick(hard_tick)
        assert d_hard.tier == 1, "Hard breach must bypass hysteresis and fire Tier 1 on tick 1"
        assert d_hard.hard_breach is True

    asyncio.run(_test())


def test_triage_reset_clears_state_and_wired_to_ring_buffer():
    """Test reset(bed_id) clears hysteresis state and is triggered by ring_buffer.reset()."""

    async def _test():
        ring_buffer = TelemetryRingBuffer(use_fallback=True)
        triage = TriageService(ring_buffer=ring_buffer, hysteresis_count=3)
        bed_id = "bed-04"

        # Simulate tier 1 hard breach
        hard_tick = ProcessedTelemetryTick(
            bed_id=bed_id,
            ts=datetime.now(timezone.utc),
            seq=1,
            hr=15.0,
            spo2=98.0,
            bp_sys=120.0,
            bp_dia=80.0,
            ecg_lead_ok=True,
        )
        d1 = await triage.evaluate_tick(hard_tick)
        assert d1.tier == 1

        # Reset ring buffer (which triggers triage.reset callback)
        await ring_buffer.reset(bed_id)

        # State should be reset to cold start and tier 3
        h_state = triage._get_hysteresis_state(bed_id)
        assert h_state.current_confirmed_tier == 3
        assert h_state.candidate_count == 0

    asyncio.run(_test())
