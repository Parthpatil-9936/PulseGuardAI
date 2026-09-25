"""PulseGuard-AI Per-Bed Telemetry Ring Buffer Service.

Maintains a per-bed rolling window of the last 100 raw (HR, SpO2, BP_sys) samples
as a (3, 100) numpy array for ML 1D-CNN autoencoder scoring.

Backed by Redis (LPUSH / LTRIM 0 99) with automatic in-process collections.deque
fallback on redis.RedisError / ConnectionError.

Core Behaviors:
1. Concurrency isolation: Per-bed asyncio.Lock & isolated buffer states per bed_id.
2. Cold-start safety: `is_ready(bed_id)` starts False and requires 100 samples.
3. Explicit reset: `reset(bed_id)` clears state and triggers event callbacks.
4. Fail-safe crash fallback: Redis connection failure resets cold-start state and
   refills in-process deque buffer from scratch.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

try:
    import redis.asyncio as aioredis
    from redis.exceptions import RedisError
except ImportError:
    aioredis = None

    class RedisError(Exception):
        """Fallback RedisError exception when redis-py is not installed."""
        pass


logger = logging.getLogger(__name__)

WINDOW_SIZE = 100
DEFAULT_REDIS_URL = "redis://localhost:6379/0"


class TelemetryRingBuffer:
    """Per-bed sliding window ring buffer (3, 100) for ML telemetry feature extraction."""

    def __init__(
        self,
        redis_url: Optional[str] = DEFAULT_REDIS_URL,
        redis_client: Optional[Any] = None,
        window_size: int = WINDOW_SIZE,
        use_fallback: bool = False,
    ) -> None:
        self.redis_url = redis_url
        self.window_size = window_size
        self._redis = redis_client
        self._redis_connected = False
        self._redis_failed = use_fallback or (redis_url is None)

        # Per-bed state isolation
        self._bed_locks: Dict[str, asyncio.Lock] = {}
        self._fallback_deques: Dict[str, deque] = {}
        self._using_fallback: Dict[str, bool] = {}
        self._known_beds: set[str] = set()
        self._reset_callbacks: List[Callable[[str], Any]] = []
        self._fallback_callbacks: List[Callable[[List[str]], Any]] = []

    def _get_bed_lock(self, bed_id: str) -> asyncio.Lock:
        """Retrieve or create isolated per-bed asyncio lock."""
        if bed_id not in self._bed_locks:
            self._bed_locks[bed_id] = asyncio.Lock()
        return self._bed_locks[bed_id]

    def _get_fallback_deque(self, bed_id: str) -> deque:
        """Retrieve or create isolated per-bed collections.deque fallback."""
        if bed_id not in self._fallback_deques:
            self._fallback_deques[bed_id] = deque(maxlen=self.window_size)
        return self._fallback_deques[bed_id]

    def register_reset_callback(self, callback: Callable[[str], Any]) -> None:
        """Register a callback function to be invoked when a bed buffer is reset."""
        if callback not in self._reset_callbacks:
            self._reset_callbacks.append(callback)

    def register_fallback_callback(self, callback: Callable[[List[str]], Any]) -> None:
        """Register a callback function to be invoked on Redis->deque fallback transition."""
        if callback not in self._fallback_callbacks:
            self._fallback_callbacks.append(callback)

    async def _handle_redis_failure(
        self, trigger_bed_id: Optional[str] = None, exc: Optional[Exception] = None
    ) -> List[str]:
        """Coordinate Redis->deque fallback transition across all known beds.

        REDIS BLAST RADIUS INVARIANT:
        When Redis crashes, the volatile 10-second rolling window is wiped for ALL beds
        sharing this Redis instance. ML scoring goes dark across the entire ward during the
        ~10s refill window. Hard thresholds continue evaluating per tick with zero gap.
        """
        self._redis_connected = False
        self._redis_failed = True
        self._redis = None

        if trigger_bed_id:
            self._known_beds.add(trigger_bed_id)

        affected_beds = (
            sorted(list(self._known_beds))
            if self._known_beds
            else ([trigger_bed_id] if trigger_bed_id else [])
        )

        for b in affected_beds:
            self._using_fallback[b] = True
            deq = self._get_fallback_deque(b)
            deq.clear()

        # Emit structured log / event on fallback transition
        logger.error(
            f"[ring_buffer_fallback_event] REDIS CRASH / FALLBACK TRIGGERED | "
            f"status=DEGRADED | blast_radius={len(affected_beds)} beds | "
            f"affected_bed_ids={affected_beds} | "
            "ml_state=DARK (refilling 100-sample window ~10s) | "
            "safety_net=ACTIVE (hard thresholds continue per tick with zero gap) | "
            f"cause={exc or 'ManualChaosInjection'}"
        )

        # Wire through the reset event mechanism for every affected bed
        for b in affected_beds:
            await self._trigger_reset_callbacks(b)

        # Trigger registered fallback callbacks
        for cb in self._fallback_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(affected_beds)
                else:
                    cb(affected_beds)
            except Exception as e:
                logger.error(f"[ring_buffer] Error in fallback callback: {e}")

        return affected_beds

    async def trigger_redis_crash(
        self, affected_bed_ids: Optional[List[str]] = None
    ) -> List[str]:
        """Manually trigger a simulated Redis crash across multiple beds (for chaos testing)."""
        if affected_bed_ids:
            for b in affected_bed_ids:
                self._known_beds.add(b)
        return await self._handle_redis_failure(exc=ConnectionError("Simulated Redis Chaos Outage"))

    async def _get_redis_client(self) -> Optional[Any]:
        """Lazy connection to Redis client with error handling."""
        if self._redis is not None:
            return self._redis
        if self._redis_failed or aioredis is None or not self.redis_url:
            return None
        try:
            client = aioredis.from_url(
                self.redis_url, decode_responses=True, socket_connect_timeout=0.2
            )
            await client.ping()
            self._redis = client
            self._redis_connected = True
            return self._redis
        except Exception as e:
            logger.warning(
                f"[ring_buffer] Unable to connect to Redis at {self.redis_url}: {e}. "
                "Defaulting to in-process deque fallback."
            )
            self._redis = None
            self._redis_connected = False
            self._redis_failed = True
            return None

    async def _trigger_reset_callbacks(self, bed_id: str) -> None:
        """Execute registered reset event callbacks."""
        for cb in self._reset_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(bed_id)
                else:
                    cb(bed_id)
            except Exception as e:
                logger.error(f"[ring_buffer] Error in reset callback for bed {bed_id}: {e}")

    # ----------------------------------------------------------------------
    # 1 & 4. Push Telemetry Tick & Fallback Management
    # ----------------------------------------------------------------------
    async def push_tick(
        self,
        bed_id: str,
        hr: float,
        spo2: float,
        bp_sys: float,
        seq: int = 0,
        ts: Optional[Union[str, datetime]] = None,
    ) -> bool:
        """Push single tick (HR, SpO2, BP_sys) into bed's rolling buffer.

        Guarantees concurrency isolation using per-bed asyncio.Lock.
        """
        self._known_beds.add(bed_id)
        async with self._get_bed_lock(bed_id):
            sample = {
                "hr": float(hr),
                "spo2": float(spo2),
                "bp_sys": float(bp_sys),
                "seq": int(seq),
                "ts": (
                    ts.isoformat()
                    if isinstance(ts, datetime)
                    else (ts or datetime.now(timezone.utc).isoformat())
                ),
            }

            # Check if using fallback or attempting Redis push
            use_fallback = self._using_fallback.get(bed_id, False)

            if not use_fallback:
                r_client = await self._get_redis_client()
                if r_client is not None:
                    try:
                        redis_key = f"telemetry:window:{bed_id}"
                        payload_str = json.dumps(sample)
                        async with r_client.pipeline(transaction=True) as pipe:
                            pipe.lpush(redis_key, payload_str)
                            pipe.ltrim(redis_key, 0, self.window_size - 1)
                            await pipe.execute()
                        return True
                    except (RedisError, OSError, ConnectionError) as exc:
                        logger.error(
                            f"[ring_buffer] Redis crash/connection error on bed {bed_id}: {exc}! "
                            "Triggering coordinated fallback transition for all beds."
                        )
                        await self._handle_redis_failure(trigger_bed_id=bed_id, exc=exc)

            # Fallback path: collections.deque
            deq = self._get_fallback_deque(bed_id)
            deq.append(sample)
            return True

    # ----------------------------------------------------------------------
    # 2. Cold-Start State Check: is_ready()
    # ----------------------------------------------------------------------
    async def is_ready(self, bed_id: str) -> bool:
        """Return True only once 100 samples are present in the buffer."""
        self._known_beds.add(bed_id)
        async with self._get_bed_lock(bed_id):
            use_fallback = self._using_fallback.get(bed_id, False)
            if use_fallback or self._redis is None:
                deq = self._get_fallback_deque(bed_id)
                return len(deq) >= self.window_size

            try:
                r_client = await self._get_redis_client()
                if r_client is None:
                    deq = self._get_fallback_deque(bed_id)
                    return len(deq) >= self.window_size

                redis_key = f"telemetry:window:{bed_id}"
                length = await r_client.llen(redis_key)
                return length >= self.window_size
            except (RedisError, OSError, ConnectionError) as exc:
                logger.error(
                    f"[ring_buffer] Redis error during is_ready check on bed {bed_id}: {exc}. "
                    "Triggering coordinated fallback transition for all beds."
                )
                await self._handle_redis_failure(trigger_bed_id=bed_id, exc=exc)
                return False

    # ----------------------------------------------------------------------
    # Window Extraction: get_window() -> (3, 100) Array
    # ----------------------------------------------------------------------
    async def get_window(self, bed_id: str) -> Optional[np.ndarray]:
        """Extract (3, 100) numpy array ordered chronologically (oldest to newest).

        Returns None if `is_ready(bed_id)` is False.
        Row 0: HR
        Row 1: SpO2
        Row 2: BP_sys
        """
        self._known_beds.add(bed_id)
        async with self._get_bed_lock(bed_id):
            ready = await self._is_ready_unlocked(bed_id)
            if not ready:
                return None

            samples: List[Dict[str, float]] = []
            use_fallback = self._using_fallback.get(bed_id, False)

            if not use_fallback and self._redis is not None:
                try:
                    redis_key = f"telemetry:window:{bed_id}"
                    raw_items = await self._redis.lrange(redis_key, 0, self.window_size - 1)
                    # LPUSH index 0 is newest, index 99 is oldest -> reverse for chronological order
                    samples = [json.loads(item) for item in reversed(raw_items)]
                except (RedisError, OSError, ConnectionError) as exc:
                    logger.error(
                        f"[ring_buffer] Redis error during get_window for bed {bed_id}: {exc}. "
                        "Triggering coordinated fallback transition for all beds."
                    )
                    await self._handle_redis_failure(trigger_bed_id=bed_id, exc=exc)
                    return None
            else:
                deq = self._get_fallback_deque(bed_id)
                samples = list(deq)

            if len(samples) < self.window_size:
                return None

            hr_row = [float(s["hr"]) for s in samples[: self.window_size]]
            spo2_row = [float(s["spo2"]) for s in samples[: self.window_size]]
            bp_sys_row = [float(s["bp_sys"]) for s in samples[: self.window_size]]

            window_arr = np.array([hr_row, spo2_row, bp_sys_row], dtype=np.float32)
            assert window_arr.shape == (3, self.window_size), f"Invalid shape: {window_arr.shape}"
            return window_arr

    async def _is_ready_unlocked(self, bed_id: str) -> bool:
        """Internal helper for readiness check without acquiring lock again."""
        use_fallback = self._using_fallback.get(bed_id, False)
        if use_fallback or self._redis is None:
            deq = self._get_fallback_deque(bed_id)
            return len(deq) >= self.window_size

        try:
            redis_key = f"telemetry:window:{bed_id}"
            length = await self._redis.llen(redis_key)
            return length >= self.window_size
        except Exception:
            return False

    # ----------------------------------------------------------------------
    # 3. Explicit Reset Method: reset(bed_id)
    # ----------------------------------------------------------------------
    async def reset(self, bed_id: str) -> None:
        """Immediately clear bed buffer and personalization state, firing reset callbacks."""
        self._known_beds.add(bed_id)
        async with self._get_bed_lock(bed_id):
            logger.info(f"[ring_buffer] Resetting buffer and state for bed {bed_id}")

            # Clear fallback deque
            if bed_id in self._fallback_deques:
                self._fallback_deques[bed_id].clear()

            self._using_fallback[bed_id] = False

            # Clear Redis key if connected
            if self._redis is not None:
                try:
                    redis_key = f"telemetry:window:{bed_id}"
                    await self._redis.delete(redis_key)
                except Exception as e:
                    logger.warning(f"[ring_buffer] Redis delete failed on reset for {bed_id}: {e}")

            # Fire registered reset event callbacks
            await self._trigger_reset_callbacks(bed_id)
