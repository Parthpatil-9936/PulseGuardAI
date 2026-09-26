"""PulseGuard-AI Telemetry Ingestion Service.

Implements the five core ingestion resilience requirements:
1. Pydantic bounds validation & biologically impossible value rejection.
2. Reorder defense (seq sorting, duplicate rejection, seq gap >5 flagging).
3. Rate mismatch handling (forward-fill missing vitals + staleness_ms tracking).
4. Cosine-similarity SQI drift/tamper check (Section 4.1).
5. Degenerate signal guard (rolling zero-variance stuck-sensor flag -> tamper).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Literal, Optional, Tuple

import numpy as np
from pydantic import ValidationError

try:
    from app.schemas.telemetry import ProcessedTelemetryTick, TelemetryTick
except ImportError:
    from backend.app.schemas.telemetry import ProcessedTelemetryTick, TelemetryTick

logger = logging.getLogger(__name__)

# Constants
REORDER_BUFFER_SIZE = 5  # Max ticks held to reorder out-of-order sequence
WINDOW_SIZE = 20         # 20 ticks = 2 seconds at 10 Hz
DRIFT_COSINE_THRESHOLD = 0.85
EPSILON = 1e-6

DEFAULT_BASELINES = {
    "hr": 75.0,
    "spo2": 98.0,
    "bp_sys": 120.0,
    "bp_dia": 80.0,
    "temp": 37.0,
}


class InvalidTelemetryError(ValueError):
    """Raised when an incoming payload breaches Pydantic biological bounds or contracts."""
    pass


@dataclass
class BedIngestionState:
    """Per-bed state tracker for reordering, rate mismatch, staleness, and SQI."""

    bed_id: str
    last_emitted_seq: Optional[int] = None
    last_known_vitals: Dict[str, Tuple[float, datetime]] = field(default_factory=dict)
    reorder_buffer: List[TelemetryTick] = field(default_factory=list)
    rolling_window: List[Dict[str, float]] = field(default_factory=list)
    zero_variance_counts: Dict[str, int] = field(
        default_factory=lambda: {"hr": 0, "spo2": 0, "bp_sys": 0, "bp_dia": 0}
    )
    baseline_vector: Optional[np.ndarray] = None

    def update_baseline(self, current_vector: np.ndarray) -> None:
        """Update exponential moving average baseline vector."""
        if self.baseline_vector is None:
            self.baseline_vector = current_vector.copy()
        else:
            self.baseline_vector = 0.95 * self.baseline_vector + 0.05 * current_vector


class TelemetryIngestionService:
    """Telemetry Ingestion Daemon Service implementing edge triage pre-filtering."""

    def __init__(self, reorder_buffer_size: int = REORDER_BUFFER_SIZE) -> None:
        self.reorder_buffer_size = reorder_buffer_size
        self.bed_states: Dict[str, BedIngestionState] = {}

    def _get_or_create_state(self, bed_id: str) -> BedIngestionState:
        if bed_id not in self.bed_states:
            self.bed_states[bed_id] = BedIngestionState(bed_id=bed_id)
        return self.bed_states[bed_id]

    # ----------------------------------------------------------------------
    # 1. Pydantic Bounds & Contract Validation
    # ----------------------------------------------------------------------
    def validate_raw_payload(self, raw_payload: dict) -> TelemetryTick:
        """Validate raw dictionary against TelemetryTick Pydantic bounds schema.

        Rejects biologically impossible values or ill-formed JSON payloads.
        """
        try:
            return TelemetryTick.model_validate(raw_payload)
        except ValidationError as ve:
            logger.warning(
                f"[ingest] Rejected biologically impossible / ill-formed tick: {ve}"
            )
            raise InvalidTelemetryError(f"Telemetry bounds violation: {ve}") from ve

    # ----------------------------------------------------------------------
    # 2. Reorder Defense & Monotonic Counter Validation
    # ----------------------------------------------------------------------
    def push_and_reorder(
        self, tick: TelemetryTick
    ) -> List[Tuple[TelemetryTick, bool, int]]:
        """Insert tick into reorder buffer sorted by `seq`.

        - Discards exact duplicate `seq` values (retransmissions).
        - Emits ticks in strictly ascending `seq` order.
        - Flags (does not drop) `seq` gaps > 5 as signal quality issues.

        Returns list of (emitted_tick, seq_gap_flag, seq_gap_size).
        """
        state = self._get_or_create_state(tick.bed_id)

        # Duplicate rejection: drop if seq already emitted or already in buffer
        if state.last_emitted_seq is not None and tick.seq <= state.last_emitted_seq:
            logger.info(
                f"[ingest] Bed {tick.bed_id}: Dropped duplicate/stale seq {tick.seq} "
                f"(last emitted: {state.last_emitted_seq})"
            )
            return []

        if any(t.seq == tick.seq for t in state.reorder_buffer):
            logger.info(
                f"[ingest] Bed {tick.bed_id}: Dropped duplicate buffered seq {tick.seq}"
            )
            return []

        # Insert and sort buffer by monotonic seq
        state.reorder_buffer.append(tick)
        state.reorder_buffer.sort(key=lambda t: t.seq)

        emitted: List[Tuple[TelemetryTick, bool, int]] = []

        # Emit if buffer threshold reached or seq is strictly next
        while len(state.reorder_buffer) >= self.reorder_buffer_size or (
            state.reorder_buffer
            and state.last_emitted_seq is not None
            and state.reorder_buffer[0].seq == state.last_emitted_seq + 1
        ):
            next_tick = state.reorder_buffer.pop(0)

            seq_gap_flag = False
            seq_gap_size = 0
            if state.last_emitted_seq is not None:
                gap = next_tick.seq - state.last_emitted_seq - 1
                if gap > 0:
                    seq_gap_size = gap
                    if gap > 5:
                        seq_gap_flag = True
                        logger.warning(
                            f"[ingest] Bed {next_tick.bed_id}: Sequence gap detected! "
                            f"seq jumped from {state.last_emitted_seq} to {next_tick.seq} "
                            f"(gap size: {gap})"
                        )

            state.last_emitted_seq = next_tick.seq
            emitted.append((next_tick, seq_gap_flag, seq_gap_size))

        return emitted

    def flush_reorder_buffer(
        self, bed_id: str
    ) -> List[Tuple[TelemetryTick, bool, int]]:
        """Flush remaining buffered ticks for a bed."""
        state = self._get_or_create_state(bed_id)
        emitted: List[Tuple[TelemetryTick, bool, int]] = []
        while state.reorder_buffer:
            next_tick = state.reorder_buffer.pop(0)
            seq_gap_flag = False
            seq_gap_size = 0
            if state.last_emitted_seq is not None:
                gap = next_tick.seq - state.last_emitted_seq - 1
                if gap > 0:
                    seq_gap_size = gap
                    if gap > 5:
                        seq_gap_flag = True

            state.last_emitted_seq = next_tick.seq
            emitted.append((next_tick, seq_gap_flag, seq_gap_size))
        return emitted

    # ----------------------------------------------------------------------
    # 3. Rate Mismatch Handling & Forward-Fill Staleness Tracking
    # ----------------------------------------------------------------------
    def _apply_rate_mismatch_forward_fill(
        self, state: BedIngestionState, tick: TelemetryTick
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Forward-fill missing vitals and calculate staleness in milliseconds."""
        vitals_present = {
            "hr": tick.hr,
            "spo2": tick.spo2,
            "bp_sys": tick.bp_sys,
            "bp_dia": tick.bp_dia,
            "temp": tick.temp,
        }

        held_values: Dict[str, float] = {}
        staleness_ms: Dict[str, float] = {}

        for vital_name, raw_val in vitals_present.items():
            stale_key = f"{vital_name}_staleness_ms"
            if raw_val is not None:
                val = float(raw_val)
                state.last_known_vitals[vital_name] = (val, tick.ts)
                held_values[vital_name] = val
                staleness_ms[stale_key] = 0.0
            else:
                # Forward fill
                if vital_name in state.last_known_vitals:
                    last_val, last_ts = state.last_known_vitals[vital_name]
                    held_values[vital_name] = last_val
                    delta_ms = max(0.0, (tick.ts - last_ts).total_seconds() * 1000.0)
                    staleness_ms[stale_key] = round(delta_ms, 2)
                else:
                    # Default baseline fallback
                    fallback = DEFAULT_BASELINES.get(vital_name, 0.0)
                    held_values[vital_name] = fallback
                    staleness_ms[stale_key] = 0.0

        return held_values, staleness_ms

    # ----------------------------------------------------------------------
    # 4 & 5. Cosine SQI & Degenerate Signal (Stuck Sensor) Check
    # ----------------------------------------------------------------------
    def _evaluate_sqi_and_degenerate_guard(
        self,
        state: BedIngestionState,
        tick: TelemetryTick,
        vitals: Dict[str, float],
    ) -> Literal["none", "drift", "tamper"]:
        """Compute Cosine Similarity SQI & Degenerate Signal Guard.

        - Discontinuous spikes / `ecg_lead_ok == False` -> "tamper"
        - Zero-variance stuck sensor (>2s = 20 ticks) -> "tamper" (with epsilon safety)
        - Low-frequency baseline wander (cosine similarity < 0.85) -> "drift"
        - Normal baseline -> "none"
        """
        # Immediate hardware electrode disconnect check
        if not tick.ecg_lead_ok:
            return "tamper"

        # Current 4-vital vector: [hr, spo2, bp_sys, bp_dia]
        vec = np.array(
            [vitals["hr"], vitals["spo2"], vitals["bp_sys"], vitals["bp_dia"]],
            dtype=np.float64,
        )

        # Update rolling window for zero-variance and cosine similarity
        state.rolling_window.append(
            {
                "hr": vitals["hr"],
                "spo2": vitals["spo2"],
                "bp_sys": vitals["bp_sys"],
                "bp_dia": vitals["bp_dia"],
            }
        )
        if len(state.rolling_window) > WINDOW_SIZE:
            state.rolling_window.pop(0)

        # 5. Degenerate Signal Guard: Check for zero rolling variance over 2 seconds
        is_stuck_sensor = False
        if len(state.rolling_window) >= WINDOW_SIZE:
            for vital_key in ("hr", "spo2", "bp_sys", "bp_dia"):
                arr = np.array(
                    [item[vital_key] for item in state.rolling_window], dtype=np.float64
                )
                # Compute variance safely with epsilon guard against divide-by-zero
                var = float(np.var(arr))
                safe_var = var + EPSILON

                if var < 1e-9:
                    state.zero_variance_counts[vital_key] += 1
                    is_stuck_sensor = True
                    logger.warning(
                        f"[ingest] Bed {state.bed_id}: Degenerate zero variance "
                        f"detected on channel '{vital_key}' for >2.0s! Flagging tamper."
                    )
                else:
                    state.zero_variance_counts[vital_key] = 0

        if is_stuck_sensor:
            return "tamper"

        # Update baseline vector for cosine similarity
        state.update_baseline(vec)

        # 4. Cosine Similarity SQI calculation
        norm_vec = np.linalg.norm(vec)
        norm_base = np.linalg.norm(state.baseline_vector)

        # Safe denominator with EPSILON to prevent divide-by-zero
        denom = (norm_vec * norm_base) + EPSILON
        cosine_sim = float(np.dot(vec, state.baseline_vector) / denom)

        if cosine_sim < DRIFT_COSINE_THRESHOLD:
            return "drift"

        return "none"

    # ----------------------------------------------------------------------
    # Main Ingestion Entry Point
    # ----------------------------------------------------------------------
    def process_raw_payload(self, raw_payload: dict) -> List[ProcessedTelemetryTick]:
        """Full ingestion pipeline for a raw JSON tick payload.

        1. Validates bounds (raises InvalidTelemetryError if invalid).
        2. Reorders sequence ticks and flags sequence gaps > 5.
        3. Forward-fills missing vitals and attaches staleness_ms.
        4. Calculates Cosine Similarity SQI and Degenerate Signal Guard.
        """
        # Step 1: Validate payload bounds
        valid_tick = self.validate_raw_payload(raw_payload)

        # Step 2: Push to reorder buffer
        emitted_ticks = self.push_and_reorder(valid_tick)

        processed_list: List[ProcessedTelemetryTick] = []
        state = self._get_or_create_state(valid_tick.bed_id)

        for tick, seq_gap_flag, seq_gap_size in emitted_ticks:
            # Step 3: Forward fill & staleness tracking
            held_vitals, staleness_ms = self._apply_rate_mismatch_forward_fill(
                state, tick
            )

            # Step 4 & 5: SQI & Degenerate signal check
            drift_flag = self._evaluate_sqi_and_degenerate_guard(
                state, tick, held_vitals
            )

            processed = ProcessedTelemetryTick(
                bed_id=tick.bed_id,
                ts=tick.ts,
                seq=tick.seq,
                hr=held_vitals["hr"],
                spo2=held_vitals["spo2"],
                bp_sys=held_vitals["bp_sys"],
                bp_dia=held_vitals["bp_dia"],
                temp=held_vitals.get("temp"),
                ecg_lead_ok=tick.ecg_lead_ok,
                drift_flag=drift_flag,
                seq_gap_flag=seq_gap_flag,
                seq_gap_size=seq_gap_size,
                staleness_ms=staleness_ms,
            )
            processed_list.append(processed)

        return processed_list
