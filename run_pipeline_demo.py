"""PulseGuard-AI End-to-End Pipeline Demonstration Script.

Simulates reading multi-vital telemetry ticks from simulator/out/mixed-42/bed-01.jsonl,
passing them through:
1. TelemetryIngestionService (bounds, reordering, forward-fill, staleness, SQI, stuck sensor)
2. TelemetryRingBuffer (per-bed rolling (3,100) array & cold start check)
3. TriageService (hard thresholds, ML autoencoder scoring, factor attribution, hysteresis)

Prints live TriageDecisions showing cold start -> healthy baseline -> anomaly triage!
"""

import asyncio
import json
from pathlib import Path
from backend.app.services.ingest import TelemetryIngestionService
from backend.app.services.ring_buffer import TelemetryRingBuffer
from backend.app.services.triage import TriageService
from simulator.generator import GeneratorConfig, generate_file_dataset


async def main():
    print("==========================================================================")
    print("  PulseGuard-AI Edge Triage & Anomaly Pipeline Demonstration")
    print("==========================================================================")

    # 1. Ensure test mixed-dataset exists
    dataset_dir = Path("simulator/out/mixed-42")
    if not (dataset_dir / "manifest.json").exists():
        print(f"[demo] Generating synthetic mixed telemetry dataset at {dataset_dir}...")
        cfg = GeneratorConfig(
            mode="mixed",
            seed=42,
            duration_s=60.0,
            beds=1,
            outdir=dataset_dir,
            inject_disorder=True,
            degenerate_signal=True,
        )
        generate_file_dataset(cfg)

    # 2. Instantiate pipeline services
    ingestion_service = TelemetryIngestionService(reorder_buffer_size=3)
    ring_buffer = TelemetryRingBuffer(use_fallback=True)
    triage_service = TriageService(
        ring_buffer=ring_buffer,
        checkpoint_path=Path("backend/app/ml/autoencoder_v1.pt"),
        hysteresis_count=3,
    )

    bed_file = dataset_dir / "bed-01.jsonl"
    print(f"[demo] Reading telemetry stream from {bed_file}...\n")

    tick_count = 0
    decisions_summary = {1: 0, 2: 0, 3: 0}

    with open(bed_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            raw_payload = json.loads(line)

            # Step 1: Ingest & Pre-filter raw tick
            processed_ticks = ingestion_service.process_raw_payload(raw_payload)

            for tick in processed_ticks:
                tick_count += 1

                # Step 2: Push tick to Ring Buffer
                await ring_buffer.push_tick(
                    bed_id=tick.bed_id,
                    hr=tick.hr,
                    spo2=tick.spo2,
                    bp_sys=tick.bp_sys,
                    seq=tick.seq,
                    ts=tick.ts,
                )

                # Step 3: Evaluate 3-Tier Alert Cascade Triage
                decision = await triage_service.evaluate_tick(tick)
                decisions_summary[decision.tier] += 1

                # Print key ticks (cold start, tier changes, anomalies, hard breaches)
                if tick_count <= 5 or tick_count in (100, 101) or decision.tier in (1, 2) or decision.hard_breach:
                    tier_badge = "[TIER 1 - CATASTROPHIC]" if decision.tier == 1 else "[TIER 2 - WARNING]" if decision.tier == 2 else "[TIER 3 - BASELINE]"
                    cold_badge = " [COLD START]" if decision.is_cold_start else ""
                    print(
                        f"Tick #{tick_count:03d} | Bed: {decision.bed_id} | Seq: {tick.seq} | "
                        f"HR: {tick.hr:3.0f} SpO2: {tick.spo2:2.0f}% BP: {tick.bp_sys:3.0f}/{tick.bp_dia:2.0f} | "
                        f"{tier_badge}{cold_badge} | ML Score: {decision.confidence:.4f} | Reason: {decision.reason}"
                    )

    print("\n==========================================================================")
    print(f"  Pipeline Demonstration Completed!")
    print(f"  Processed Total Ticks: {tick_count}")
    print(f"  Triage Summary: Tier 1 (Red): {decisions_summary[1]} | Tier 2 (Yellow): {decisions_summary[2]} | Tier 3 (Green): {decisions_summary[3]}")
    print("==========================================================================")


if __name__ == "__main__":
    asyncio.run(main())
