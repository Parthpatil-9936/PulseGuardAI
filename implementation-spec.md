# PulseGuard-AI — System Implementation Technical Specification

Deterministic Edge-Triage & DPDP-Compliant Resilience Gateway.
Core invariant: 100% local, sub-5ms alarm path, zero WAN dependencies.

## 1. Architectural Strategy & Reconciled Tech Stack

To maintain sub-5ms deterministic triage while avoiding event-loop blocking
during high-frequency array processing:
- **Edge Ingestion & Inference Daemon** — FastAPI (Python 3.11 / AsyncIO).
- **Real-Time Sliding Window** — Redis 7.x, volatile in-memory FIFO, 10s
  rolling buffer per bed (~50-100 samples), no disk I/O.
- **Medicolegal & DPDP Audit Store** — PostgreSQL 16, append-only,
  transaction-safe, HMAC-SHA256 chained clinician action logs.
- **Presentation Layer** — React + Vite + TailwindCSS, live waveforms and
  advisory cards over WebSockets (WSS).
- **Container Orchestration** — single-host docker-compose.yml, total
  isolation from public internet outages.

Data flow: Bed telemetry (MQTT/JSON) → FastAPI zero-trust ingestion gateway
(Pydantic validation + range clamp + cosine-similarity drift/tamper check) →
Redis 10s FIFO window (async, non-blocking) → ML anomaly engine → PostgreSQL
SHA-256 chained audit log (async, non-blocking) → React clinical ward
dashboard (10-bed urgency cards, 5-min mute clamp, "Simulate Cloud Outage"
toggle).

## 2. ML Pipeline: 1D-CNN Autoencoder & Parallel Safety Net

NOTE: This project uses ONLY the 1D-CNN Autoencoder described below.
Isolation Forest, mentioned in earlier spec drafts, has been dropped from
this implementation.

### Model Architecture & Telemetry Feature Processing
1. **Feature Extraction** — incoming ticks enter the Redis FIFO buffer.
   Rolling statistical markers (mean, variance, cross-vital covariance
   across HR, SpO2, BP) may still be computed for dashboard display, but are
   NOT the ML model's input — the autoencoder consumes the raw (3, 100)
   sequence directly (HR, SpO2, BP_sys channels x 100 timesteps).
2. **Signal Quality & Baseline Drift** — cosine-similarity baseline check
   evaluates waveform morphology. Slow baseline wander (0.05-0.5 Hz) flags
   as sensor drift; sudden discontinuous open-circuit values flag as
   tamper/lead disconnect rather than cardiac collapse.
3. **Sequence Anomaly Engine (1D-CNN Autoencoder)** — trained exclusively on
   healthy, homeostatic baseline profiles. Reconstructs the incoming
   10-second multi-vital array. Deviations from homeostatic patterns cause
   high Mean Squared Error (MSE) across diverging vital channels, yielding a
   continuous Anomaly Score normalized 0.0-1.0 in under 5 milliseconds.

### The 3-Tier Alert Cascade & the Deterministic OR'd Safety Net
Hard physiological thresholds and the ML score are OR'd, never AND'd — a low
ML score can never suppress a hard threshold breach.

- **TIER 1 — Catastrophic/Siren**: SpO2<85%, asystole, extreme rate
  divergence, OR ML Anomaly Score>0.9. Immediate hardwire bypass, audible
  alarm, bed card pulses red — cannot be suppressed.
- **TIER 2 — Warning/Advisory**: multi-vital covariance divergence with ML
  score between 0.5 and 0.9 (e.g. HR elevating while BP collapses).
  High-priority yellow card with plain-language summary, requires clinician
  acknowledgment, no panic sirens.
- **TIER 3 — Transient Noise/Suppressed**: single-vital transient spike
  (coughing, repositioning) with ML score<0.5. Silently logged to
  PostgreSQL, sirens suppressed, "Noise Suppression" counter increments.

## 3. DPDP Act & Data Protection Implementation

- **Data Minimization (Section 6, DPDP)** — ingestion schemas strictly
  prohibit patient PII. Telemetry payloads carry only an ephemeral UUID or
  hardware bed_id, a monotonic sequence number, and physiological floats.
- **Purpose Limitation via Volatile Storage (Section 8, DPDP)** —
  high-frequency waveform data resides exclusively in volatile in-memory
  Redis buffers (10s TTL), auto-purged. Never persisted to disk or
  transmitted across WAN.
- **Cryptographically Chained Audit Ledger** — clinician overrides,
  acknowledgments, mute actions write to PostgreSQL using SHA-256
  hash-chaining. Any post-hoc tampering or row deletion breaks the
  verifiable hash chain, ensuring non-repudiation for hospital medicolegal
  defense.

```
Hash_n = SHA-256( Hash_(n-1) || Timestamp || Bed ID || Clinician ID || Action )
```

## 4. Failure Modes & Edge Resilience Handling

| Failure | Detection | Local Behavior | Clinical Safety Guarantee |
|---|---|---|---|
| WAN/Cloud Outage | 5s ping heartbeat drop | Switches outbound queue to local disk buffer; dashboard badge "Offline." | Zero change in ward monitoring. Triage, hard thresholds, local alerts run at 100%. |
| Redis Crash | Connection error callback in FastAPI client | Falls back to internal in-process Python ring buffer. | Cross-tick correlation briefly constrained, but hard thresholds evaluate per-tick and continue firing. |
| PostgreSQL Crash | Async SQLAlchemy write timeout | Audit records buffer in memory; flush with Gap-Marker flag on reconnect. | Alarm path async/non-blocking, continues without deadlock. |
| Sensor Disconnect | Sequence ID gap or tick timeout >2.0s | Tile shifts green→gray "No Signal." | Silence never rendered as healthy. |
| Accidental Mute | REST /mute payload execution | Server-side clamp limits duration to 300s. Client input cannot override. | Alarms auto-unmute after 5 minutes, preventing permanent silencing. |

## 5. Phase-by-Phase 36-Hour Build Plan

- **Phase 1 (Hours 0-8) — Core Foundation & Contracts**: Initialize
  docker-compose.yml linking FastAPI, Redis, PostgreSQL, React. Freeze JSON
  data contracts for /ingest/telemetry, /alerts/push, /alerts/{id}/action.
  Deploy multi-bed synthetic telemetry generator.
- **Phase 2 (Hours 8-18) — Ingestion, Buffer & ML Core**: Build Redis 10s
  FIFO sliding window with monotonic sequence validation. Implement SQI and
  cosine-similarity baseline drift filter. Integrate the autoencoder anomaly
  scoring model and the parallel OR'd safety-net routing logic.
- **Phase 3 (Hours 18-26) — Clinical Dashboard & Resilience Controls**:
  Build 10-bed React dashboard with real-time WebSocket bindings and
  Chart.js rolling vital displays. Implement server-side 5-minute mute
  clamping and the in-process ring buffer fallback for Redis outages. Build
  "Simulate Cloud Outage" toggle and bed "No Signal" timeout handlers.
- **Phase 4 (Hours 26-32) — DPDP Audit Ledger & Verification**: Implement
  append-only PostgreSQL ledger with SHA-256 hash chaining. Validate all
  acceptance criteria run without manual intervention. Execute chaos
  testing: inject Tier-1 events while disconnecting network interfaces and
  stopping database containers.
- **Phase 5 (Hours 32-36) — Code Freeze & Presentation Dry Run**: Lock all
  codebase repositories; restrict changes strictly to demo bug fixes.
  Rehearse demo sequence: Quiet Ward → Tier-3 Noise Suppression → Tier-1
  Hypoxia Alert → Simulate Cloud Blackout → DPDP Audit Verification.
