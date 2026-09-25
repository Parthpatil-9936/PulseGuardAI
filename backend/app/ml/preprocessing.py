"""Preprocessing and Feature Engineering for PulseGuard-AI ML Inference.

Enforces:
1. Strict biological bounds validation and clipping.
2. Canonical channel ordering: [0: HR, 1: SpO2, 2: BP_sys].
3. Min-max normalization scaled to [0.0, 1.0].
4. Generation of a deterministic SHA-256 fingerprint for Redis caching & DPDP audit logging.
"""

from __future__ import annotations

import hashlib
from typing import Dict, List, Optional, Tuple, Union
import numpy as np

# Canonical feature ordering & biological boundaries as trained in autoencoder_v1.pt
FEATURE_ORDER: List[str] = ["hr", "spo2", "bp_sys"]

MIN_BOUNDS: Dict[str, float] = {
    "hr": 0.0,
    "spo2": 0.0,
    "bp_sys": 0.0,
}

MAX_BOUNDS: Dict[str, float] = {
    "hr": 300.0,
    "spo2": 100.0,
    "bp_sys": 300.0,
}

WINDOW_SIZE: int = 100  # 10 seconds @ 10 Hz


def build_raw_array_from_samples(samples: List[Dict[str, float]]) -> np.ndarray:
    """Build a (3, 100) float32 numpy array from a list of sample dicts.

    If fewer than 100 samples are provided, repeats the oldest sample to left-pad
    so chronological ordering is preserved at the right (newest) end.
    """
    if not samples:
        raise ValueError("Cannot build raw array from empty sample list")

    n = len(samples)
    arr = np.zeros((3, WINDOW_SIZE), dtype=np.float32)

    # If samples exceed window size, take the latest 100
    selected_samples = samples[-WINDOW_SIZE:]
    k = len(selected_samples)
    pad_len = WINDOW_SIZE - k

    first_sample = selected_samples[0]
    first_hr = float(first_sample.get("hr", 75.0))
    first_spo2 = float(first_sample.get("spo2", 98.0))
    first_bp_sys = float(first_sample.get("bp_sys", 120.0))

    # Pad prefix
    for t in range(pad_len):
        arr[0, t] = first_hr
        arr[1, t] = first_spo2
        arr[2, t] = first_bp_sys

    # Fill suffix with actual chronological samples
    for idx, s in enumerate(selected_samples):
        col = pad_len + idx
        arr[0, col] = float(s.get("hr", 75.0))
        arr[1, col] = float(s.get("spo2", 98.0))
        arr[2, col] = float(s.get("bp_sys", 120.0))

    return arr


def scale_vitals_array(raw_arr: np.ndarray) -> np.ndarray:
    """Min-max scale raw biological array (3, 100) or (N, 3, 100) to [0.0, 1.0].

    scaled = clip((raw - min) / (max - min), 0.0, 1.0)
    """
    if raw_arr.ndim == 2:
        if raw_arr.shape != (3, WINDOW_SIZE):
            raise ValueError(f"Expected shape (3, {WINDOW_SIZE}), got {raw_arr.shape}")
        scaled = np.zeros_like(raw_arr, dtype=np.float32)
        for c, name in enumerate(FEATURE_ORDER):
            mn = MIN_BOUNDS[name]
            mx = MAX_BOUNDS[name]
            scaled[c, :] = (raw_arr[c, :] - mn) / (mx - mn)
        return np.clip(scaled, 0.0, 1.0)

    elif raw_arr.ndim == 3:
        if raw_arr.shape[1:] != (3, WINDOW_SIZE):
            raise ValueError(f"Expected shape (N, 3, {WINDOW_SIZE}), got {raw_arr.shape}")
        scaled = np.zeros_like(raw_arr, dtype=np.float32)
        for c, name in enumerate(FEATURE_ORDER):
            mn = MIN_BOUNDS[name]
            mx = MAX_BOUNDS[name]
            scaled[:, c, :] = (raw_arr[:, c, :] - mn) / (mx - mn)
        return np.clip(scaled, 0.0, 1.0)

    else:
        raise ValueError(f"Invalid array dimensions for scaling: {raw_arr.ndim}")


def compute_input_hash(raw_arr: np.ndarray, bed_id: str) -> str:
    """Computes a deterministic SHA-256 fingerprint for caching and DPDP audit trail.

    Contains bed_id and rounded vital values. Contains NO PII (no names, no MRNs).
    """
    # Round to 2 decimal places to ensure floating point stability across sessions
    rounded = np.round(raw_arr, 2).tobytes()
    hasher = hashlib.sha256()
    hasher.update(bed_id.encode("utf-8"))
    hasher.update(rounded)
    return hasher.hexdigest()


def preprocess_triage_input(
    bed_id: str,
    samples: Optional[List[Dict[str, float]]] = None,
    raw_window: Optional[List[List[float]]] = None,
    single_vitals: Optional[Dict[str, float]] = None,
) -> Tuple[np.ndarray, np.ndarray, str]:
    """Complete preprocessing pipeline for triage model inference.

    Validates inputs, formats them into standard biological window (3, 100),
    applies min-max scaling to [0.0, 1.0], and produces an input fingerprint hash.

    Returns:
        (raw_window_array: np.ndarray (3, 100),
         scaled_window_array: np.ndarray (3, 100),
         input_hash: str)
    """
    if raw_window is not None:
        raw_arr = np.array(raw_window, dtype=np.float32)
        if raw_arr.shape != (3, WINDOW_SIZE):
            raise ValueError(
                f"raw_window must be shaped (3, {WINDOW_SIZE}), got {raw_arr.shape}"
            )
    elif samples is not None and len(samples) > 0:
        raw_arr = build_raw_array_from_samples(samples)
    elif single_vitals is not None:
        # Broadcast single vital reading across entire 100-sample window
        hr = float(single_vitals.get("hr", 75.0))
        spo2 = float(single_vitals.get("spo2", 98.0))
        bp_sys = float(single_vitals.get("bp_sys", 120.0))
        raw_arr = np.zeros((3, WINDOW_SIZE), dtype=np.float32)
        raw_arr[0, :] = hr
        raw_arr[1, :] = spo2
        raw_arr[2, :] = bp_sys
    else:
        raise ValueError(
            "Must provide at least one of: 'samples', 'raw_window', or 'single_vitals'"
        )

    # Bounds check on raw array
    if np.any(np.isnan(raw_arr)) or np.any(np.isinf(raw_arr)):
        raise ValueError("Input vitals contain NaN or Inf values")

    # Min-max scale
    scaled_arr = scale_vitals_array(raw_arr)

    # Compute deterministic fingerprint
    inp_hash = compute_input_hash(raw_arr, bed_id)

    return raw_arr, scaled_arr, inp_hash
