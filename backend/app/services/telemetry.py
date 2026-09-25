import asyncio
import json
import logging
import time
from collections import deque
from typing import Dict, List, Any, Optional
import redis.asyncio as aioredis
from app.core.config import settings
from app.ml.inference import get_anomaly_score
from app.services.alert_service import evaluate_alert

logger = logging.getLogger("pulseguard.telemetry")


class InProcessRingBuffer:
    """
    Fixed-size in-memory ring buffer fallback.
    Activates automatically if Redis fails, guaranteeing hard-threshold evaluation never stops.
    """
    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self.buffers: Dict[str, deque] = {}

    def push(self, bed_id: str, sample: Dict[str, Any]):
        if bed_id not in self.buffers:
            self.buffers[bed_id] = deque(maxlen=self.capacity)
        self.buffers[bed_id].append(sample)

    def get_window(self, bed_id: str) -> List[Dict[str, Any]]:
        if bed_id in self.buffers:
            return list(self.buffers[bed_id])
        return []


class TelemetryService:
    def __init__(self):
        self.ring_buffer = InProcessRingBuffer(capacity=100)
        self.redis_client: Optional[aioredis.Redis] = None
        self.redis_connected: bool = False
        self.last_seen_timestamp: Dict[str, float] = {}
        self.last_sequence_num: Dict[str, int] = {}
        self.current_vitals: Dict[str, Dict[str, Any]] = {}
        self.active_subscribers: List[asyncio.Queue] = []
        self._generator_task: Optional[asyncio.Task] = None

    async def connect_redis(self):
        try:
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=1.0,
                socket_timeout=1.0
            )
            await self.redis_client.ping()
            self.redis_connected = True
            logger.info("Connected to Redis 7.x telemetry buffer.")
        except Exception as e:
            self.redis_connected = False
            logger.warning(f"Redis unavailable ({e}). Fallback to in-process ring buffer active.")

    async def push_sample(self, bed_id: str, sample: Dict[str, Any]):
        """
        Pushes physiological sample to Redis rolling list.
        Falls back to in-process ring buffer on any Redis error callback.
        NO PII in payload: only bed_id, seq, timestamp, and floats.
        """
        # Always update in-process ring buffer for zero-delay local evaluation
        self.ring_buffer.push(bed_id, sample)

        if self.redis_connected and self.redis_client:
            try:
                key = f"telemetry:bed:{bed_id}"
                # FIFO 10-second rolling window (~50-100 samples)
                payload = json.dumps(sample)
                pipe = self.redis_client.pipeline()
                pipe.lpush(key, payload)
                pipe.ltrim(key, 0, 99)
                pipe.expire(key, 30)
                await pipe.execute()
            except Exception as e:
                self.redis_connected = False
                logger.warning(f"Redis push error: {e}. In-process fallback active.")

    async def get_recent_window(self, bed_id: str) -> List[Dict[str, Any]]:
        if self.redis_connected and self.redis_client:
            try:
                key = f"telemetry:bed:{bed_id}"
                raw = await self.redis_client.lrange(key, 0, 99)
                if raw:
                    return [json.loads(item) for item in reversed(raw)]
            except Exception:
                self.redis_connected = False

        return self.ring_buffer.get_window(bed_id)

    async def ingest_tick(self, bed_id: str, sample: Dict[str, Any]):
        now = time.time()
        prev_time = self.last_seen_timestamp.get(bed_id, now)
        gap = now - prev_time
        self.last_seen_timestamp[bed_id] = now

        seq = sample.get("seq", 0)
        self.last_sequence_num[bed_id] = seq

        # Check sensor timeout invariant: gap > 2.0s marks no_signal
        if gap > settings.SENSOR_TIMEOUT_SECONDS and sample.get("lead_status") != "disconnected":
            logger.warning(f"Sensor timeout on Bed {bed_id}: {gap:.2f}s gap > 2.0s limit.")
            sample["lead_status"] = "disconnected"

        # Push to FIFO buffer
        await self.push_sample(bed_id, sample)

        # Get window and evaluate ML stub score + hard threshold
        window = await self.get_recent_window(bed_id)
        anomaly_score = get_anomaly_score(window)
        tier, factors = evaluate_alert(sample, anomaly_score)

        # Store latest telemetry snapshot
        telemetry_frame = {
            "bed_id": bed_id,
            "seq": seq,
            "timestamp": sample.get("timestamp", now),
            "hr": sample.get("hr", 75),
            "spo2": sample.get("spo2", 98),
            "bp_sys": sample.get("bp_sys", 120),
            "bp_dia": sample.get("bp_dia", 80),
            "rr": sample.get("rr", 16),
            "temp": sample.get("temp", 36.8),
            "tier": tier,
            "anomaly_score": anomaly_score,
            "factors": factors,
            "lead_status": sample.get("lead_status", "connected"),
        }
        self.current_vitals[bed_id] = telemetry_frame

        # Broadcast to WebSocket subscribers
        await self._broadcast(telemetry_frame)

    async def _broadcast(self, frame: Dict[str, Any]):
        dead_queues = []
        for q in self.active_subscribers:
            try:
                q.put_nowait(frame)
            except asyncio.QueueFull:
                pass
            except Exception:
                dead_queues.append(q)

        for dq in dead_queues:
            if dq in self.active_subscribers:
                self.active_subscribers.remove(dq)

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=100)
        self.active_subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self.active_subscribers:
            self.active_subscribers.remove(q)

    async def start_synthetic_generator(self):
        """
        Background synthetic multi-bed generator (10 beds) emitting samples at 1 Hz.
        Replaces physical sensors for test & evaluation.
        """
        seq = 0
        logger.info("Starting synthetic 10-bed telemetry loop.")

        # Baseline vital parameters per bed
        baselines = {
            "01": {"hr": 76, "spo2": 98, "bp_sys": 122, "bp_dia": 78},
            "02": {"hr": 104, "spo2": 92, "bp_sys": 148, "bp_dia": 96},  # Tier 2 warning
            "03": {"hr": 82, "spo2": 96, "bp_sys": 118, "bp_dia": 74},
            "04": {"hr": 138, "spo2": 81, "bp_sys": 84, "bp_dia": 52},   # Tier 1 critical breach!
            "05": {"hr": 68, "spo2": 99, "bp_sys": 116, "bp_dia": 72},
            "06": {"hr": 98, "spo2": 89, "bp_sys": 138, "bp_dia": 86},   # Tier 2 warning
            "07": {"hr": 84, "spo2": 97, "bp_sys": 112, "bp_dia": 70},
            "08": {"hr": 0, "spo2": 0, "bp_sys": 0, "bp_dia": 0, "lead_status": "disconnected"}, # Lead-off
            "09": {"hr": 72, "spo2": 98, "bp_sys": 126, "bp_dia": 80},
            "10": {"hr": 74, "spo2": 98, "bp_sys": 120, "bp_dia": 76},
        }

        while True:
            try:
                seq += 1
                now = time.time()
                for bed_id, base in baselines.items():
                    sample = {
                        "bed_id": bed_id,
                        "seq": seq,
                        "timestamp": now,
                        "hr": base["hr"],
                        "spo2": base["spo2"],
                        "bp_sys": base["bp_sys"],
                        "bp_dia": base["bp_dia"],
                        "rr": 16,
                        "temp": 36.8,
                        "lead_status": base.get("lead_status", "connected"),
                    }
                    await self.ingest_tick(bed_id, sample)

                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in telemetry generator loop: {e}")
                await asyncio.sleep(1.0)


telemetry_service = TelemetryService()
