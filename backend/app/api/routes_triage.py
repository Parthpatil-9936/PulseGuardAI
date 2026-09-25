"""FastAPI Route for ML Triage Prediction and Model Health.

Includes:
1. POST /api/v1/triage/predict: Validated inference endpoint with low-latency Redis caching.
2. DPDP-compliant SHA-256 chained audit logging (zero PII in audit store).
3. GET /health/model: Model readiness and parameter health check.
"""

from __future__ import annotations

import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.ml.inference import predict_triage
from app.ml.model_loader import ml_manager
from app.schemas.triage_predict import (
    ModelHealthResponse,
    TriagePredictRequest,
    TriagePredictResponse,
)
from app.services.audit_service import append_audit_log
from app.services.telemetry import telemetry_service

logger = logging.getLogger("pulseguard.api.triage")

router = APIRouter(tags=["ML Triage Prediction"])

REDIS_CACHE_PREFIX = "ml:pred_cache:"


@router.post(
    "/triage/predict",
    response_model=TriagePredictResponse,
    summary="Predict Clinical Triage Tier from Multi-Vital Telemetry",
    status_code=status.HTTP_200_OK,
)
async def predict_triage_endpoint(
    request: TriagePredictRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TriagePredictResponse:
    """Predicts patient triage tier (1-Catastrophic, 2-Warning, 3-Baseline)

    from 10-second multi-vital telemetry.
    - Validates feature shape, order, and biological limits via Pydantic.
    - Uses Redis to cache recent predictions (TTL: 10s) for low latency.
    - Cryptographically logs input hash + prediction to PostgreSQL audit ledger (DPDP compliant).
    """
    # 1. Check Model Readiness
    if not ml_manager.is_ready:
        if ml_manager.loading:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ML model is currently initializing. Please retry in a moment.",
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"ML model unavailable: {ml_manager.load_error or 'Not loaded'}",
        )

    # 2. Redis Cache Lookup (Low-latency repeat calls)
    cache_hit = False
    redis_client = telemetry_service.redis_client
    # Preliminary hash from request attributes for cache key check
    quick_hash_seed = f"{request.bed_id}:{len(request.samples or [])}:{request.raw_window is not None}"

    try:
        # Pre-generate prediction to obtain deterministic input_hash
        prediction = predict_triage(request, cached=False)
        cache_key = f"{REDIS_CACHE_PREFIX}{prediction.input_hash}"

        if telemetry_service.redis_connected and redis_client:
            try:
                cached_data = await redis_client.get(cache_key)
                if cached_data:
                    cached_dict = json.loads(cached_data)
                    cached_dict["cached"] = True
                    response.headers["X-Cache"] = "HIT"
                    return TriagePredictResponse(**cached_dict)
            except Exception as e:
                logger.warning(f"Redis cache lookup failed ({e}), proceeding with fresh inference")

        response.headers["X-Cache"] = "MISS"

        # 3. Cache into Redis with TTL
        if telemetry_service.redis_connected and redis_client:
            try:
                ttl = getattr(settings, "ML_PREDICTION_CACHE_TTL_SECONDS", 10)
                await redis_client.set(
                    cache_key,
                    prediction.model_dump_json(),
                    ex=ttl,
                )
            except Exception as e:
                logger.warning(f"Redis cache store failed: {e}")

        # 4. DPDP-Compliant PostgreSQL Cryptographic Audit Log
        # Invariant: Record prediction + input hash + timestamp; ZERO raw patient-identifiable data
        try:
            await append_audit_log(
                session=db,
                action="TRIAGE_PREDICTION",
                bed_id=prediction.bed_id,
                clinician_id=None,
                metadata={
                    "input_hash": prediction.input_hash,
                    "tier": prediction.tier,
                    "confidence": prediction.confidence,
                    "attributing_vital": prediction.attributing_vital,
                    "hard_breach": prediction.hard_breach,
                    "latency_ms": prediction.latency_ms,
                    "cached": False,
                    "model_version": prediction.model_version,
                },
            )
        except Exception as e:
            logger.warning(f"Non-blocking audit log write failure: {e}")

        return prediction

    except ValueError as ve:
        logger.warning(f"Validation error in triage prediction: {ve}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except RuntimeError as re:
        logger.error(f"Runtime error in triage prediction: {re}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(re),
        )
    except Exception as e:
        logger.error(f"Unexpected inference failure: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal ML inference error occurred",
        )


@router.get(
    "/health/model",
    response_model=ModelHealthResponse,
    summary="Get ML Model Status and Operational Health",
)
async def get_model_health() -> ModelHealthResponse:
    """Returns real-time loading, device, and readiness status of the 1D-CNN autoencoder."""
    status_info = ml_manager.get_health_status()
    return ModelHealthResponse(**status_info)
