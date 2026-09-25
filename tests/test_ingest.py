"""Unit tests for TelemetryTick schema and TelemetryIngestionService."""

from datetime import datetime, timezone, timedelta
import pytest

from backend.app.schemas.telemetry import TelemetryTick, ProcessedTelemetryTick
from backend.app.services.ingest import (
    TelemetryIngestionService,
    InvalidTelemetryError,
)


def test_telemetry_tick_pydantic_bounds_valid():
    """Test valid tick passes Pydantic bounds check."""
    raw = {
        "bed_id": "bed-01",
        "ts": "2026-09-18T01:46:16.123Z",
        "hr": 78,
        "spo2": 98,
        "bp_sys": 120,
        "bp_dia": 80,
        "ecg_lead_ok": True,
        "seq": 10452,
    }
    tick = TelemetryTick.model_validate(raw)
    assert tick.bed_id == "bed-01"
    assert tick.hr == 78
    assert tick.spo2 == 98
    assert tick.bp_sys == 120
    assert tick.bp_dia == 80
    assert tick.seq == 10452


def test_telemetry_tick_invalid_bed_id():
    """Test invalid bed_id fails regex pattern ^bed-(0[1-9]|10)$."""
    raw = {
        "bed_id": "bed-99",  # Invalid
        "ts": "2026-09-18T01:46:16.123Z",
        "hr": 78,
        "spo2": 98,
        "bp_sys": 120,
        "bp_dia": 80,
        "seq": 100,
    }
    with pytest.raises(Exception):
        TelemetryTick.model_validate(raw)


def test_telemetry_tick_biologically_impossible_bounds():
    """Test out-of-bounds hr, spo2, bp raise ValidationError."""
    service = TelemetryIngestionService()

    # HR > 300
    with pytest.raises(InvalidTelemetryError):
        service.validate_raw_payload({
            "bed_id": "bed-01",
            "ts": "2026-09-18T01:46:16.123Z",
            "hr": 350,  # Invalid
            "spo2": 98,
            "bp_sys": 120,
            "bp_dia": 80,
            "seq": 1,
        })

    # SpO2 > 100
    with pytest.raises(InvalidTelemetryError):
        service.validate_raw_payload({
            "bed_id": "bed-01",
            "ts": "2026-09-18T01:46:16.123Z",
            "hr": 78,
            "spo2": 110,  # Invalid
            "bp_sys": 120,
            "bp_dia": 80,
            "seq": 2,
        })

    # Diastolic > Systolic
    with pytest.raises(InvalidTelemetryError):
        service.validate_raw_payload({
            "bed_id": "bed-01",
            "ts": "2026-09-18T01:46:16.123Z",
            "hr": 78,
            "spo2": 98,
            "bp_sys": 80,
            "bp_dia": 120,  # Invalid (dia > sys)
            "seq": 3,
        })


def test_reorder_defense_and_duplicate_dropping():
    """Test reordering out-of-order seq ticks, dropping duplicates, and flagging seq gaps > 5."""
    service = TelemetryIngestionService(reorder_buffer_size=3)

    base_ts = datetime.now(timezone.utc)

    # Tick 1 (seq=100)
    raw1 = {"bed_id": "bed-01", "ts": base_ts.isoformat(), "hr": 75, "spo2": 98, "bp_sys": 120, "bp_dia": 80, "seq": 100}
    # Tick 3 (seq=102) - arrives out of order before 101
    raw3 = {"bed_id": "bed-01", "ts": (base_ts + timedelta(seconds=0.2)).isoformat(), "hr": 76, "spo2": 98, "bp_sys": 121, "bp_dia": 81, "seq": 102}
    # Tick 2 (seq=101)
    raw2 = {"bed_id": "bed-01", "ts": (base_ts + timedelta(seconds=0.1)).isoformat(), "hr": 75, "spo2": 98, "bp_sys": 120, "bp_dia": 80, "seq": 101}

    # Push 1
    res1 = service.process_raw_payload(raw1)
    # Push 3
    res2 = service.process_raw_payload(raw3)
    # Push 2 -> triggers buffer flush of 3 items
    res3 = service.process_raw_payload(raw2)

    all_emitted = res1 + res2 + res3
    seqs = [t.seq for t in all_emitted]
    assert seqs == [100, 101, 102], "Ticks must be emitted in strictly ascending order"

    # Test Duplicate rejection (seq=101 sent again)
    dup = service.process_raw_payload(raw2)
    assert len(dup) == 0, "Duplicate seq must be dropped"

    # Test Seq Gap > 5 flagging
    raw_gap = {"bed_id": "bed-01", "ts": (base_ts + timedelta(seconds=1.0)).isoformat(), "hr": 75, "spo2": 98, "bp_sys": 120, "bp_dia": 80, "seq": 110}
    for _ in range(2):  # Fill buffer to force emit
        service.process_raw_payload({"bed_id": "bed-01", "ts": (base_ts + timedelta(seconds=1.1)).isoformat(), "hr": 75, "spo2": 98, "bp_sys": 120, "bp_dia": 80, "seq": 111})

    res_gap = service.process_raw_payload(raw_gap)
    gap_ticks = [t for t in res_gap if t.seq == 110]
    if not gap_ticks:
        # Check flushed buffer
        flushed = service.flush_reorder_buffer("bed-01")
        flushed_proc = []
        state = service._get_or_create_state("bed-01")
        for tick, gap_flag, gap_sz in flushed:
            hv, st = service._apply_rate_mismatch_forward_fill(state, tick)
            flushed_proc.append(ProcessedTelemetryTick(
                bed_id=tick.bed_id, ts=tick.ts, seq=tick.seq, hr=hv["hr"], spo2=hv["spo2"],
                bp_sys=hv["bp_sys"], bp_dia=hv["bp_dia"], temp=hv.get("temp"), ecg_lead_ok=tick.ecg_lead_ok,
                drift_flag="none", seq_gap_flag=gap_flag, seq_gap_size=gap_sz, staleness_ms=st
            ))
        gap_ticks = [t for t in flushed_proc if t.seq == 110]

    assert len(gap_ticks) == 1
    assert gap_ticks[0].seq_gap_flag is True
    assert gap_ticks[0].seq_gap_size == 7  # 110 - 102 - 1 = 7


def test_rate_mismatch_forward_fill_and_staleness():
    """Test sparse vital forward fill and staleness_ms tracking."""
    service = TelemetryIngestionService(reorder_buffer_size=1)

    t0 = datetime.now(timezone.utc)
    t1 = t0 + timedelta(milliseconds=500)

    # Tick 1 with temperature
    raw1 = {
        "bed_id": "bed-02",
        "ts": t0.isoformat(),
        "hr": 80,
        "spo2": 97,
        "bp_sys": 120,
        "bp_dia": 80,
        "temp": 36.8,
        "seq": 1,
    }
    p1 = service.process_raw_payload(raw1)[0]
    assert p1.temp == 36.8
    assert p1.staleness_ms["temp_staleness_ms"] == 0.0

    # Tick 2 missing temp and bp (rate mismatch)
    raw2 = {
        "bed_id": "bed-02",
        "ts": t1.isoformat(),
        "hr": 82,
        "spo2": 97,
        "temp": None,
        "seq": 2,
    }
    p2 = service.process_raw_payload(raw2)[0]
    assert p2.temp == 36.8, "Missing temp must be forward-filled from last known value"
    assert p2.staleness_ms["temp_staleness_ms"] == pytest.approx(500.0, abs=10.0)


def test_degenerate_signal_stuck_sensor_guard():
    """Test stuck sensor (zero rolling variance for >2s) sets drift_flag='tamper'."""
    service = TelemetryIngestionService(reorder_buffer_size=1)
    base_ts = datetime.now(timezone.utc)

    # Send 25 ticks with EXACTLY flat HR=80.0
    processed_ticks = []
    for i in range(25):
        raw = {
            "bed_id": "bed-03",
            "ts": (base_ts + timedelta(seconds=i * 0.1)).isoformat(),
            "hr": 80,  # Zero variance!
            "spo2": 98 + (i % 2),
            "bp_sys": 120 + (i % 3),
            "bp_dia": 80,
            "seq": i + 1,
        }
        res = service.process_raw_payload(raw)
        if res:
            processed_ticks.append(res[0])

    # After 20 ticks of zero variance, drift_flag must become 'tamper'
    last_ticks = processed_ticks[-5:]
    assert any(t.drift_flag == "tamper" for t in last_ticks), "Stuck sensor must flag drift_flag='tamper'"


def test_ecg_lead_disconnect_tamper_flag():
    """Test ecg_lead_ok=False sets drift_flag='tamper'."""
    service = TelemetryIngestionService(reorder_buffer_size=1)
    raw = {
        "bed_id": "bed-04",
        "ts": datetime.now(timezone.utc).isoformat(),
        "hr": 80,
        "spo2": 98,
        "bp_sys": 120,
        "bp_dia": 80,
        "ecg_lead_ok": False,
        "seq": 1,
    }
    res = service.process_raw_payload(raw)
    assert res[0].drift_flag == "tamper"
