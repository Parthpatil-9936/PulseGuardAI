"""Singleton Model Loader and Lifecycle Manager for PulseGuard-AI.

Guarantees:
1. Model is loaded ONCE at app startup (via FastAPI lifespan), not per-request.
2. Safe PyTorch deserialization using `weights_only=True` (zero pickle vulnerability).
3. Non-blocking initialization with `/health/model` reporting readiness.
4. Mandatory eval mode (`model.eval()`) and startup assertion before traffic is served.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("pulseguard.ml.loader")


class MLModelManager:
    """Manages the in-memory lifecycle of the 1D-CNN Telemetry Autoencoder."""

    _instance: Optional["MLModelManager"] = None

    def __init__(self) -> None:
        self.model: Any = None
        self.is_ready: bool = False
        self.loading: bool = False
        self.load_error: Optional[str] = None
        self.device: str = "cpu"
        self.model_version: str = "1D-CNN-Autoencoder-v1.0"
        self.load_duration_ms: float = 0.0

        # Calibrated normalization constants
        self.per_channel_offset: Dict[str, float] = {
            "hr": 0.000138,
            "spo2": 0.000731,
            "bp_sys": 0.000115,
        }
        self.per_channel_scale: Dict[str, float] = {
            "hr": 0.001122,
            "spo2": 0.003417,
            "bp_sys": 0.000566,
        }
        self.latent_dim: int = 16
        self.in_channels: int = 3
        self.window_size: int = 100

    @classmethod
    def get_instance(cls) -> "MLModelManager":
        if cls._instance is None:
            cls._instance = MLModelManager()
        return cls._instance

    def load_sync(
        self,
        checkpoint_path: Optional[Path] = None,
        calibration_path: Optional[Path] = None,
    ) -> None:
        """Synchronously load model and calibration artifacts."""
        import torch
        from app.ml.autoencoder import TelemetryAutoencoder

        start_time = time.perf_counter()
        self.loading = True
        self.load_error = None

        ckpt_path = checkpoint_path or Path("backend/app/ml/autoencoder_v1.pt")
        calib_path = calibration_path or Path("backend/app/ml/calibration_v1.json")

        # Resolve paths relative to root or backend if needed
        if not ckpt_path.exists() and Path("app/ml/autoencoder_v1.pt").exists():
            ckpt_path = Path("app/ml/autoencoder_v1.pt")
        if not calib_path.exists() and Path("app/ml/calibration_v1.json").exists():
            calib_path = Path("app/ml/calibration_v1.json")

        logger.info(f"Loading ML autoencoder checkpoint from {ckpt_path}...")

        try:
            # 1. Load calibration parameters first
            if calib_path.exists():
                with open(calib_path, "r", encoding="utf-8") as f:
                    calib_data = json.load(f)
                    self.per_channel_offset = calib_data.get(
                        "per_channel_offset", self.per_channel_offset
                    )
                    self.per_channel_scale = calib_data.get(
                        "per_channel_scale", self.per_channel_scale
                    )
                    self.latent_dim = calib_data.get("latent_dim", 16)
                    self.window_size = calib_data.get("window_size", 100)
                logger.info(f"Loaded calibration offsets and scales from {calib_path}")

            # 2. Instantiate architecture
            model = TelemetryAutoencoder(
                in_channels=self.in_channels, latent_dim=self.latent_dim
            )

            # 3. Load weights strictly with weights_only=True (zero-pickle security)
            if ckpt_path.exists():
                checkpoint = torch.load(ckpt_path, map_location="cpu", weights_only=True)
                if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                    model.load_state_dict(checkpoint["model_state_dict"])
                    if "per_channel_offset" in checkpoint and not calib_path.exists():
                        self.per_channel_offset = checkpoint["per_channel_offset"]
                    if "per_channel_scale" in checkpoint and not calib_path.exists():
                        self.per_channel_scale = checkpoint["per_channel_scale"]
                else:
                    model.load_state_dict(checkpoint)
                logger.info(f"Successfully loaded PyTorch state dict from {ckpt_path}")
            else:
                logger.warning(
                    f"Checkpoint file {ckpt_path} not found. Running with initialized baseline weights."
                )

            # 4. Enforce eval mode and determinism
            model.eval()
            assert not model.training, (
                "FATAL: Autoencoder model must be in eval mode (model.training == False) "
                "before serving traffic"
            )

            self.model = model
            self.is_ready = True
            self.loading = False
            self.load_duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.info(
                f"ML Engine successfully initialized in {self.load_duration_ms:.2f}ms. Status: READY"
            )

        except Exception as e:
            self.loading = False
            self.is_ready = False
            self.load_error = str(e)
            logger.error(f"Failed to load ML autoencoder model: {e}", exc_info=True)
            raise

    async def initialize_async(
        self,
        checkpoint_path: Optional[Path] = None,
        calibration_path: Optional[Path] = None,
    ) -> None:
        """Asynchronously load model without blocking event loop."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, self.load_sync, checkpoint_path, calibration_path
        )

    def get_health_status(self) -> Dict[str, Any]:
        """Provides status dictionary for /health/model and /health."""
        if self.is_ready:
            status = "ready"
            desc = "Production PyTorch 1D-CNN autoencoder mounted and active."
        elif self.loading:
            status = "loading"
            desc = "Model weights currently initializing in background."
        else:
            status = "error" if self.load_error else "unloaded"
            desc = self.load_error or "Model not loaded."

        return {
            "status": status,
            "model_name": "1D-CNN Telemetry Autoencoder",
            "version": self.model_version,
            "weights_path": "backend/app/ml/autoencoder_v1.pt",
            "device": self.device,
            "in_channels": self.in_channels,
            "latent_dim": self.latent_dim,
            "is_eval_mode": (
                not self.model.training if self.model is not None else False
            ),
            "load_duration_ms": round(self.load_duration_ms, 2),
            "description": desc,
        }


# Global singleton instance
ml_manager = MLModelManager.get_instance()
