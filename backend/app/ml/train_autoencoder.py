"""Training & Calibration Script for PulseGuard-AI 1D-CNN Telemetry Autoencoder.

Implements required behaviors:
1. Multi-seed healthy dataset training (combines seeds 41, 42, 43 to avoid mode collapse).
2. Per-channel reconstruction error (separate MSE for HR, SpO2, BP_sys).
3. Mode-collapse sanity check (evaluates error variance across 10 healthy + 10 anomaly windows).
4. Averaged multi-realization calibration constants (offset/scale computed per seed & averaged).
5. Saves model checkpoint to autoencoder_v1.pt.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

from backend.app.ml.autoencoder import (
    CHANNEL_NAMES,
    MAX_BOUNDS,
    MIN_BOUNDS,
    TelemetryAutoencoder,
    compute_per_channel_mse,
    scale_raw_window,
)
from simulator.generator import GeneratorConfig, generate_file_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_SEEDS = [41, 42, 43]
WINDOW_SIZE = 100
STRIDE = 10


def ensure_healthy_dataset(seed: int, duration_s: float = 300.0, base_dir: Path = Path("simulator/out")) -> Path:
    """Ensure synthetic healthy dataset for a given seed exists, generating if needed."""
    outdir = base_dir / f"healthy-{seed}"
    if not (outdir / "manifest.json").exists():
        logger.info(f"Generating healthy dataset for seed {seed} at {outdir}...")
        cfg = GeneratorConfig(
            mode="healthy",
            seed=seed,
            duration_s=duration_s,
            beds=10,
            outdir=outdir,
            role="train",
        )
        generate_file_dataset(cfg)
    return outdir


def ensure_mixed_dataset(seed: int = 99, duration_s: float = 120.0, base_dir: Path = Path("simulator/out")) -> Path:
    """Ensure synthetic mixed anomaly dataset for mode-collapse check exists."""
    outdir = base_dir / f"mixed-{seed}"
    if not (outdir / "manifest.json").exists():
        logger.info(f"Generating mixed anomaly dataset for mode collapse check at {outdir}...")
        cfg = GeneratorConfig(
            mode="mixed",
            seed=seed,
            duration_s=duration_s,
            beds=10,
            outdir=outdir,
            role="val",
            inject_disorder=True,
            degenerate_signal=True,
        )
        generate_file_dataset(cfg)
    return outdir


def load_windows_from_directory(dataset_dir: Path) -> np.ndarray:
    """Load jsonl telemetry files from directory and extract (N, 3, 100) raw windows."""
    windows_list = []
    jsonl_files = sorted(list(dataset_dir.glob("bed-*.jsonl")))

    for path in jsonl_files:
        hr_series, spo2_series, bp_sys_series = [], [], []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                tick = json.loads(line)
                hr_series.append(float(tick["hr"]))
                spo2_series.append(float(tick["spo2"]))
                bp_sys_series.append(float(tick["bp_sys"]))

        n_ticks = len(hr_series)
        for start_idx in range(0, n_ticks - WINDOW_SIZE + 1, STRIDE):
            end_idx = start_idx + WINDOW_SIZE
            win = np.array(
                [
                    hr_series[start_idx:end_idx],
                    spo2_series[start_idx:end_idx],
                    bp_sys_series[start_idx:end_idx],
                ],
                dtype=np.float32,
            )
            windows_list.append(win)

    if not windows_list:
        raise ValueError(f"No valid telemetry windows extracted from {dataset_dir}")

    raw_windows = np.stack(windows_list, axis=0)  # (N, 3, 100)
    return raw_windows


def train_autoencoder(
    seeds: List[int] = DEFAULT_SEEDS,
    epochs: int = 15,
    batch_size: int = 64,
    lr: float = 1e-3,
    output_checkpoint: Path = Path("backend/app/ml/autoencoder_v1.pt"),
) -> None:
    """Full training, calibration, and mode-collapse verification workflow."""
    logger.info("==================================================================")
    logger.info("PulseGuard-AI Autoencoder Training & Multi-Seed Calibration")
    logger.info("==================================================================")

    # 1. Load multi-seed healthy datasets
    seed_windows: Dict[int, np.ndarray] = {}
    all_scaled_windows = []

    for seed in seeds:
        wdir = ensure_healthy_dataset(seed)
        raw_win = load_windows_from_directory(wdir)
        scaled_win = scale_raw_window(raw_win)
        seed_windows[seed] = scaled_win
        all_scaled_windows.append(scaled_win)
        logger.info(f"Loaded seed {seed} healthy dataset: {scaled_win.shape[0]} windows")

    train_data_np = np.concatenate(all_scaled_windows, axis=0)
    logger.info(f"Combined Multi-Seed Training Set Shape: {train_data_np.shape}")

    train_tensor = torch.from_numpy(train_data_np)
    dataset = TensorDataset(train_tensor, train_tensor)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # Instantiate model & optimizer
    model = TelemetryAutoencoder(in_channels=3, latent_dim=16)
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    criterion = nn.MSELoss()

    model.train()
    for epoch in range(1, epochs + 1):
        running_loss = 0.0
        for x_batch, _ in loader:
            optimizer.zero_grad()
            recon = model(x_batch)
            loss = criterion(recon, x_batch)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * x_batch.size(0)

        epoch_loss = running_loss / len(train_tensor)
        if epoch % 3 == 0 or epoch == epochs:
            logger.info(f"Epoch [{epoch:02d}/{epochs:02d}] Loss: {epoch_loss:.6f}")

    model.eval()

    # 2. Compute Reconstruction Error PER CHANNEL
    logger.info("\n--- 2. Per-Channel Reconstruction Error Evaluation ---")
    with torch.no_grad():
        all_recon = model(train_tensor)
        # Compute per-channel MSE: (N, 3) where columns are [hr, spo2, bp_sys]
        per_channel_mse = compute_per_channel_mse(train_tensor, all_recon).numpy()

    mean_per_channel = per_channel_mse.mean(axis=0)
    for idx, cname in enumerate(CHANNEL_NAMES):
        logger.info(f"Mean {cname.upper()} MSE: {mean_per_channel[idx]:.6f}")

    # 3. Mode-Collapse Sanity Check
    logger.info("\n--- 3. Mode-Collapse Sanity Check ---")
    healthy_dir = ensure_healthy_dataset(seeds[0])
    mixed_dir = ensure_mixed_dataset(99)

    healthy_wins = load_windows_from_directory(healthy_dir)
    mixed_wins = load_windows_from_directory(mixed_dir)

    rng = np.random.RandomState(42)
    h_sample = healthy_wins[rng.choice(len(healthy_wins), 10, replace=False)]
    m_sample = mixed_wins[rng.choice(len(mixed_wins), 10, replace=False)]

    eval_sample_raw = np.concatenate([h_sample, m_sample], axis=0)  # (20, 3, 100)
    eval_sample_scaled = scale_raw_window(eval_sample_raw)

    eval_tensor = torch.from_numpy(eval_sample_scaled)
    with torch.no_grad():
        eval_recon = model(eval_tensor)
        eval_channel_mse = compute_per_channel_mse(eval_tensor, eval_recon).numpy()

    variance_per_channel = np.var(eval_channel_mse, axis=0)
    logger.info("Per-channel reconstruction error variance across 20 test examples (10 healthy + 10 anomaly):")
    for idx, cname in enumerate(CHANNEL_NAMES):
        logger.info(f"  {cname.upper()} Error Variance: {variance_per_channel[idx]:.8f}")

    if np.any(variance_per_channel < 1e-6):
        logger.warning(
            "[WARNING] Mode collapse detected! Reconstruction error variance across inputs is near-zero (< 1e-6). "
            "Model outputs look identical regardless of input shape. Increase healthy training variation!"
        )
    else:
        logger.info("[SUCCESS] Mode-collapse sanity check passed. Error variance across inputs is healthy.")

    # 4. Calibrate Normalization Constants (offset/scale) SEPARATELY per seed
    logger.info("\n--- 4. Multi-Realization Calibration (Offset & Scale) ---")
    seed_offsets: List[Dict[str, float]] = []
    seed_scales: List[Dict[str, float]] = []

    for seed in seeds:
        swin_scaled = seed_windows[seed]
        stensor = torch.from_numpy(swin_scaled)
        with torch.no_grad():
            srecon = model(stensor)
            smse = compute_per_channel_mse(stensor, srecon).numpy()

        # Compute 5th and 95th percentiles per channel
        p5 = np.percentile(smse, 5, axis=0)
        p95 = np.percentile(smse, 95, axis=0)

        offset_seed = {cname: float(p5[idx]) for idx, cname in enumerate(CHANNEL_NAMES)}
        scale_seed = {
            cname: float(max(1e-5, p95[idx] - p5[idx])) for idx, cname in enumerate(CHANNEL_NAMES)
        }

        seed_offsets.append(offset_seed)
        seed_scales.append(scale_seed)
        logger.info(f"Seed {seed} Calibration:")
        logger.info(f"  Offset (P5):  {offset_seed}")
        logger.info(f"  Scale (P95-P5): {scale_seed}")

    # Average calibration constants across seeded realizations
    final_offset = {
        cname: float(np.mean([so[cname] for so in seed_offsets]))
        for cname in CHANNEL_NAMES
    }
    final_scale = {
        cname: float(np.mean([ss[cname] for ss in seed_scales]))
        for cname in CHANNEL_NAMES
    }

    logger.info("\nFinal Averaged Multi-Seed Calibration Constants:")
    logger.info(f"  Final Offset: {final_offset}")
    logger.info(f"  Final Scale:  {final_scale}")

    # 5. Save Checkpoint (.pt format) and Calibration Constants (.json format)
    logger.info("\n--- 5. Saving Checkpoint & Calibration Metadata ---")
    output_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "model_state_dict": model.state_dict(),
        "channels": CHANNEL_NAMES,
        "min_bounds": MIN_BOUNDS,
        "max_bounds": MAX_BOUNDS,
        "per_channel_offset": final_offset,
        "per_channel_scale": final_scale,
        "latent_dim": 16,
        "window_size": WINDOW_SIZE,
    }

    torch.save(checkpoint, output_checkpoint)
    logger.info(f"[SUCCESS] Saved PyTorch model checkpoint to {output_checkpoint}")

    # Save calibration constants to secure JSON format (no pickle deserialization risk)
    calib_checkpoint = output_checkpoint.with_name("calibration_v1.json")
    calib_data = {
        "channels": CHANNEL_NAMES,
        "min_bounds": MIN_BOUNDS,
        "max_bounds": MAX_BOUNDS,
        "per_channel_offset": final_offset,
        "per_channel_scale": final_scale,
        "latent_dim": 16,
        "window_size": WINDOW_SIZE,
    }
    with open(calib_checkpoint, "w", encoding="utf-8") as f:
        json.dump(calib_data, f, indent=2)
    logger.info(f"[SUCCESS] Saved secure JSON calibration constants to {calib_checkpoint}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train PulseGuard-AI 1D-CNN Autoencoder")
    parser.add_argument("--epochs", type=int, default=15, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--out", type=Path, default=Path("backend/app/ml/autoencoder_v1.pt"), help="Output model path")
    args = parser.parse_args()

    train_autoencoder(epochs=args.epochs, batch_size=args.batch_size, lr=args.lr, output_checkpoint=args.out)
