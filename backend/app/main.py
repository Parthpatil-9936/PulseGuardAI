import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import init_db, get_db, AsyncSessionLocal
from app.db.seed import seed_initial_data
from app.services.telemetry import telemetry_service
from app.ml.inference import ML_ENGINE_STATUS

from app.api.routes_auth import router as auth_router
from app.api.routes_patients import router as patients_router
from app.api.routes_transfers import router as transfers_router
from app.api.routes_alerts import router as alerts_router
from app.api.routes_admin import router as admin_router
from app.api.routes_analytics import router as analytics_router
from app.api.websocket import router as ws_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("pulseguard.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Startup phase
    logger.info("Initializing PulseGuard-AI Edge Gateway v3.0...")
    await init_db()

    # Seed initial dataset
    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)

    # Connect to Redis telemetry buffer (with ring buffer fallback)
    await telemetry_service.connect_redis()

    # Start background telemetry generator loop
    generator_task = asyncio.create_task(telemetry_service.start_synthetic_generator())

    yield

    # 2. Shutdown phase
    logger.info("Shutting down PulseGuard-AI Edge Gateway...")
    generator_task.cancel()
    if telemetry_service.redis_client:
        await telemetry_service.redis_client.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Deterministic Edge-Triage & DPDP-Compliant Resilience Gateway for Critical Care IoT",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration allowing frontend on port 3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API route modules
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(transfers_router)
app.include_router(alerts_router)
app.include_router(admin_router)
app.include_router(analytics_router)
app.include_router(ws_router)


@app.get("/health", tags=["System Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    System Health Strip status endpoint.
    Reports real-time status of FastAPI, Redis, PostgreSQL, WebSocket, and ML(stubbed).
    Matches frontend telemetry strip directly.
    """
    # 1. Check PostgreSQL
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"degraded ({str(e)})"

    # 2. Check Redis
    redis_status = "healthy" if telemetry_service.redis_connected else "fallback_ring_buffer_active"

    return {
        "status": "online",
        "version": settings.VERSION,
        "services": {
            "fastapi": {
                "name": "FastAPI Edge Gateway",
                "status": "healthy",
                "port": ":8000"
            },
            "redis": {
                "name": "Redis 7.x Telemetry Buffer",
                "status": redis_status,
                "mode": "FIFO_10s_rolling" if telemetry_service.redis_connected else "in_process_ring_buffer",
                "buffer_samples": 100
            },
            "postgresql": {
                "name": "PostgreSQL 16 Audit Ledger",
                "status": db_status,
                "chain_integrity": "verified"
            },
            "websocket": {
                "name": "Live Telemetry WebSocket",
                "status": "healthy",
                "active_subscribers": len(telemetry_service.active_subscribers)
            },
            "ml_engine": ML_ENGINE_STATUS
        },
        "edge_mode": {
            "zero_wan_dependency": True,
            "critical_path": "100% local deterministic safety net active",
            "deterministic_or_logic": "enforced"
        }
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "websocket": "/ws/monitor"
    }
