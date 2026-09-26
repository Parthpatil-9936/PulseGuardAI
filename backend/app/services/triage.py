"""PulseGuard-AI OR'd 3-Tier Decision Engine Service.

Implements the 3-Tier Alert Cascade triage rules:
1. Hard physiological thresholds (SpO2<85, HR<20, HR>220, BP_sys<60, BP_sys>200 or BP_dia>120,
   and ECG lead off) evaluated UNCONDITIONALLY from tick 1 with 0 hysteresis delay (life safety invariant).
2. Hardware lead disconnect (ecg_lead_ok == False) triggers immediate Tier-1 with distinct
   reason string: "CRITICAL: ECG lead disconnected — no signal".
3. Server-enforced mute clamping with persistent visual escalation: Tier-1 sirens can be temporarily
   muted (audio silenced) for bedside interventions, strictly hard-capped server-side at 300 seconds
   (5 minutes) with forced unmute, while visual escalation remains unsuppressable and active.
4. Cold start state: ML scoring runs only when `ring_buffer.is_ready(bed_id)` is True.
   If False, returns confidence=0.0 with reason="cold_start".
5. Per-vital attribution: factor attribution includes the channel name (HR/SpO2/BP_sys) with
   the highest normalized reconstruction error.
6. Hysteresis anti-flicker: requires non-hard tiers to persist for 3 consecutive ticks.
   Hard Tier-1 breaches bypass hysteresis immediately.
7. Explicit reset(bed_id): clears per-bed hysteresis state machine and mute state when a bed is reassigned.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Literal, Optional, Tuple, Union

import numpy as np
import torch

try:
    from app.ml.autoencoder import (
        CHANNEL_NAMES,
        MAX_BOUNDS,
        MIN_BOUNDS,
        TelemetryAutoencoder,
        compute_per_channel_mse,
        scale_raw_window,
    )
    from app.schemas.telemetry import ProcessedTelemetryTick
    from app.schemas.triage import TriageDecision
    from app.services.ring_buffer import TelemetryRingBuffer
except ImportError:
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
HARD_BP_SYS_MIN = 60.0
HARD_BP_SYS_MAX = 200.0
HARD_BP_DIA_MAX = 120.0

# Hardware / Lead Disconnect distinct reason
ECG_LEAD_DISCONNECT_REASON = "CRITICAL: ECG lead disconnected — no signal"

# Server-enforced mute ceiling (Option B)
MAX_MUTE_DURATION_S = 300  # 5 minutes maximum

HYSTERESIS_COUNT = 3  # Ticks required to confirm tier change (non-hard)


@dataclass
class HysteresisState:
    """Per-bed tier hysteresis state machine."""

    current_confirmed_tier: int = 3
    candidate_tier: int = 3
    candidate_count: int = 0


@dataclass
class MuteState:
    """Per-bed alarm siren mute state machine.

    Enforces Option (B) Rule:
    - Tier-1 audio sirens can be temporarily muted so bedside clinicians can conduct emergency
      care without auditory distress.
    - Hard-capped at 300 seconds (5 minutes) server-side; client inputs >300s are strictly clamped.
    - Visual escalation remains unsuppressable and continuously active while audio is silenced.
    - Forced unmute occurs automatically once the clamped duration expires if condition persists.
    """

    is_muted: bool = False
    muted_at: Optional[datetime] = None
    mute_duration_s: int = 0
    mute_expires_at: Optional[datetime] = None
    visual_escalation: bool = False
    clinician_id: Optional[str] = None


class TriageService:
    """OR'd 3-Tier Decision Triage Service combining hard limits & ML anomaly scoring."""

    def __init__(
        self,
        ring_buffer: Optional[TelemetryRingBuffer] = None,
        checkpoint_path: Path = Path("backend/app/ml/autoencoder_v1.pt"),
        hysteresis_count: int = HYSTERESIS_COUNT,
        mute_policy: Literal["clamp_with_visual_escalation", "reject_tier1"] = "clamp_with_visual_escalation",
    ) -> None:
        self.ring_buffer = ring_buffer or TelemetryRingBuffer()
        self.checkpoint_path = checkpoint_path
        self.hysteresis_count = hysteresis_count
        self.mute_policy = mute_policy

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
        self.mute_states: Dict[str, MuteState] = {}

        # Auto-register reset callback with ring buffer
        self.ring_buffer.register_reset_callback(self.reset)

    def _load_checkpoint(self) -> None:
        """Load trained model state (.pt) and per-channel calibration constants (.json or .pt).

        Security invariant: No pickle deserialization is used anywhere in the inference path.
        Model weights are loaded strictly with weights_only=True to prevent arbitrary code execution.
        """
        target_path = self.checkpoint_path
        if not target_path.exists() and target_path.with_suffix(".pt").exists():
            target_path = target_path.with_suffix(".pt")

        if not target_path.exists():
            logger.warning(
                f"[triage] Checkpoint {self.checkpoint_path} not found. "
                "Using uncalibrated fallback autoencoder model."
            )
            self.model = TelemetryAutoencoder(in_channels=3, latent_dim=16)
            self.model.eval()
            assert self.model is not None and not self.model.training, (
                "FATAL: Autoencoder model must be in eval mode (model.training == False) "
                "before service accepts live traffic"
            )
            return

        try:
            # Safe deserialization strictly enforcing weights_only=True (no arbitrary code execution)
            ckpt = torch.load(target_path, weights_only=True)

            model = TelemetryAutoencoder(
                in_channels=3, latent_dim=ckpt.get("latent_dim", 16)
            )
            model.load_state_dict(ckpt["model_state_dict"])
            model.eval()
            self.model = model

            # Prefer secure calibration_v1.json if present
            calib_json = target_path.with_name("calibration_v1.json")
            if calib_json.exists():
                with open(calib_json, "r", encoding="utf-8") as f:
                    calib_dict = json.load(f)
                if "per_channel_offset" in calib_dict:
                    self.per_channel_offset = calib_dict["per_channel_offset"]
                if "per_channel_scale" in calib_dict:
                    self.per_channel_scale = calib_dict["per_channel_scale"]
            else:
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

        # Startup assertion: fail loudly at startup, not silently in production
        assert self.model is not None and not self.model.training, (
            "FATAL: Autoencoder model must be in evaluation mode (model.training == False) "
            "before service accepts live traffic"
        )

    def _get_hysteresis_state(self, bed_id: str) -> HysteresisState:
        if bed_id not in self.hysteresis_states:
            self.hysteresis_states[bed_id] = HysteresisState()
        return self.hysteresis_states[bed_id]

    def reset(self, bed_id: str) -> None:
        """Reset per-bed hysteresis state machine and restore cold-start status."""
        logger.info(f"[triage] Resetting hysteresis triage state for bed {bed_id}")
        self.hysteresis_states[bed_id] = HysteresisState()
        self.mute_states[bed_id] = MuteState()

    # ----------------------------------------------------------------------
    # 1. Unconditional Hard Physiological Limits Check
    # ----------------------------------------------------------------------
    def check_hard_thresholds(
        self, tick: ProcessedTelemetryTick
    ) -> Tuple[bool, Optional[str]]:
        """Evaluate hard physiological limits UNCONDITIONALLY on every tick.

        Protects patient during cold start (first 10 seconds).
        Evaluates SpO2 < 85, HR < 20 / HR > 220, profound hypotension (BP_sys < 60),
        hypertensive crisis (BP_sys > 200 or BP_dia > 120), and ECG lead disconnect
        unconditionally with zero hysteresis delay.

        Returns (hard_breach: bool, breach_detail: str).
        """
        breaches = []
        if tick.spo2 < HARD_SPO2_MIN:
            breaches.append(f"SpO2={tick.spo2:g}% < {HARD_SPO2_MIN:g}%")

        if tick.hr < HARD_HR_MIN:
            breaches.append(f"HR={tick.hr:g} < {HARD_HR_MIN:g} bpm")
        elif tick.hr > HARD_HR_MAX:
            breaches.append(f"HR={tick.hr:g} > {HARD_HR_MAX:g} bpm")

        # Catastrophic BP hard limits (profound hypotension / hypertensive crisis)
        if tick.bp_sys < HARD_BP_SYS_MIN:
            breaches.append(f"BP_sys={tick.bp_sys:g} < {HARD_BP_SYS_MIN:g} mmHg")
        elif tick.bp_sys > HARD_BP_SYS_MAX:
            breaches.append(f"BP_sys={tick.bp_sys:g} > {HARD_BP_SYS_MAX:g} mmHg")

        if tick.bp_dia > HARD_BP_DIA_MAX:
            breaches.append(f"BP_dia={tick.bp_dia:g} > {HARD_BP_DIA_MAX:g} mmHg")

        # Hardware electrode impedance / lead-off status
        if not tick.ecg_lead_ok:
            breaches.append(ECG_LEAD_DISCONNECT_REASON)

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

        assert not self.model.training, "FATAL: Autoencoder model must be in eval mode during inference"

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
        if not tick.ecg_lead_ok:
            # Wire lead-disconnect as a true hard threshold with distinct reason string
            raw_tier = 1
            reason = ECG_LEAD_DISCONNECT_REASON
        elif hard_breach:
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

        # Step 5: Mute-Clamping State Evaluation & Forced Unmute (Option B)
        mute_state = self._get_mute_state(bed_id)
        audio_muted = False
        remaining_mute_s = 0
        visual_escalation = False

        if confirmed_tier == 1:
            # Visual escalation is always unsuppressable for Tier-1 alerts
            visual_escalation = True
            if mute_state.is_muted:
                tick_ts = tick.ts if tick.ts.tzinfo is not None else tick.ts.replace(tzinfo=timezone.utc)
                if mute_state.mute_expires_at is not None and tick_ts >= mute_state.mute_expires_at:
                    # FORCED UNMUTE: Server-enforced hard ceiling reached
                    mute_state.is_muted = False
                    mute_state.mute_duration_s = 0
                    mute_state.mute_expires_at = None
                    audio_muted = False
                    remaining_mute_s = 0
                    logger.info(
                        f"[triage] Forced unmute for bed {bed_id}: clamped mute duration expired while in Tier-1"
                    )
                else:
                    audio_muted = True
                    if mute_state.mute_expires_at is not None:
                        remaining_mute_s = max(
                            0, int((mute_state.mute_expires_at - tick_ts).total_seconds())
                        )
        else:
            # If vitals recover to normal (Tier 3), naturally clear mute
            if confirmed_tier == 3 and mute_state.is_muted:
                mute_state.is_muted = False
                mute_state.mute_duration_s = 0
                mute_state.mute_expires_at = None

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
            audio_muted=audio_muted,
            remaining_mute_s=remaining_mute_s,
            visual_escalation=visual_escalation,
        )

    # ----------------------------------------------------------------------
    # 4. Alarm Siren Mute Handling with Server-Side Clamping
    # ----------------------------------------------------------------------
    def _get_mute_state(self, bed_id: str) -> MuteState:
        if bed_id not in self.mute_states:
            self.mute_states[bed_id] = MuteState()
        return self.mute_states[bed_id]

    def get_mute_state(self, bed_id: str) -> MuteState:
        """Retrieve current mute state for a bed."""
        return self._get_mute_state(bed_id)

    def mute_alert(
        self,
        bed_id: str,
        duration_s: int = MAX_MUTE_DURATION_S,
        clinician_id: Optional[str] = None,
        ts: Optional[datetime] = None,
    ) -> MuteState:
        """Apply temporary siren silencing to a live alarm with deterministic server clamping.

        MUTE RULE (Option B):
        - Tier-1 audio sirens can be temporarily muted so bedside clinicians can conduct emergency
          care without auditory distress.
        - Hard-capped at 300 seconds (5 minutes) server-side; client inputs >300s are strictly clamped.
        - Visual escalation remains True (unsuppressable visual alert on dashboard).
        - Forced unmute occurs automatically once the clamped duration expires if condition persists.

        If configured with mute_policy == 'reject_tier1' (Option A), attempts to mute Tier-1 are rejected outright.

        Raises:
            PermissionError: If mute_policy is 'reject_tier1' and an attempt is made to mute Tier-1.
            ValueError: If there is no active alert on the bed to mute (i.e. confirmed tier is 3).
        """
        h_state = self._get_hysteresis_state(bed_id)
        if h_state.current_confirmed_tier == 3:
            raise ValueError(f"Cannot mute bed {bed_id}: no active alert (current tier is 3)")

        if h_state.current_confirmed_tier == 1 and self.mute_policy == "reject_tier1":
            raise PermissionError(
                f"Cannot mute bed {bed_id}: Tier-1 critical sirens cannot be muted by any role under reject_tier1 policy"
            )

        mute_ts = ts or datetime.now(timezone.utc)
        if mute_ts.tzinfo is None:
            mute_ts = mute_ts.replace(tzinfo=timezone.utc)

        # Enforce server-side hard ceiling: min(requested, 300)
        clamped_s = min(max(1, duration_s), MAX_MUTE_DURATION_S)
        expires_at = mute_ts + timedelta(seconds=clamped_s)

        mute_state = self._get_mute_state(bed_id)
        mute_state.is_muted = True
        mute_state.muted_at = mute_ts
        mute_state.mute_duration_s = clamped_s
        mute_state.mute_expires_at = expires_at
        mute_state.visual_escalation = (h_state.current_confirmed_tier == 1)
        mute_state.clinician_id = clinician_id

        logger.info(
            f"[triage] Bed {bed_id} siren muted for {clamped_s}s (requested {duration_s}s). "
            f"Expires at {expires_at.isoformat()}. Visual escalation: {mute_state.visual_escalation}"
        )
        return mute_state

    def unmute(self, bed_id: str) -> None:
        """Manually unmute alarm siren for a bed."""
        mute_state = self._get_mute_state(bed_id)
        mute_state.is_muted = False
        mute_state.mute_duration_s = 0
        mute_state.mute_expires_at = None
        logger.info(f"[triage] Bed {bed_id} siren unmuted manually")
