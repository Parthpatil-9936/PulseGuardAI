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


def test_bp_hard_thresholds_evaluated_on_tick_1():
    """Test catastrophic BP hard limits evaluated unconditionally on tick 1 (no window):
    - bp_sys=55 (profound hypotension < 60) -> immediate Tier-1
    - bp_sys=210 (hypertensive crisis > 200) -> immediate Tier-1
    - bp_dia=125 (hypertensive crisis > 120) -> immediate Tier-1
    """

    async def _test():
        ring_buffer = TelemetryRingBuffer(use_fallback=True)
        triage = TriageService(ring_buffer=ring_buffer)

        # 1. Profound hypotension: bp_sys = 55 (< 60) on tick 1 with empty buffer
        tick_hypo = ProcessedTelemetryTick(
            bed_id="bed-05",
            ts=datetime.now(timezone.utc),
            seq=1,
            hr=75.0,
            spo2=98.0,
            bp_sys=55.0,
            bp_dia=35.0,
            ecg_lead_ok=True,
        )
        d_hypo = await triage.evaluate_tick(tick_hypo)
        assert d_hypo.tier == 1, "bp_sys=55 must trigger Tier-1 immediately"
        assert d_hypo.hard_breach is True
        assert d_hypo.is_cold_start is True
        assert "BP_sys=55 < 60 mmHg" in d_hypo.reason

        # 2. Hypertensive crisis systolic: bp_sys = 210 (> 200) on tick 1
        tick_hyper_sys = ProcessedTelemetryTick(
            bed_id="bed-06",
            ts=datetime.now(timezone.utc),
            seq=1,
            hr=80.0,
            spo2=97.0,
            bp_sys=210.0,
            bp_dia=95.0,
            ecg_lead_ok=True,
        )
        d_hyper_sys = await triage.evaluate_tick(tick_hyper_sys)
        assert d_hyper_sys.tier == 1, "bp_sys=210 must trigger Tier-1 immediately"
        assert d_hyper_sys.hard_breach is True
        assert d_hyper_sys.is_cold_start is True
        assert "BP_sys=210 > 200 mmHg" in d_hyper_sys.reason

        # 3. Hypertensive crisis diastolic: bp_dia = 125 (> 120) on tick 1
        tick_hyper_dia = ProcessedTelemetryTick(
            bed_id="bed-07",
            ts=datetime.now(timezone.utc),
            seq=1,
            hr=82.0,
            spo2=99.0,
            bp_sys=150.0,
            bp_dia=125.0,
            ecg_lead_ok=True,
        )
        d_hyper_dia = await triage.evaluate_tick(tick_hyper_dia)
        assert d_hyper_dia.tier == 1, "bp_dia=125 must trigger Tier-1 immediately"
        assert d_hyper_dia.hard_breach is True
        assert d_hyper_dia.is_cold_start is True
        assert "BP_dia=125 > 120 mmHg" in d_hyper_dia.reason

    asyncio.run(_test())


def test_ecg_lead_disconnect_true_hard_threshold_on_tick_1():
    """Test ecg_lead_ok=False triggers Tier-1 immediately on tick 1 with distinct reason string."""

    async def _test():
        ring_buffer = TelemetryRingBuffer(use_fallback=True)
        triage = TriageService(ring_buffer=ring_buffer)

        # Buffer is not ready (tick 1 cold start)
        assert await ring_buffer.is_ready("bed-08") is False

        tick_lead_off = ProcessedTelemetryTick(
            bed_id="bed-08",
            ts=datetime.now(timezone.utc),
            seq=1,
            hr=72.0,
            spo2=98.0,
            bp_sys=120.0,
            bp_dia=80.0,
            ecg_lead_ok=False,  # Hardware disconnect!
        )

        decision = await triage.evaluate_tick(tick_lead_off)

        assert decision.tier == 1, "Lead disconnect must trigger Tier-1 immediately on tick 1"
        assert decision.hard_breach is True
        assert decision.is_cold_start is True
        assert decision.reason == "CRITICAL: ECG lead disconnected — no signal", (
            "Must have distinct lead-off reason string"
        )

    asyncio.run(_test())


def test_mute_clamping_on_live_tier1_alert():
    """Test mute handling on live Tier-1 alert under chosen Option B rule:
    - Attempted mute with duration > 300s is deterministically hard-clamped to 300s.
    - Siren is silenced (audio_muted=True), but visual escalation remains continuously active (visual_escalation=True).
    - Forced unmute occurs after 300s expiration if vital breach persists.
    - Attempting to mute an inactive alert (Tier 3) is rejected.
    """

    async def _test():
        from datetime import timedelta
        ring_buffer = TelemetryRingBuffer(use_fallback=True)
        triage = TriageService(ring_buffer=ring_buffer)
        bed_id = "bed-09"
        base_time = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)

        # 1. Generate live Tier-1 alert (profound hypotension bp_sys=55)
        tick1 = ProcessedTelemetryTick(
            bed_id=bed_id,
            ts=base_time,
            seq=1,
            hr=75.0,
            spo2=98.0,
            bp_sys=55.0,
            bp_dia=35.0,
            ecg_lead_ok=True,
        )
        d1 = await triage.evaluate_tick(tick1)
        assert d1.tier == 1
        assert d1.audio_muted is False
        assert d1.visual_escalation is True

        # 2. Clinician attempts excessive mute duration (9999s)
        mute_state = triage.mute_alert(
            bed_id=bed_id,
            duration_s=9999,
            clinician_id="MD-101",
            ts=base_time,
        )
        # Server clamps to 300 seconds
        assert mute_state.mute_duration_s == 300, "Mute duration must be clamped to 300s"
        assert mute_state.is_muted is True
        assert mute_state.visual_escalation is True, "Visual escalation must persist during mute"

        # 3. Next tick 60s later (still in mute window, vitals still critical)
        tick2 = ProcessedTelemetryTick(
            bed_id=bed_id,
            ts=base_time + timedelta(seconds=60),
            seq=2,
            hr=75.0,
            spo2=98.0,
            bp_sys=55.0,
            bp_dia=35.0,
            ecg_lead_ok=True,
        )
        d2 = await triage.evaluate_tick(tick2)
        assert d2.tier == 1
        assert d2.audio_muted is True, "Audio siren must be muted within 300s window"
        assert d2.visual_escalation is True, "Visual escalation remains active during mute"
        assert d2.remaining_mute_s == 240, "Remaining mute time should be 240s"

        # 4. Next tick 301s later (exceeded 300s hard ceiling -> FORCED UNMUTE)
        tick3 = ProcessedTelemetryTick(
            bed_id=bed_id,
            ts=base_time + timedelta(seconds=301),
            seq=3,
            hr=75.0,
            spo2=98.0,
            bp_sys=55.0,
            bp_dia=35.0,
            ecg_lead_ok=True,
        )
        d3 = await triage.evaluate_tick(tick3)
        assert d3.tier == 1
        assert d3.audio_muted is False, "Audio siren must forcibly unmute after 300s"
        assert d3.visual_escalation is True
        assert d3.remaining_mute_s == 0
        assert triage.get_mute_state(bed_id).is_muted is False

        # 5. Verify attempting to mute an inactive bed (Tier 3) is rejected
        normal_tick = ProcessedTelemetryTick(
            bed_id="bed-10",
            ts=base_time,
            seq=1,
            hr=75.0,
            spo2=98.0,
            bp_sys=120.0,
            bp_dia=80.0,
            ecg_lead_ok=True,
        )
        d_normal = await triage.evaluate_tick(normal_tick)
        assert d_normal.tier == 3
        with pytest.raises(ValueError, match="Cannot mute bed bed-10: no active alert"):
            triage.mute_alert("bed-10", duration_s=60)

    asyncio.run(_test())


def test_mute_policy_reject_tier1_option_a():
    """Test Option A policy ('reject_tier1') outright rejects muting Tier-1 alerts."""

    async def _test():
        ring_buffer = TelemetryRingBuffer(use_fallback=True)
        triage = TriageService(ring_buffer=ring_buffer, mute_policy="reject_tier1")
        bed_id = "bed-01"

        # Generate live Tier-1 breach
        tick = ProcessedTelemetryTick(
            bed_id=bed_id,
            ts=datetime.now(timezone.utc),
            seq=1,
            hr=15.0,  # Hard breach
            spo2=98.0,
            bp_sys=120.0,
            bp_dia=80.0,
            ecg_lead_ok=True,
        )
        d = await triage.evaluate_tick(tick)
        assert d.tier == 1

        # Attempting to mute live Tier-1 under Option A must be rejected outright
        with pytest.raises(PermissionError, match="Tier-1 critical sirens cannot be muted"):
            triage.mute_alert(bed_id, duration_s=120)

    asyncio.run(_test())
