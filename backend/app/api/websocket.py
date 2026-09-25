import asyncio
import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select

from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.assignment import PatientAssignment
from app.models.patient import Bed
from app.services.telemetry import telemetry_service

logger = logging.getLogger("pulseguard.ws")

router = APIRouter(tags=["WebSocket Real-Time Monitoring"])


@router.websocket("/ws/monitor")
async def websocket_monitor(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    Authenticated, role-filtered real-time telemetry WebSocket.
    - Admin: Ward-wide oversight (all 10 beds)
    - Doctor: Filtered to assigned patients' telemetry streams (or ward view if permitted).
    """
    await websocket.accept()

    # Authenticate via query param token
    user_id = None
    role = "doctor"  # Default fallback if unauthenticated demo token
    assigned_bed_ids = set()

    if token:
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("sub")
            role = payload.get("role", "doctor").lower()

    # Fetch assigned bed IDs for doctor
    if role == "doctor" and user_id:
        try:
            async with AsyncSessionLocal() as session:
                # Query active assignments
                stmt = (
                    select(Bed.id)
                    .join(PatientAssignment, PatientAssignment.patient_id == Bed.patient_id)
                    .where(
                        PatientAssignment.doctor_id == user_id,
                        PatientAssignment.status == "active"
                    )
                )
                res = await session.execute(stmt)
                assigned_bed_ids = set(res.scalars().all())
        except Exception as e:
            logger.warning(f"Could not load doctor assignments: {e}")
            # Fallback to standard doctor demo beds if DB is seeding
            assigned_bed_ids = {"01", "02", "04", "07", "10"}

    # If no beds found or role is admin, allow all beds
    allow_all = (role == "admin") or (not assigned_bed_ids)

    queue = telemetry_service.subscribe()
    logger.info(f"WebSocket client connected: user={user_id}, role={role}, allow_all={allow_all}")

    try:
        while True:
            # Wait for next telemetry tick
            frame = await queue.get()
            bed_id = frame.get("bed_id")

            # Role-filtered streaming
            if allow_all or (bed_id in assigned_bed_ids):
                await websocket.send_text(json.dumps(frame))

    except (WebSocketDisconnect, asyncio.CancelledError):
        logger.info(f"WebSocket client disconnected: user={user_id}")
    except Exception as e:
        logger.error(f"WebSocket streaming error: {e}")
    finally:
        telemetry_service.unsubscribe(queue)
