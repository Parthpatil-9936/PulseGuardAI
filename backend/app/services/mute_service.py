import time
import datetime
from typing import Dict, Any, Optional
from app.core.config import settings

class MuteManager:
    """
    Server-side anti-tamper alarm mute coordinator.
    CORE INVARIANT: Server-enforced clamp caps any mute request to <= 300 seconds (5 minutes).
    Auto-unmutes immediately after expiry.
    """
    def __init__(self):
        # Maps bed_id or "ward" -> float timestamp when mute expires
        self.muted_until: Dict[str, float] = {}

    def request_mute(self, bed_id: Optional[str], requested_duration_seconds: int) -> Dict[str, Any]:
        key = bed_id if bed_id else "ward"
        
        # Hard server-side clamp: cannot exceed 300s under any circumstances
        clamped_duration = min(int(requested_duration_seconds), settings.MUTE_MAX_DURATION_SECONDS)
        if clamped_duration <= 0:
            clamped_duration = settings.MUTE_MAX_DURATION_SECONDS

        now = time.time()
        expiry = now + clamped_duration
        self.muted_until[key] = expiry

        expiry_dt = datetime.datetime.utcfromtimestamp(expiry)

        return {
            "target": key,
            "requested_duration_seconds": requested_duration_seconds,
            "clamped_duration_seconds": clamped_duration,
            "muted_until": expiry_dt.isoformat(),
            "active": True
        }

    def is_muted(self, bed_id: Optional[str] = None) -> bool:
        now = time.time()
        # Check ward-wide mute
        if self.muted_until.get("ward", 0) > now:
            return True
        # Check specific bed mute
        if bed_id and self.muted_until.get(bed_id, 0) > now:
            return True
        return False

    def unmute(self, bed_id: Optional[str] = None):
        key = bed_id if bed_id else "ward"
        if key in self.muted_until:
            del self.muted_until[key]


mute_manager = MuteManager()
