"""PulseGuard-AI Configuration Settings.

Centralized configuration for system limits, networking, and thresholds.
Allows bed capacity, Redis connection, and scoring thresholds to be configured
via environment variables without hardcoded architectural ceilings.
"""

from __future__ import annotations

import os


class Settings:
    """System runtime settings with environment variable fallbacks."""

    def __init__(self) -> None:
        self.MAX_BEDS: int = int(os.getenv("MAX_BEDS", "10"))
        self.REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
        self.REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))


settings = Settings()
