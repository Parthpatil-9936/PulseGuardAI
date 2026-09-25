"""PulseGuard-AI 1D-CNN Autoencoder Model.

Small 1D-CNN Autoencoder in PyTorch:
- Input channels: 3 (HR, SpO2, BP_sys)
- Input timesteps: 100 (10 seconds @ 10 Hz)
- Latent dimension: ~16
- Encoder downsampling: 100 -> 50 -> 25 -> 5 timesteps
- Decoder upsampling: 5 -> 25 -> 50 -> 100 timesteps + Sigmoid output
- Min-max scaling: inputs scaled to [0, 1] based on biological bounds
- Per-channel reconstruction error: separate MSE for HR, SpO2, BP_sys
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import torch
import torch.nn as nn

CHANNEL_NAMES: List[str] = ["hr", "spo2", "bp_sys"]
MIN_BOUNDS: Dict[str, float] = {"hr": 0.0, "spo2": 0.0, "bp_sys": 0.0}
MAX_BOUNDS: Dict[str, float] = {"hr": 300.0, "spo2": 100.0, "bp_sys": 300.0}


class TelemetryAutoencoder(nn.Module):
    """1D-CNN Autoencoder for multi-vital telemetry reconstruction."""

    def __init__(self, in_channels: int = 3, latent_dim: int = 16) -> None:
        super().__init__()
        self.in_channels = in_channels
        self.latent_dim = latent_dim

        # Encoder: (batch, 3, 100) -> (batch, 16, 50) -> (batch, 32, 25) -> (batch, 32, 5) -> (batch, 16)
        self.encoder_conv = nn.Sequential(
            nn.Conv1d(3, 16, kernel_size=3, stride=2, padding=1),  # (16, 50)
            nn.BatchNorm1d(16),
            nn.LeakyReLU(0.2),
            nn.Conv1d(16, 32, kernel_size=3, stride=2, padding=1),  # (32, 25)
            nn.BatchNorm1d(32),
            nn.LeakyReLU(0.2),
            nn.Conv1d(32, 32, kernel_size=5, stride=5, padding=0),  # (32, 5)
            nn.BatchNorm1d(32),
            nn.LeakyReLU(0.2),
        )
        self.fc_enc = nn.Linear(32 * 5, latent_dim)  # 160 -> 16

        # Decoder: (batch, 16) -> (batch, 160) -> (batch, 32, 5) -> (batch, 32, 25) -> (batch, 16, 50) -> (batch, 3, 100)
        self.fc_dec = nn.Linear(latent_dim, 32 * 5)
        self.decoder_conv = nn.Sequential(
            nn.ConvTranspose1d(32, 32, kernel_size=5, stride=5, padding=0),  # (32, 25)
            nn.BatchNorm1d(32),
            nn.LeakyReLU(0.2),
            nn.ConvTranspose1d(
                32, 16, kernel_size=3, stride=2, padding=1, output_padding=1
            ),  # (16, 50)
            nn.BatchNorm1d(16),
            nn.LeakyReLU(0.2),
            nn.ConvTranspose1d(
                16, 3, kernel_size=3, stride=2, padding=1, output_padding=1
            ),  # (3, 100)
            nn.Sigmoid(),  # Output strictly bounded in [0.0, 1.0]
        )

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """Encode (batch, 3, 100) into (batch, latent_dim)."""
        h = self.encoder_conv(x)
        h_flat = h.view(h.size(0), -1)
        z = self.fc_enc(h_flat)
        return z

    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """Decode (batch, latent_dim) into (batch, 3, 100)."""
        h_flat = self.fc_dec(z)
        h = h_flat.view(h_flat.size(0), 32, 5)
        out = self.decoder_conv(h)
        return out

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Full forward reconstruction pass."""
        z = self.encode(x)
        recon = self.decode(z)
        return recon


def scale_raw_window(raw_arr: np.ndarray) -> np.ndarray:
    """Min-max scale raw biological array (3, 100) or (N, 3, 100) to [0, 1] range."""
    scaled = np.zeros_like(raw_arr, dtype=np.float32)
    mins = [MIN_BOUNDS["hr"], MIN_BOUNDS["spo2"], MIN_BOUNDS["bp_sys"]]
    maxs = [MAX_BOUNDS["hr"], MAX_BOUNDS["spo2"], MAX_BOUNDS["bp_sys"]]

    if raw_arr.ndim == 2:
        for c in range(3):
            scaled[c, :] = (raw_arr[c, :] - mins[c]) / (maxs[c] - mins[c])
    elif raw_arr.ndim == 3:
        for c in range(3):
            scaled[:, c, :] = (raw_arr[:, c, :] - mins[c]) / (maxs[c] - mins[c])
    else:
        raise ValueError(f"Invalid array dimension for scaling: {raw_arr.ndim}")

    return np.clip(scaled, 0.0, 1.0)


def unscale_window(scaled_arr: np.ndarray) -> np.ndarray:
    """Convert [0, 1] scaled array back to raw biological units."""
    raw = np.zeros_like(scaled_arr, dtype=np.float32)
    mins = [MIN_BOUNDS["hr"], MIN_BOUNDS["spo2"], MIN_BOUNDS["bp_sys"]]
    maxs = [MAX_BOUNDS["hr"], MAX_BOUNDS["spo2"], MAX_BOUNDS["bp_sys"]]

    if scaled_arr.ndim == 2:
        for c in range(3):
            raw[c, :] = scaled_arr[c, :] * (maxs[c] - mins[c]) + mins[c]
    elif scaled_arr.ndim == 3:
        for c in range(3):
            raw[:, c, :] = scaled_arr[:, c, :] * (maxs[c] - mins[c]) + mins[c]
    else:
        raise ValueError(f"Invalid array dimension for unscaling: {scaled_arr.ndim}")

    return raw


def compute_per_channel_mse(
    input_scaled: torch.Tensor, recon_scaled: torch.Tensor
) -> torch.Tensor:
    """Compute separate per-channel MSE across timesteps for each sample in batch.

    Inputs:
      input_scaled: Tensor of shape (batch, 3, 100)
      recon_scaled: Tensor of shape (batch, 3, 100)

    Returns:
      per_channel_mse: Tensor of shape (batch, 3) where columns are [hr_mse, spo2_mse, bp_sys_mse]
    """
    diff_sq = (input_scaled - recon_scaled) ** 2
    per_channel_mse = diff_sq.mean(dim=2)  # Mean over timesteps -> (batch, 3)
    return per_channel_mse
