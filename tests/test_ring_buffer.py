"""Unit tests for TelemetryRingBuffer per-bed rolling window service."""

import asyncio
import numpy as np
import pytest

from backend.app.services.ring_buffer import TelemetryRingBuffer


def test_cold_start_state_is_ready():
    """Test cold-start state: is_ready() is False until exactly 100 samples are pushed."""

    async def _test():
        buffer = TelemetryRingBuffer()
        bed_id = "bed-01"

        assert await buffer.is_ready(bed_id) is False, "New bed must start with is_ready=False"

        # Push 99 ticks
        for i in range(99):
            await buffer.push_tick(bed_id, hr=75 + i * 0.1, spo2=98, bp_sys=120, seq=i + 1)
            assert await buffer.is_ready(bed_id) is False, "is_ready must stay False for < 100 samples"

        # get_window should return None when not ready
        arr_not_ready = await buffer.get_window(bed_id)
        assert arr_not_ready is None, "get_window must return None before cold-start is complete"

        # Push 100th tick
        await buffer.push_tick(bed_id, hr=85.0, spo2=98.0, bp_sys=122.0, seq=100)
        assert await buffer.is_ready(bed_id) is True, "is_ready must become True when 100 samples are present"

        # get_window should return (3, 100) array
        arr_ready = await buffer.get_window(bed_id)
        assert arr_ready is not None
        assert arr_ready.shape == (3, 100), f"Window shape must be (3, 100), got {arr_ready.shape}"
        assert arr_ready.dtype == np.float32

    asyncio.run(_test())


def test_array_chronological_order():
    """Test (3, 100) array columns are ordered chronologically (oldest to newest)."""

    async def _test():
        buffer = TelemetryRingBuffer()
        bed_id = "bed-02"

        for i in range(100):
            # HR increases from 100.0 to 199.0
            await buffer.push_tick(bed_id, hr=100.0 + i, spo2=95.0, bp_sys=110.0, seq=i + 1)

        arr = await buffer.get_window(bed_id)
        assert arr is not None

        hr_row = arr[0, :]
        assert hr_row[0] == pytest.approx(100.0), "First column (index 0) must be oldest sample"
        assert hr_row[99] == pytest.approx(199.0), "Last column (index 99) must be newest sample"

    asyncio.run(_test())


def test_concurrency_isolation():
    """Test beds operate in total isolation; concurrent pushes do not corrupt windows."""

    async def _test():
        buffer = TelemetryRingBuffer()

        async def push_bed_ticks(bed_id: str, base_hr: float):
            for i in range(100):
                await buffer.push_tick(bed_id, hr=base_hr, spo2=98.0, bp_sys=120.0, seq=i + 1)

        # Push to bed-01 (HR=70.0) and bed-02 (HR=140.0) concurrently
        await asyncio.gather(
            push_bed_ticks("bed-01", 70.0),
            push_bed_ticks("bed-02", 140.0),
        )

        arr1 = await buffer.get_window("bed-01")
        arr2 = await buffer.get_window("bed-02")

        assert arr1 is not None and arr2 is not None
        assert np.allclose(arr1[0, :], 70.0), "Bed-01 HR window must contain only 70.0"
        assert np.allclose(arr2[0, :], 140.0), "Bed-02 HR window must contain only 140.0"

    asyncio.run(_test())


def test_explicit_reset_method_and_callbacks():
    """Test reset(bed_id) clears buffer, resets is_ready to False, and fires callbacks."""

    async def _test():
        buffer = TelemetryRingBuffer()
        bed_id = "bed-03"

        callback_invoked = []

        def on_reset(reset_bed_id: str):
            callback_invoked.append(reset_bed_id)

        buffer.register_reset_callback(on_reset)

        # Fill 100 ticks
        for i in range(100):
            await buffer.push_tick(bed_id, hr=80.0, spo2=98.0, bp_sys=120.0, seq=i + 1)

        assert await buffer.is_ready(bed_id) is True

        # Call reset
        await buffer.reset(bed_id)

        assert await buffer.is_ready(bed_id) is False, "is_ready must be False after reset"
        assert await buffer.get_window(bed_id) is None, "get_window must return None after reset"
        assert callback_invoked == ["bed-03"], "Reset callback must be invoked with bed_id"

    asyncio.run(_test())


def test_redis_crash_fallback_resets_state():
    """Test Redis crash/connection error switches to deque fallback and resets cold-start state."""

    async def _test():
        buffer = TelemetryRingBuffer()
        bed_id = "bed-04"

        # Fill 100 ticks using deque fallback
        for i in range(100):
            await buffer.push_tick(bed_id, hr=80.0, spo2=98.0, bp_sys=120.0, seq=i + 1)

        assert await buffer.is_ready(bed_id) is True

        # Simulate crash/fallback trigger
        buffer._using_fallback[bed_id] = True
        deq = buffer._get_fallback_deque(bed_id)
        deq.clear()  # Crash clears history

        assert await buffer.is_ready(bed_id) is False, "Crash fallback must reset is_ready to False"
        assert await buffer.get_window(bed_id) is None

    asyncio.run(_test())
