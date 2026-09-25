#!/usr/bin/env python3
"""PulseGuard-AI synthetic 10-bed ICU telemetry generator.

Produces physiologically-COUPLED HR / SpO2 / BP_sys / BP_dia ticks at 10 Hz
per bed, matching the JSON ingestion contract of docs/context-spec.md
Section 3.1:

    {"bed_id": "bed-01", "ts": "...Z", "hr": 78, "spo2": 98,
     "bp_sys": 120, "bp_dia": 80, "ecg_lead_ok": true, "seq": 10452}

Design goals (why the vitals are coupled, not independent-random):
  * A later 1D-CNN autoencoder trains on healthy baseline telemetry. If the
    generator emitted four independent noise channels, the model could learn
    per-channel marginals and never notice cross-vital divergence. Here the
    channels share structure:
      - a per-bed "patient profile" (different resting HR/SpO2/BP, response
        gains, respiratory rate) so no two beds look alike,
      - a shared autonomic drive term that moves HR and BP together,
      - a baroreflex term (BP deviation above resting depresses HR),
      - respiratory sinus-arrhythmia: HR wobbles with the breathing cycle
        and SpO2 wobbles slightly in phase-lag with it,
      - pulse pressure ties BP_dia to BP_sys instead of floating freely,
      - AR(1)-shaped per-vital noise (correlated tick-to-tick, not white).
    This forces the autoencoder to learn the covariance, so "tachy with BP
    collapse" episodes actually light up the reconstruction error.

Modes:
  healthy : pure homeostatic baseline (training/calibration data).
  mixed   : healthy baseline + injected, LABELED anomaly episodes. Episode
            ground truth is written to manifest.json (the wire contract has
            no label field, by design - DPDP data minimisation).

CLI flags:
  --seed               Deterministic RNG seed (int). All per-bed RNGs are
                       derived from it, so runs are reproducible.
  --role               Metadata only (train|calib|val) recorded in
                       manifest.json. Generate several independently seeded
                       healthy + calibration datasets (--seed 41, 42, 43 ...)
                       so thresholds/autoencoders are validated against more
                       than one random realisation instead of being tuned to
                       a single synthetic run.
  --inject-disorder    Occasionally emits arrival jitter: a duplicated seq
                       (retransmission) or an out-of-order pair (tick s+1
                       arrives before tick s). The monitor-side counter stays
                       strictly monotonic per Section 3.1; jitter happens at
                       emission, exactly like a real lossy network.
  --degenerate-signal  Occasionally holds ONE vital perfectly flat (zero
                       variance) for a few seconds - a stuck sensor - to
                       exercise downstream epsilon / divide-by-zero guards.

Output:
  Default : JSONL file per bed under --outdir + manifest.json.
  --publish: streams the same JSON lines (newline-delimited) over UDP to
            --host/--port at real-time pace (aggregate 100 ticks/s for 10
            beds). UDP keeps the simulator dependency-free; MQTT/HTTP
            adapters live on the gateway side.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import socket
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

BED_COUNT = 10
TICK_HZ = 10
DT = 1.0 / TICK_HZ  # 100 ms

# Section 3.1 field constraints (hard clamps before serialization).
HR_RANGE = (0, 300)
SPO2_RANGE = (0, 100)
BP_SYS_RANGE = (0, 300)
BP_DIA_RANGE = (0, 200)

EPISODE_KINDS = (
    "hypoxia",
    "bradycardia",
    "tachy-divergent",
    "transient-spike",
    "drift",
    "tamper",
)

# Episode length range in tick indices (inclusive lo, exclusive hi cap).
EPISODE_LENGTH_IDX: Dict[str, Tuple[int, int]] = {
    "transient-spike": (int(0.8 * TICK_HZ), int(2.0 * TICK_HZ)),
    "tamper": (int(2.5 * TICK_HZ), int(5.0 * TICK_HZ)),
    "drift": (int(30 * TICK_HZ), int(75 * TICK_HZ)),
    "hypoxia": (int(30 * TICK_HZ), int(60 * TICK_HZ)),
    "bradycardia": (int(20 * TICK_HZ), int(45 * TICK_HZ)),
    "tachy-divergent": (int(20 * TICK_HZ), int(45 * TICK_HZ)),
}

ROLES = ("train", "calib", "val")


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def smoothstep(t: float) -> float:
    """S-curve easing on t in [0, 1]; avoids physiologically impossible steps."""
    t = clamp(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def iso_ms(dt: datetime) -> str:
    """ISO-8601 UTC with exactly millisecond precision (Section 3.1)."""
    return f"{dt:%Y-%m-%dT%H:%M:%S}.{dt.microsecond // 1000:03d}Z"


# --------------------------------------------------------------------------
# Per-bed patient profile - the anti-mode-collapse core (requirement 2)
# --------------------------------------------------------------------------


@dataclass
class PatientProfile:
    """Static physiology of one simulated patient.

    Every field is drawn per bed from the run seed, so bed-03 is a real
    *different* patient from bed-07 for the whole run: different resting
    vitals, different response gains, different baseline-wander periods and
    phases. Random float phases/frequencies mean the slow oscillations never
    repeat a fixed pattern, and an autoencoder cannot collapse to "always
    output the population-average shape".
    """

    bed_id: str
    resting_hr: float
    resting_spo2: float
    resting_bp_sys: float
    pulse_pressure: float
    resp_rate_bpm: float
    autonomic_gain: float   # how strongly shared drive moves HR
    bp_gain: float          # ... and how strongly it moves BP_sys
    baroreflex_gain: float  # negative HR response to BP deviation
    spo2_resp_amp: float
    hr_resp_amp: float
    noise_sigma: Dict[str, float]
    noise_phi: float
    wander: Dict[str, List[Tuple[float, float, float]]]  # vital -> [(amp, freq_hz, phase)]
    resp_phase: float

    @classmethod
    def generate(cls, rng: random.Random, bed_index: int) -> "PatientProfile":
        bed_id = f"bed-{bed_index + 1:02d}"

        def wander(amp: float, lo_hz: float, hi_hz: float) -> List[Tuple[float, float, float]]:
            # Two slow sinusoids per vital (0.02-0.12 Hz) with random periods
            # and phases -> aperiodic-looking baseline drift per patient.
            parts = []
            for _ in range(2):
                parts.append(
                    (
                        amp * rng.uniform(0.4, 1.0),
                        rng.uniform(lo_hz, hi_hz),
                        rng.uniform(0.0, 2.0 * math.pi),
                    )
                )
            return parts

        resting_bp_sys = rng.gauss(122, 12)
        return cls(
            bed_id=bed_id,
            resting_hr=clamp(rng.gauss(78, 11), 56, 96),
            resting_spo2=clamp(rng.gauss(97.2, 1.0), 94.0, 99.0),
            resting_bp_sys=clamp(resting_bp_sys, 100.0, 148.0),
            pulse_pressure=clamp(rng.gauss(44, 6), 32.0, 58.0),
            resp_rate_bpm=clamp(rng.gauss(14.5, 2.2), 10.0, 20.0),
            autonomic_gain=rng.uniform(0.35, 0.8),
            bp_gain=rng.uniform(0.6, 1.1),
            baroreflex_gain=rng.uniform(0.06, 0.13),
            spo2_resp_amp=rng.uniform(0.15, 0.45),
            hr_resp_amp=rng.uniform(1.2, 3.0),
            noise_sigma={
                "hr": rng.uniform(0.5, 0.75),
                "spo2": rng.uniform(0.16, 0.28),
                "bp_sys": rng.uniform(0.9, 1.3),
                "pp": rng.uniform(0.7, 1.1),
            },
            noise_phi=rng.uniform(0.86, 0.93),
            wander={
                "hr": wander(2.6, 0.02, 0.12),
                "spo2": wander(0.45, 0.02, 0.09),
                "bp_sys": wander(3.4, 0.02, 0.09),
                "pp": wander(1.6, 0.03, 0.11),
            },
            resp_phase=rng.uniform(0.0, 2.0 * math.pi),
        )

    def summary(self) -> Dict[str, object]:
        return {
            "bed_id": self.bed_id,
            "resting_hr_bpm": round(self.resting_hr, 1),
            "resting_spo2_pct": round(self.resting_spo2, 2),
            "resting_bp_sys_mmhg": round(self.resting_bp_sys, 1),
            "resting_bp_dia_mmhg": round(self.resting_bp_sys - self.pulse_pressure, 1),
            "resp_rate_bpm": round(self.resp_rate_bpm, 1),
            "baroreflex_gain": round(self.baroreflex_gain, 3),
        }


# --------------------------------------------------------------------------
# Labeled anomaly episodes (requirement 1)
# --------------------------------------------------------------------------


@dataclass
class Episode:
    """One labeled physiological disturbance on a single bed.

    ``offsets()`` returns additive deltas per vital plus flags. A smoothstep
    envelope ramps effects in/out so the waveform itself stays continuous
    (the *pathology* is the deviation, not a step function).
    """

    kind: str
    bed_id: str
    start_idx: int
    end_idx: int
    start_ts: str = ""
    end_ts: str = ""
    detail: Dict[str, object] = field(default_factory=dict)

    # -- envelope ----------------------------------------------------------
    def envelope(self, idx: int, attack_s: float, release_s: float) -> float:
        dur_idx = self.end_idx - self.start_idx
        pos = idx - self.start_idx
        if pos < 0 or pos >= dur_idx:
            return 0.0
        atk = max(1, int(attack_s * TICK_HZ))
        rel = max(1, int(release_s * TICK_HZ))
        rise = smoothstep(pos / atk)
        fall = smoothstep((dur_idx - pos) / rel)
        return min(rise, fall)

    # -- effect ------------------------------------------------------------
    def offsets(self, idx: int) -> Tuple[Dict[str, float], bool]:
        """Return ({vital: delta}, ecg_lead_ok) at tick index ``idx``."""
        t_rel = (idx - self.start_idx) / TICK_HZ
        d = self.detail
        if self.kind == "hypoxia":
            # Primary desaturation; HR compensates up, BP sags slightly.
            e = self.envelope(idx, attack_s=4.0, release_s=5.0)
            return (
                {
                    "spo2": -e * d["spo2_drop"],
                    "hr": e * d["hr_rise"],
                    "bp_sys": -e * d["bp_sag"],
                },
                True,
            )
        if self.kind == "bradycardia":
            # HR falls with BP following down (coupled, not independent).
            e = self.envelope(idx, attack_s=3.0, release_s=4.0)
            return (
                {
                    "hr": -e * d["hr_drop"],
                    "bp_sys": -e * d["bp_drop"],
                    "spo2": -e * d["spo2_dip"],
                },
                True,
            )
        if self.kind == "tachy-divergent":
            # The Tier-2 signature: HR climbs while BP collapses (divergence
            # that only a covariance-aware model can catch).
            e = self.envelope(idx, attack_s=5.0, release_s=6.0)
            return (
                {
                    "hr": e * d["hr_rise"],
                    "bp_sys": -e * d["bp_fall"],
                    "bp_dia": -e * d["bp_fall"] * 0.55,
                    "spo2": -e * d["spo2_drift"],
                },
                True,
            )
        if self.kind == "transient-spike":
            # 1-2 s single-vital spike on a *stable* rest of the ward:
            # the canonical Tier-3 noise-suppression pattern.
            e = self.envelope(idx, attack_s=0.15, release_s=0.3)
            return ({str(d["vital"]): e * float(d["amplitude"])}, True)
        if self.kind == "drift":
            # Slow low-frequency wander of one channel (drying electrode /
            # sweat). Ramp only; no release inside the episode.
            pos = idx - self.start_idx
            dur = max(1, self.end_idx - self.start_idx)
            return ({str(d["vital"]): float(d["amplitude"]) * (pos / dur)}, True)
        if self.kind == "tamper":
            # Loose lead: ecg_lead_ok flips false, HR flatlines ~1 s (frozen
            # at its last live value, see is_frozen) then slams to
            # open-circuit artifact values with dropouts.
            if t_rel < float(d["flat_s"]):
                return ({}, False)
            phase = int((t_rel - float(d["flat_s"])) * 2) % 3
            artifact = {0: float(d["open_circuit"]), 1: float(d["open_circuit"]) * 0.6,
                        2: -60.0}[phase]
            return ({"hr": artifact}, False)
        raise ValueError(f"unknown episode kind: {self.kind}")

    def is_frozen(self, vital: str, idx: int) -> bool:
        """Tamper keeps HR *perfectly* flat before the artifact slams."""
        if self.kind != "tamper" or vital != "hr":
            return False
        return (idx - self.start_idx) < float(self.detail["flat_s"]) * TICK_HZ

    def manifest_entry(self) -> Dict[str, object]:
        return {
            "kind": self.kind,
            "bed_id": self.bed_id,
            "start_ts": self.start_ts,
            "end_ts": self.end_ts,
            "start_idx": self.start_idx,
            "end_idx": self.end_idx,
            "detail": {
                k: (round(v, 2) if isinstance(v, (int, float)) and not isinstance(v, bool) else v)
                for k, v in self.detail.items()
            },
        }


def _build_episode(kind: str, rng: random.Random, profile: PatientProfile,
                   start_idx: int, end_idx: int) -> Episode:
    """Parameterise one episode with severities drawn per-instance."""
    ep = Episode(kind=kind, bed_id=profile.bed_id, start_idx=start_idx, end_idx=end_idx)
    if kind == "hypoxia":
        severe = rng.random() < 0.35
        drop = rng.uniform(13.0, 17.0) if severe else rng.uniform(6.0, 12.0)
        ep.detail = {
            "spo2_drop": drop,
            "hr_rise": rng.uniform(8.0, 22.0),
            "bp_sag": rng.uniform(4.0, 12.0),
            "severe": 1.0 if severe else 0.0,  # severe can breach SpO2<85 (Tier 1)
        }
    elif kind == "bradycardia":
        ep.detail = {
            "hr_drop": rng.uniform(28.0, 42.0),  # HR -> mid-30s/40s
            "bp_drop": rng.uniform(8.0, 18.0),
            "spo2_dip": rng.uniform(0.5, 2.0),
        }
    elif kind == "tachy-divergent":
        ep.detail = {
            "hr_rise": rng.uniform(45.0, 70.0),   # HR -> 125-165
            "bp_fall": rng.uniform(18.0, 35.0),   # BP_sys collapses
            "spo2_drift": rng.uniform(1.5, 4.0),
        }
    elif kind == "transient-spike":
        vital = rng.choice(("hr", "bp_sys"))
        ep.detail = {
            "vital": vital,
            "amplitude": rng.uniform(35.0, 60.0) if vital == "hr" else rng.uniform(25.0, 45.0),
        }
    elif kind == "drift":
        vital = rng.choice(("bp_sys", "spo2", "hr"))
        ep.detail = {
            "vital": vital,
            "amplitude": rng.uniform(0.6, 1.6) if vital == "spo2"
            else rng.uniform(6.0, 14.0) if vital == "bp_sys"
            else rng.uniform(5.0, 11.0),
        }
    elif kind == "tamper":
        ep.detail = {
            "flat_s": rng.uniform(0.8, 1.4),
            "open_circuit": rng.uniform(210.0, 285.0),
        }
    return ep


def schedule_episodes(rng: random.Random, profiles: Sequence[PatientProfile],
                      ticks_per_bed: int, episode_rate_per_min: float,
                      base_ts: datetime) -> List[Episode]:
    """Spread non-overlapping labeled episodes across beds and time.

    Kinds are assigned round-robin over shuffled slots so every episode kind
    appears at least once whenever >=6 episodes are scheduled (the acceptance
    test needs, e.g., a hypoxia Tier-1 injection to exist in the dataset).
    """
    episodes: List[Episode] = []
    per_bed = max(1, int(round(episode_rate_per_min * (ticks_per_bed / TICK_HZ) / 60.0)))
    slots = [(p, i) for p in profiles for i in range(per_bed)]
    rng.shuffle(slots)
    kind_cycle = list(EPISODE_KINDS)
    rng.shuffle(kind_cycle)

    min_start = min(int(15 * TICK_HZ), max(0, ticks_per_bed - int(10 * TICK_HZ)))
    placed_by_bed: Dict[str, List[Tuple[int, int]]] = {p.bed_id: [] for p in profiles}
    for n, (profile, _i) in enumerate(slots):
        kind = kind_cycle[n % len(kind_cycle)]
        placed = placed_by_bed[profile.bed_id]
        for _attempt in range(12):
            lo, hi = EPISODE_LENGTH_IDX[kind]
            max_len = max(int(2 * TICK_HZ), ticks_per_bed - int(5 * TICK_HZ))
            length = rng.randint(min(lo, max_len), min(hi, max_len))
            max_start = max(min_start, ticks_per_bed - length - int(2 * TICK_HZ))
            if max_start < min_start:
                start = min_start
            else:
                start = rng.randint(min_start, max_start)
            end = start + length
            if end <= ticks_per_bed and all(end < s or start > e for s, e in placed):
                placed.append((start, end))
                ep = _build_episode(kind, rng, profile, start, end)
                ep.start_ts = iso_ms(base_ts + timedelta(seconds=start * DT))
                ep.end_ts = iso_ms(base_ts + timedelta(seconds=end * DT))
                episodes.append(ep)
                break
    episodes.sort(key=lambda e: (e.start_idx, e.bed_id))
    return episodes


# --------------------------------------------------------------------------
# Degenerate (stuck-sensor) flatline events (requirement 5)
# --------------------------------------------------------------------------


@dataclass
class FlatlineEvent:
    bed_id: str
    vital: str
    start_idx: int
    end_idx: int
    frozen_value: int

    def active(self, idx: int) -> bool:
        return self.start_idx <= idx < self.end_idx


def schedule_flatlines(rng: random.Random, profiles: Sequence[PatientProfile],
                       ticks_per_bed: int, base_ts: datetime) -> List[FlatlineEvent]:
    """Occasionally hold one vital perfectly flat for a few seconds."""
    events: List[FlatlineEvent] = []
    expected = max(1, int(round((ticks_per_bed / TICK_HZ) / 180.0)))
    for profile in profiles:
        for _ in range(expected):
            if rng.random() > 0.6:
                continue
            length = rng.randint(int(2.0 * TICK_HZ), int(4.0 * TICK_HZ))
            min_start = min(int(10 * TICK_HZ), max(0, ticks_per_bed - length - 1))
            max_start = max(min_start, ticks_per_bed - length - 1)
            start = rng.randint(min_start, max_start)
            vital = rng.choice(("hr", "spo2", "bp_sys", "bp_dia"))
            base_val = {
                "hr": profile.resting_hr,
                "spo2": profile.resting_spo2,
                "bp_sys": profile.resting_bp_sys,
                "bp_dia": profile.resting_bp_sys - profile.pulse_pressure,
            }[vital]
            events.append(
                FlatlineEvent(
                    bed_id=profile.bed_id,
                    vital=vital,
                    start_idx=start,
                    end_idx=start + length,
                    frozen_value=int(round(base_val)),
                )
            )
    events.sort(key=lambda f: (f.start_idx, f.bed_id))
    return events


# --------------------------------------------------------------------------
# Bed physiology engine
# --------------------------------------------------------------------------


class BedSimulator:
    """Steps one bed's coupled vitals forward at 10 Hz.

    State carries over tick-to-tick (AR noise, smoothed baroreflex, episode
    freeze), so the waveform is a continuous process, not iid samples.
    """

    def __init__(self, profile: PatientProfile, rng: random.Random,
                 episodes: Sequence[Episode], flatlines: Sequence[FlatlineEvent]):
        self.profile = profile
        self.rng = rng
        self.episodes = episodes
        self.flatlines = sorted(flatlines, key=lambda f: f.start_idx)
        self.seq = rng.randrange(1_000, 9_999)  # monitor was already running
        self.t = 0.0
        # AR(1) noise states + shared autonomic drive + smoothed BP deviation.
        self.ar = {k: 0.0 for k in profile.noise_sigma}
        self.drive = 0.0
        self.bp_dev_smooth = 0.0
        self.episode_cursor = 0
        self.sorted_eps = sorted(episodes, key=lambda e: e.start_idx)
        self.last_hr = profile.resting_hr  # for tamper flatline freeze

    # -- helpers -----------------------------------------------------------
    def _wander(self, vital: str) -> float:
        total = 0.0
        for amp, freq, phase in self.profile.wander[vital]:
            total += amp * math.sin(2.0 * math.pi * freq * self.t + phase)
        return total

    def _active_episode(self, idx: int) -> Optional[Episode]:
        # Episodes are sorted and non-overlapping per bed: advance cursor.
        while (self.episode_cursor < len(self.sorted_eps)
               and idx >= self.sorted_eps[self.episode_cursor].end_idx):
            self.episode_cursor += 1
        ep = (self.sorted_eps[self.episode_cursor]
              if self.episode_cursor < len(self.sorted_eps) else None)
        if ep is not None and ep.start_idx <= idx < ep.end_idx:
            return ep
        return None

    def _frozen_value(self, idx: int) -> Optional[Tuple[str, int]]:
        for ev in self.flatlines:
            if ev.active(idx):
                return ev.vital, ev.frozen_value
            if ev.start_idx > idx:
                break
        return None

    # -- one tick ----------------------------------------------------------
    def step(self, base_ts: datetime, idx: int) -> Dict[str, object]:
        p = self.profile
        self.t = idx * DT

        # Shared autonomic drive: AR(1); HR and BP_sys both read it, so they
        # co-wander. This is the core cross-vital coupling.
        self.drive = 0.92 * self.drive + self.rng.gauss(0.0, 0.45)

        # Respiratory cycle: drives HR (sinus arrhythmia) and SpO2 (lagged).
        w_resp = 2.0 * math.pi * (p.resp_rate_bpm / 60.0) * self.t + p.resp_phase
        hr_resp = p.hr_resp_amp * math.sin(w_resp)
        spo2_resp = p.spo2_resp_amp * math.sin(w_resp - 0.4)

        # AR(1) per-vital measurement noise (correlated, not white).
        for k, sigma in p.noise_sigma.items():
            self.ar[k] = p.noise_phi * self.ar[k] + self.rng.gauss(0.0, sigma)

        # Raw (pre-reflex) BP_sys deviation drives the baroreflex.
        raw_bps = (p.resting_bp_sys + self._wander("bp_sys")
                   + p.bp_gain * self.drive + self.ar["bp_sys"])
        bp_dev = raw_bps - p.resting_bp_sys
        self.bp_dev_smooth += 0.025 * (bp_dev - self.bp_dev_smooth)  # ~2 s lag
        baro = -p.baroreflex_gain * self.bp_dev_smooth * 10.0

        hr = (p.resting_hr + self._wander("hr") + p.autonomic_gain * self.drive
              + hr_resp + baro + self.ar["hr"])
        spo2 = (p.resting_spo2 + self._wander("spo2") + 0.10 * self.drive
                + spo2_resp + self.ar["spo2"])
        bps = raw_bps
        pulse_pressure = (p.pulse_pressure + self._wander("pp") + self.ar["pp"])

        values = {"hr": hr, "spo2": spo2, "bp_sys": bps, "bp_dia": bps - pulse_pressure}

        # Labeled episode overlay.
        ecg_lead_ok = True
        ep = self._active_episode(idx)
        if ep is not None:
            offsets, lead_ok = ep.offsets(idx)
            for vital, delta in offsets.items():
                values[vital] = values.get(vital, 0.0) + delta
            ecg_lead_ok = lead_ok
            if ep.is_frozen("hr", idx):
                values["hr"] = self.last_hr
            else:
                self.last_hr = values["hr"]
        else:
            self.last_hr = values["hr"]

        # Flatline (stuck sensor) overlay wins on its channel: zero variance.
        frozen = self._frozen_value(idx)
        if frozen is not None:
            vital, fval = frozen
            values[vital] = float(fval)

        # Serialize to the Section 3.1 contract: integers + bounds clamps.
        tick = {
            "bed_id": p.bed_id,
            "ts": iso_ms(base_ts + timedelta(seconds=idx * DT)),
            "hr": int(round(clamp(values["hr"], *HR_RANGE))),
            "spo2": int(round(clamp(values["spo2"], *SPO2_RANGE))),
            "bp_sys": int(round(clamp(values["bp_sys"], *BP_SYS_RANGE))),
            "bp_dia": int(round(clamp(max(values["bp_dia"], 15.0), *BP_DIA_RANGE))),
            "ecg_lead_ok": ecg_lead_ok,
            "seq": self.seq,
        }
        self.seq += 1
        return tick


# --------------------------------------------------------------------------
# Arrival-order jitter (requirement 4)
# --------------------------------------------------------------------------


class JitterStream:
    """Wraps a bed's tick sequence with real-world arrival jitter.

    The monitor-side counter stays strictly monotonic (Section 3.1); what
    jitters is *emission*: sometimes tick s+1 is emitted before tick s
    (out-of-order pair), sometimes the same tick is emitted twice with the
    same seq (retransmission duplicate).
    """

    def __init__(self, bed: BedSimulator, rng: random.Random,
                 p_ooo: float = 0.0005, p_dup: float = 0.0008):
        self.bed = bed
        self.rng = rng
        self.p_ooo = p_ooo
        self.p_dup = p_dup
        self.queue: List[Dict[str, object]] = []
        self.ooo_events = 0
        self.dup_events = 0
        self._last_swapped = False

    def next_ticks(self, base_ts: datetime, idx: int) -> List[Dict[str, object]]:
        while len(self.queue) < 2:
            self.queue.append(self.bed.step(base_ts, idx if not self.queue else idx + 1))
        if not self._last_swapped and self.rng.random() < self.p_ooo:
            self.queue.reverse()  # emit later seq first, then the held one
            self.ooo_events += 1
            self._last_swapped = True
        else:
            self._last_swapped = False
        out = [self.queue.pop(0)]
        if self.rng.random() < self.p_dup:
            out.append(dict(out[0]))  # duplicate seq = retransmission
            self.dup_events += 1
        return out


# --------------------------------------------------------------------------
# Dataset generation (requirement 3: multi-realisation seeds)
# --------------------------------------------------------------------------


@dataclass
class GeneratorConfig:
    mode: str = "healthy"          # "healthy" | "mixed"
    seed: int = 42
    duration_s: float = 120.0
    beds: int = BED_COUNT
    outdir: Path = Path("simulator/out")
    role: str = "train"
    publish: bool = False
    host: str = "127.0.0.1"
    port: int = 9500
    inject_disorder: bool = False
    degenerate_signal: bool = False
    episode_rate: float = 0.25     # episodes per bed per minute (mixed mode)


def build_beds(cfg: GeneratorConfig, ticks_per_bed: int,
               base_ts: datetime) -> Tuple[List[BedSimulator], List[Episode],
                                           List[FlatlineEvent], random.Random]:
    """Derive all RNGs from the single --seed so runs are reproducible."""
    master = random.Random(cfg.seed)
    bed_rngs = [random.Random(master.getrandbits(64)) for _ in range(cfg.beds)]
    profiles = [PatientProfile.generate(r, i) for i, r in enumerate(bed_rngs)]

    episodes: List[Episode] = []
    flatlines: List[FlatlineEvent] = []
    if cfg.mode == "mixed":
        ep_rng = random.Random(master.getrandbits(64))
        episodes = schedule_episodes(ep_rng, profiles, ticks_per_bed,
                                     cfg.episode_rate, base_ts)
    if cfg.degenerate_signal:
        flat_rng = random.Random(master.getrandbits(64))
        flatlines = schedule_flatlines(flat_rng, profiles, ticks_per_bed, base_ts)

    beds = [
        BedSimulator(profile, rng, [e for e in episodes if e.bed_id == profile.bed_id],
                     [f for f in flatlines if f.bed_id == profile.bed_id])
        for profile, rng in zip(profiles, bed_rngs)
    ]
    return beds, episodes, flatlines, master


def generate_file_dataset(cfg: GeneratorConfig) -> None:
    """Write per-bed JSONL files + manifest.json (the labeled ground truth)."""
    outdir = cfg.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    ticks_per_bed = int(cfg.duration_s * TICK_HZ)
    base_ts = datetime.now(timezone.utc)

    beds, episodes, flatlines, master = build_beds(cfg, ticks_per_bed, base_ts)
    jitter_rngs = [random.Random(master.getrandbits(64)) for _ in beds]
    streams = (
        [JitterStream(b, r) for b, r in zip(beds, jitter_rngs)]
        if cfg.inject_disorder else
        [JitterStream(b, r, p_ooo=0.0, p_dup=0.0) for b, r in zip(beds, jitter_rngs)]
    )

    file_handles = []
    file_meta = []
    counts = [0] * len(beds)
    try:
        for i, bed in enumerate(beds):
            path = outdir / f"{bed.profile.bed_id}.jsonl"
            fh = open(path, "w", encoding="utf-8")
            file_handles.append(fh)
            file_meta.append(path)

        # Round-robin across beds, 10 ticks/s per bed = 100 ticks/s aggregate.
        for idx in range(ticks_per_bed):
            for i, stream in enumerate(streams):
                for tick in stream.next_ticks(base_ts, idx):
                    file_handles[i].write(json.dumps(tick, separators=(",", ":")) + "\n")
                    counts[i] += 1

        # Flush any remaining ticks buffered in JitterStream queues.
        for i, stream in enumerate(streams):
            while stream.queue:
                tick = stream.queue.pop(0)
                file_handles[i].write(json.dumps(tick, separators=(",", ":")) + "\n")
                counts[i] += 1
    finally:
        for fh in file_handles:
            fh.close()

    ooo = sum(s.ooo_events for s in streams)
    dups = sum(s.dup_events for s in streams)
    manifest = {
        "schema_version": "1.0",
        "generator": "simulator/generator.py",
        "mode": cfg.mode,
        "role": cfg.role,
        "seed": cfg.seed,
        "duration_s": cfg.duration_s,
        "tick_hz": TICK_HZ,
        "beds": cfg.beds,
        "contract": "context-spec.md Section 3.1",
        "flags": {
            "inject_disorder": cfg.inject_disorder,
            "degenerate_signal": cfg.degenerate_signal,
        },
        "counts": {
            "ticks_total": sum(counts),
            "ticks_per_bed_min": min(counts),
            "out_of_order_events": ooo,
            "duplicate_seq_events": dups,
            "flatline_events": len(flatlines),
            "episodes": len(episodes),
        },
        "patients": [p.summary() for p in (b.profile for b in beds)],
        "episodes": [e.manifest_entry() for e in episodes],
        "flatlines": [
            {
                "bed_id": f.bed_id,
                "vital": f.vital,
                "start_ts": iso_ms(base_ts + timedelta(seconds=f.start_idx * DT)),
                "end_ts": iso_ms(base_ts + timedelta(seconds=f.end_idx * DT)),
                "frozen_value": f.frozen_value,
            }
            for f in flatlines
        ],
        "files": [
            {"bed_id": bed.profile.bed_id, "path": str(path), "ticks": counts[i]}
            for i, (bed, path) in enumerate(zip(beds, file_meta))
        ],
    }
    manifest_path = outdir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(
        f"[generator] mode={cfg.mode} role={cfg.role} seed={cfg.seed} "
        f"beds={cfg.beds} duration={cfg.duration_s:g}s -> {outdir}"
    )
    print(f"[generator] ticks={sum(counts)} episodes={len(episodes)} "
          f"flatlines={len(flatlines)} ooo={ooo} dups={dups} manifest={manifest_path}")


def publish_stream(cfg: GeneratorConfig) -> None:
    """Stream ticks over UDP in real time (Ctrl+C to stop).

    duration_s <= 0 streams until interrupted. JSON lines, one tick per
    datagram, aggregate 100 ticks/s for 10 beds.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ticks_per_bed = int(cfg.duration_s * TICK_HZ) if cfg.duration_s > 0 else None
    base_ts = datetime.now(timezone.utc)
    beds, episodes, flatlines, master = build_beds(
        cfg, ticks_per_bed or int(3600 * TICK_HZ), base_ts
    )
    jitter_rngs = [random.Random(master.getrandbits(64)) for _ in beds]
    streams = (
        [JitterStream(b, r) for b, r in zip(beds, jitter_rngs)]
        if cfg.inject_disorder else
        [JitterStream(b, r, p_ooo=0.0, p_dup=0.0) for b, r in zip(beds, jitter_rngs)]
    )

    print(f"[generator] publishing UDP -> {cfg.host}:{cfg.port} "
          f"mode={cfg.mode} seed={cfg.seed} "
          f"({'infinite' if ticks_per_bed is None else f'{cfg.duration_s:g}s'})")
    addr = (cfg.host, cfg.port)
    interval = DT
    next_t = time.perf_counter()
    idx = 0
    sent = 0
    try:
        while ticks_per_bed is None or idx < ticks_per_bed:
            for stream in streams:
                for tick in stream.next_ticks(base_ts, idx):
                    sock.sendto(
                        (json.dumps(tick, separators=(",", ":")) + "\n").encode("utf-8"),
                        addr,
                    )
                    sent += 1
            idx += 1
            next_t += interval
            delay = next_t - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
            else:
                next_t = time.perf_counter()  # fell behind; skip catch-up
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()
        print(f"[generator] stopped; sent {sent} ticks, "
              f"episodes={len(episodes)} flatlines={len(flatlines)}")


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="PulseGuard-AI synthetic 10-bed ICU telemetry generator "
                    "(Section 3.1 contract, physiologically coupled vitals).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("--mode", choices=("healthy", "mixed"), default="healthy",
                    help="healthy = pure baseline; mixed = baseline + labeled episodes")
    ap.add_argument("--seed", type=int, default=42,
                    help="master RNG seed; vary it to get independent realizations")
    ap.add_argument("--role", choices=ROLES, default="train",
                    help="dataset role recorded in manifest.json (metadata only)")
    ap.add_argument("--duration", type=float, default=120.0,
                    help="seconds of telemetry per bed (<=0 with --publish = infinite)")
    ap.add_argument("--beds", type=int, default=BED_COUNT)
    ap.add_argument("--outdir", type=Path, default=Path("simulator/out"),
                    help="output directory for JSONL + manifest.json")
    ap.add_argument("--publish", action="store_true",
                    help="stream over UDP instead of writing files")
    ap.add_argument("--host", default="127.0.0.1", help="UDP publish host")
    ap.add_argument("--port", type=int, default=9500, help="UDP publish port")
    ap.add_argument("--episode-rate", type=float, default=0.25,
                    help="mixed mode: episodes per bed per minute")
    ap.add_argument("--inject-disorder", action="store_true",
                    help="emit occasional out-of-order pairs and duplicate seqs")
    ap.add_argument("--degenerate-signal", action="store_true",
                    help="occasionally hold one vital perfectly flat (zero variance) "
                         "for a few seconds")
    return ap


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if not 1 <= args.beds <= 64:
        print("error: --beds must be in [1, 64]", file=sys.stderr)
        return 2
    cfg = GeneratorConfig(
        mode=args.mode,
        seed=args.seed,
        duration_s=args.duration,
        beds=args.beds,
        outdir=args.outdir,
        role=args.role,
        publish=args.publish,
        host=args.host,
        port=args.port,
        inject_disorder=args.inject_disorder,
        degenerate_signal=args.degenerate_signal,
        episode_rate=args.episode_rate,
    )
    if cfg.publish:
        publish_stream(cfg)
    else:
        generate_file_dataset(cfg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
