from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

    PROJECT_NAME: str = "PulseGuard-AI Edge Gateway"
    VERSION: str = "3.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./pulseguard.db"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "pulseguard"
    POSTGRES_PORT: int = 5432

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Security
    SECRET_KEY: str = "pulseguard-super-secret-jwt-key-nexhack-2026-critical-care"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12

    # Resilience & Clinical Invariants
    MUTE_MAX_DURATION_SECONDS: int = 300  # Hard 5-minute anti-tamper server clamp
    TELEMETRY_BUFFER_SECONDS: int = 10     # 10s FIFO rolling buffer
    SENSOR_TIMEOUT_SECONDS: float = 2.0   # >2.0s gap marks bed no_signal
    
    # Deterministic physiological safety thresholds
    TIER1_SPO2_THRESHOLD: float = 85.0     # Critical hypoxia
    TIER1_HR_HIGH: float = 140.0           # Severe tachycardia
    TIER1_HR_LOW: float = 40.0             # Severe bradycardia
    TIER2_SPO2_THRESHOLD: float = 90.0     # Warning desaturation
    TIER2_HR_HIGH: float = 120.0           # Moderate tachycardia
    TIER2_HR_LOW: float = 50.0             # Moderate bradycardia


settings = Settings()
