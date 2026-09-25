"""PulseGuard-AI OR'd 3-Tier Decision Engine Service.

Implements the 3-Tier Alert Cascade triage rules:
1. Hard physiological thresholds (SpO2<85, HR<20, HR>220, lead off) evaluated UNCONDITIONALLY
   from tick 1 with 0 hysteresis delay (life safety invariant).
2. Cold start state: ML scoring runs only when `ring_buffer.is_ready(bed_id)` is True.
   If False, returns confidence=0.0 with reason="cold_start".
3. Per-vital attribution: factor attribution includes the channel name (HR/SpO2/BP_sys) with
   the highest normalized reconstruction error.
4. Hysteresis anti-flicker: requires non-hard tiers to persist for 3 consecutive ticks.
   Hard Tier-1 breaches bypass hysteresis immediately.
5. Explicit reset(bed_id): clears per-bed hysteresis state machine when a bed is reassigned.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Literal, Optional, Tuple, Union

import numpy as np
import torch

from backend.app.ml.autoencoder import (
    CHANNEL_NAMES,
    MAX_BOUNDS,
    MIN_BOUNDS,
    TelemetryAutoencoder,
    compute_per_channel_mse,
    scale_raw_window,
)
from backend.app.schemas.telemetry import ProcessedTelemetryTick
from backend.app.schemas.triage import TriageDecision
from backend.app.services.ring_buffer import TelemetryRingBuffer

logger = logging.getLogger(__name__)

# Hard physiological limits
HARD_SPO2_MIN = 85.0
HARD_HR_MIN = 20.0
HARD_HR_MAX = 220.0

HYSTERESIS_COUNT = 3  # Ticks required to confirm tier change (non-hard)


@dataclass
class HysteresisState:
    """Per-bed tier hysteresis state machine."""

    current_confirmed_tier: int = 3
    candidate_tier: int = 3
    candidate_count: int = 0


class TriageService:
    """OR'd 3-Tier Decision Triage Service combining hard limits & ML anomaly scoring."""

    def __init__(
        self,
        ring_buffer: Optional[TelemetryRingBuffer] = None,
        checkpoint_path: Path = Path("backend/app/ml/autoencoder_v1.pt"),
        hysteresis_count: int = HYSTERESIS_COUNT,
    ) -> None:
        self.ring_buffer = ring_buffer or TelemetryRingBuffer()
        self.checkpoint_path = checkpoint_path
        self.hysteresis_count = hysteresis_count

        self.model: Optional[TelemetryAutoencoder] = None
        self.per_channel_offset: Dict[str, float] = {
            "hr": 0.001,
            "spo2": 0.001,
            "bp_sys": 0.001,
        }
        self.per_channel_scale: Dict[str, float] = {
            "hr": 0.01,
            "spo2": 0.01,
            "bp_sys": 0.01,
        }

        # Load trained PyTorch checkpoint if available
        self._load_checkpoint()

        # Per-bed state machines
        self.hysteresis_states: Dict[str, HysteresisState] = {}

        # Auto-register reset callback with ring buffer
        self.ring_buffer.register_reset_callback(self.reset)

    def _load_checkpoint(self) -> None:
        """Load trained model state and per-channel calibration constants (.pt or .pkl)."""
        target_path = self.checkpoint_path
        if not target_path.exists() and target_path.with_suffix(".pkl").exists():
            target_path = target_path.with_suffix(".pkl")
        elif not target_path.exists() and target_path.with_suffix(".pt").exists():
            target_path = target_path.with_suffix(".pt")

        if not target_path.exists():
            logger.warning(
                f"[triage] Checkpoint {self.checkpoint_path} not found. "
                "Using uncalibrated fallback autoencoder model."
            )
            self.model = TelemetryAutoencoder(in_channels=3, latent_dim=16)
            self.model.eval()
            return

        try:
            if target_path.suffix == ".pkl":
                import pickle
                with open(target_path, "rb") as f:
                    ckpt = pickle.load(f)
            else:
                ckpt = torch.load(target_path, weights_only=False)

            model = TelemetryAutoencoder(
                in_channels=3, latent_dim=ckpt.get("latent_dim", 16)
            )
            model.load_state_dict(ckpt["model_state_dict"])
            model.eval()
            self.model = model

            if "per_channel_offset" in ckpt:
                self.per_channel_offset = ckpt["per_channel_offset"]
            if "per_channel_scale" in ckpt:
                self.per_channel_scale = ckpt["per_channel_scale"]

            logger.info(
                f"[triage] Loaded model checkpoint from {target_path}. "
                f"Offsets: {self.per_channel_offset}, Scales: {self.per_channel_scale}"
            )
        except Exception as e:
            logger.error(
                f"[triage] Failed to load checkpoint {self.checkpoint_path}: {e}. "
                "Using fallback model."
            )
            self.model = TelemetryAutoencoder(in_channels=3, latent_dim=16)
            self.model.eval()

    def _get_hysteresis_state(self, bed_id: str) -> HysteresisState:
        if bed_id not in self.hysteresis_states:
            self.hysteresis_states[bed_id] = HysteresisState()
        return self.hysteresis_states[bed_id]

    def reset(self, bed_id: str) -> None:
        """Reset per-bed hysteresis state machine and restore cold-start status."""
        logger.info(f"[triage] Resetting hysteresis triage state for bed {bed_id}")
        self.hysteresis_states[bed_id] = HysteresisState()

    # ----------------------------------------------------------------------
    # 1. Unconditional Hard Physiological Limits Check
    # ----------------------------------------------------------------------
    def check_hard_thresholds(
        self, tick: ProcessedTelemetryTick
    ) -> Tuple[bool, Optional[str]]:
        """Evaluate hard physiological limits UNCONDITIONALLY on every tick.

        Protects patient during cold start (first 10 seconds).
        Returns (hard_breach: bool, breach_detail: str).
        """
        breaches = []
        if tick.spo2 < HARD_SPO2_MIN:
            breaches.append(f"SpO2={tick.spo2:g}% < {HARD_SPO2_MIN:g}%")

        if tick.hr < HARD_HR_MIN:
            breaches.append(f"HR={tick.hr:g} < {HARD_HR_MIN:g} bpm")
        elif tick.hr > HARD_HR_MAX:
            breaches.append(f"HR={tick.hr:g} > {HARD_HR_MAX:g} bpm")

        if not tick.ecg_lead_ok:
            breaches.append("ECG Lead Off")

        if tick.drift_flag == "tamper":
            breaches.append("Sensor Disconnect / Tamper")

        if breaches:
            return True, ", ".join(breaches)
        return False, None

    # ----------------------------------------------------------------------
    # 2 & 3. ML Scoring, Calibration & Per-Vital Attribution
    # ----------------------------------------------------------------------
    def _score_window(
        self, raw_window: np.ndarray
    ) -> Tuple[float, str, Dict[str, float]]:
        """Run ML autoencoder scoring over a (3, 100) raw biological window.

        Returns (ml_confidence: float [0.0, 1.0], attributing_vital: str, norm_errors: dict).
        """
        if self.model is None:
            return 0.0, "none", {"hr": 0.0, "spo2": 0.0, "bp_sys": 0.0}

        # Min-max scale raw (3, 100) window
        scaled_win = scale_raw_window(raw_window)
        input_tensor = torch.from_numpy(scaled_win).unsqueeze(0)  # (1, 3, 100)

        with torch.no_grad():
            recon_tensor = self.model(input_tensor)
            channel_mse = (
                compute_per_channel_mse(input_tensor, recon_tensor)
                .squeeze(0)
                .numpy()
            )  # (3,)

        # Compute normalized errors per channel using offset/scale
        norm_errors: Dict[str, float] = {}
        for idx, cname in enumerate(CHANNEL_NAMES):
            raw_mse = float(channel_mse[idx])
            offset = self.per_channel_offset.get(cname, 0.001)
            scale = max(1e-6, self.per_channel_scale.get(cname, 0.01))

            # Normalize: clip((raw_error - offset) / scale, 0.0, 1.0)
            norm_val = float(np.clip((raw_mse - offset) / scale, 0.0, 1.0))
            norm_errors[cname] = norm_val

        # Find vital channel with highest normalized reconstruction error
        attributing_vital = max(norm_errors, key=lambda k: norm_errors[k])
        confidence = float(max(norm_errors.values()))

        return confidence, attributing_vital, norm_errors

    # ----------------------------------------------------------------------
    # Main Async Triage Pipeline Method
    # ----------------------------------------------------------------------
    async def evaluate_tick(self, tick: ProcessedTelemetryTick) -> TriageDecision:
        """Evaluate tick through hard thresholds, ML autoencoder, and hysteresis."""
        bed_id = tick.bed_id

        # Step 1: Unconditional Hard Threshold Check (0-delay safety net)
        hard_breach, breach_detail = self.check_hard_thresholds(tick)

        # Step 2: Check ML Readiness
        is_ready = await self.ring_buffer.is_ready(bed_id)
        is_cold_start = not is_ready

        ml_score = 0.0
        attributing_vital = "none"

        if is_ready:
            window_arr = await self.ring_buffer.get_window(bed_id)
            if window_arr is not None:
                ml_score, attributing_vital, _ = self._score_window(window_arr)

        # Determine pre-hysteresis raw_tier and reason string
        if hard_breach:
            raw_tier = 1
            reason = f"CATASTROPHIC: Hard limit breach ({breach_detail})"
        elif ml_score > 0.9:
            raw_tier = 1
            reason = (
                f"CATASTROPHIC: Severe {attributing_vital.upper()} trajectory divergence"
            )
        elif ml_score >= 0.5:
            raw_tier = 2
            reason = (
                f"WARNING: {attributing_vital.upper()} divergent from expected pattern"
            )
        elif is_cold_start:
            raw_tier = 3
            reason = "cold_start"
        else:
            raw_tier = 3
            reason = "Normal homeostatic baseline"

        # Step 4: Hysteresis / Anti-Flicker State Machine
        h_state = self._get_hysteresis_state(bed_id)

        if hard_breach:
            # SAFETY INVARIANT: Hard Tier-1 breaches fire IMMEDIATELY with NO hysteresis delay
            h_state.current_confirmed_tier = 1
            h_state.candidate_tier = 1
            h_state.candidate_count = 0
            confirmed_tier = 1
        else:
            if raw_tier == h_state.current_confirmed_tier:
                h_state.candidate_tier = raw_tier
                h_state.candidate_count = 0
            elif raw_tier == h_state.candidate_tier:
                h_state.candidate_count += 1
                if h_state.candidate_count >= self.hysteresis_count:
                    h_state.current_confirmed_tier = raw_tier
                    h_state.candidate_count = 0
            else:
                h_state.candidate_tier = raw_tier
                h_state.candidate_count = 1
                if h_state.candidate_count >= self.hysteresis_count:
                    h_state.current_confirmed_tier = raw_tier
                    h_state.candidate_count = 0

            confirmed_tier = h_state.current_confirmed_tier

        return TriageDecision(
            bed_id=bed_id,
            ts=tick.ts,
            tier=confirmed_tier,
            confidence=round(ml_score, 4),
            reason=reason,
            attributing_vital=attributing_vital,
            drift_flag=tick.drift_flag,
            is_cold_start=is_cold_start,
            hard_breach=hard_breach,
            raw_tier=raw_tier,
        )
