"""Unit tests for TelemetryAutoencoder and scaling functions."""

from pathlib import Path
import numpy as np
import torch
import pytest

from backend.app.ml.autoencoder import (
    TelemetryAutoencoder,
    scale_raw_window,
    unscale_window,
    compute_per_channel_mse,
    CHANNEL_NAMES,
)


def test_autoencoder_forward_pass_shape():
    """Test TelemetryAutoencoder forward pass produces (batch, 3, 100) output."""
    model = TelemetryAutoencoder(in_channels=3, latent_dim=16)
    model.eval()

    dummy_input = torch.rand(4, 3, 100)  # batch of 4
    with torch.no_grad():
        recon = model(dummy_input)

    assert recon.shape == (4, 3, 100), f"Expected shape (4, 3, 100), got {recon.shape}"
    assert torch.all(recon >= 0.0) and torch.all(recon <= 1.0), "Sigmoid output must be in [0.0, 1.0]"


def test_min_max_scaling_and_unscaling():
    """Test scale_raw_window scales values to [0, 1] and unscale_window restores them."""
    # Create biological window: HR=75, SpO2=98, BP_sys=120
    raw = np.zeros((3, 100), dtype=np.float32)
    raw[0, :] = 75.0   # HR: [0, 300] -> 75/300 = 0.25
    raw[1, :] = 98.0   # SpO2: [0, 100] -> 98/100 = 0.98
    raw[2, :] = 120.0  # BP_sys: [0, 300] -> 120/300 = 0.40

    scaled = scale_raw_window(raw)
    assert scaled.shape == (3, 100)
    assert np.allclose(scaled[0, :], 0.25)
    assert np.allclose(scaled[1, :], 0.98)
    assert np.allclose(scaled[2, :], 0.40)

    unscaled = unscale_window(scaled)
    assert np.allclose(unscaled[0, :], 75.0)
    assert np.allclose(unscaled[1, :], 98.0)
    assert np.allclose(unscaled[2, :], 120.0)


def test_per_channel_mse_calculation():
    """Test compute_per_channel_mse calculates separate MSE for each channel."""
    x = torch.zeros(2, 3, 100)
    recon = torch.zeros(2, 3, 100)

    # Sample 0: HR error = 0.1, SpO2 error = 0.2, BP_sys error = 0.3
    recon[0, 0, :] = 0.1
    recon[0, 1, :] = 0.2
    recon[0, 2, :] = 0.3

    mse = compute_per_channel_mse(x, recon).numpy()
    assert mse.shape == (2, 3), f"MSE shape must be (2, 3), got {mse.shape}"

    assert mse[0, 0] == pytest.approx(0.01)  # 0.1^2
    assert mse[0, 1] == pytest.approx(0.04)  # 0.2^2
    assert mse[0, 2] == pytest.approx(0.09)  # 0.3^2


def test_saved_checkpoint_structure():
    """Test saved autoencoder_v1.pt and calibration_v1.json contain required fields without pickle."""
    ckpt_path = Path("backend/app/ml/autoencoder_v1.pt")
    assert ckpt_path.exists(), "autoencoder_v1.pt checkpoint must exist"

    # Verify checkpoint loads securely with weights_only=True (zero code execution risk)
    ckpt = torch.load(ckpt_path, weights_only=True)
    assert "model_state_dict" in ckpt
    assert "channels" in ckpt and ckpt["channels"] == ["hr", "spo2", "bp_sys"]
    assert "per_channel_offset" in ckpt
    assert "per_channel_scale" in ckpt
    assert "min_bounds" in ckpt
    assert "max_bounds" in ckpt

    # Verify no legacy pickle file exists
    pkl_path = Path("backend/app/ml/autoencoder_v1.pkl")
    assert not pkl_path.exists(), "autoencoder_v1.pkl must be deleted to eliminate pickle deserialization risks"

    # Verify calibration_v1.json exists and is valid JSON
    import json
    calib_path = Path("backend/app/ml/calibration_v1.json")
    assert calib_path.exists(), "calibration_v1.json must exist"
    with open(calib_path, "r", encoding="utf-8") as f:
        calib = json.load(f)
    assert "per_channel_offset" in calib
    assert "per_channel_scale" in calib


def test_batchnorm_single_sample_inference_consistency():
    """Regression test: model.eval() produces identical output on batch_size=1 and guards against BatchNorm train bugs."""
    ckpt_path = Path("backend/app/ml/autoencoder_v1.pt")
    ckpt = torch.load(ckpt_path, weights_only=True)

    model = TelemetryAutoencoder(in_channels=3, latent_dim=ckpt.get("latent_dim", 16))
    model.load_state_dict(ckpt["model_state_dict"])

    # Startup assertion: model must be in evaluation mode
    model.eval()
    assert model.training is False, "Autoencoder model must be in eval mode (model.training == False)"

    # Single-sample input (batch_size=1, 3 channels, 100 timesteps)
    torch.manual_seed(42)
    single_input = torch.rand(1, 3, 100)

    with torch.no_grad():
        out1 = model(single_input)
        out2 = model(single_input)

    # In eval mode with frozen running stats, outputs must be identical across calls
    assert torch.equal(out1, out2), (
        "Inference outputs for batch_size=1 must be identical across successive forward passes"
    )

    # In train mode, BatchNorm dynamically calculates batch stats and updates running statistics,
    # mutating state across calls. This proves why model.eval() and startup assertions are critical.
    model.train()
    assert model.training is True
    initial_running_mean = model.encoder_conv[1].running_mean.clone()
    _ = model(single_input)
    updated_running_mean = model.encoder_conv[1].running_mean.clone()
    assert not torch.equal(initial_running_mean, updated_running_mean), (
        "Train mode mutates BatchNorm running stats on batch_size=1, proving why eval() is vital"
    )

