# PulseGuard-AI — Full-Stack Engineering & Database Architecture Guide
**Target Audience:** Frontend Engineers, Backend Engineers, Database Architects, Hardware/IoT Gateway Engineers  
**System Target:** PulseGuard-AI Edge Gateway & ICU Command Center  
**Status:** Production Reference Specification (v3.1)  

---

## 1. Executive Overview & Data Flow Pipeline

PulseGuard-AI is an edge-native, local-first patient monitoring platform that processes continuous high-frequency multi-vital telemetry (10 Hz) from bedside monitors, evaluates physiological deterioration via a 1D-CNN autoencoder and deterministic hard tripwires, and renders live alerts with zero WAN dependency.

### Complete Data Flow Diagram

```
 Bedside Monitor Hardware (ECG, SpO2, NIBP)
                   │
                   ▼ (10 Hz JSON Telemetry Stream)
 ┌────────────────────────────────────────────────────────┐
 │ 1. Ingestion Layer (`TelemetryIngestionService`)      │
 │    - Pydantic schema validation & bounds enforcement   │
 │    - Monotonic seq sorting & duplicate packet dropping │
 │    - Forward-fill rate mismatch & staleness tracking   │
 │    - Sensor SQI & zero-variance stuck-sensor guard     │
 └─────────────────────────┬──────────────────────────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
 ┌──────────────────────┐    ┌───────────────────────────────────┐
 │ 2. Zero-Delay Tripwire│    │ 3. 10-Second Rolling Window Buffer│
 │    SpO2 < 85%         │    │    (`TelemetryRingBuffer`)        │
 │    HR < 20 / > 220    │    │    - Volatile Redis FIFO Lists    │
 │    BP_sys < 60 / > 200│    │    - In-Process deque Fallback    │
 │    BP_dia > 120       │    │    - 100 timesteps @ 10 Hz        │
 │    ECG Lead Off       │    └─────────────────┬─────────────────┘
 └───────────┬──────────┘                       │ (if is_ready == True)
             │                                  ▼
             │               ┌───────────────────────────────────┐
             │               │ 4. 1D-CNN ML Inference Engine     │
             │               │    - Min-Max Scaling to [0.0, 1.0]│
             │               │    - Forward pass (eval mode)     │
             │               │    - Per-channel MSE calculation  │
             │               │    - Calibrated normalization     │
             │               │    - Factor attribution (HR/SpO2/ │
             │               │      BP_sys)                      │
             │               └──────────────────┬────────────────┘
             │                                  │
             └─────────────┬────────────────────┘
                           ▼
 ┌────────────────────────────────────────────────────────┐
 │ 5. OR'd 3-Tier Decision Engine (`TriageService`)       │
 │    - Unconditional Tier-1 hard breach bypass           │
 │    - Hysteresis anti-flicker debouncing (3 ticks)      │
 │    - Server-side siren mute clamping (<= 300s)         │
 └─────────────────────────┬──────────────────────────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
 ┌──────────────────────┐    ┌───────────────────────────────────┐
 │ 6. Persistence Layer │    │ 7. Real-Time WebSocket Delivery   │
 │    - Timeseries Store│    │    - `/ws/monitor` (10 Hz ticks)  │
 │    - Alerts Ledger   │    │    - Live React ICU Dashboard     │
 │    - Audit Chain     │    │    - Audio Siren + Visual Banner  │
 └──────────────────────┘    └───────────────────────────────────┘
```

---

## 2. Telemetry Input Specification (Ingestion Contract)

### 2.1 Raw Telemetry JSON Payload (`TelemetryTick`)
Bedside monitors or edge IoT gateways must emit a continuous JSON tick every **100 ms (10 Hz)** to the backend telemetry pipeline.

```json
{
  "bed_id": "bed-01",
  "ts": "2026-09-25T18:38:37.123Z",
  "seq": 10452,
  "hr": 78,
  "spo2": 98,
  "bp_sys": 120,
  "bp_dia": 80,
  "temp": 37.0,
  "ecg_lead_ok": true
}
```

### 2.2 Field Validation & Engineering Invariants

| Field | Type | Required? | Accepted Range | Clinical & Engineering Handling |
| :--- | :--- | :--- | :--- | :--- |
| `bed_id` | `string` | **Yes** | Configurable: `get_bed_id_pattern(settings.MAX_BEDS)` | Default pattern `^bed-(0[1-9]\|10)$`. Configurable via environment variable `MAX_BEDS` (e.g. `MAX_BEDS=24`). Rejects out-of-range beds. |
| `ts` | `string` / `number` | **Yes** | ISO-8601 UTC or millisecond Unix timestamp | Automatically parsed to UTC timezone-aware datetime. |
| `seq` | `integer` | **Yes** | $\ge 0$ | Strictly monotonic integer counter incremented by monitor hardware. |
| `hr` | `integer` | Optional | $0 - 300\text{ bpm}$ | Values $<0$ or $>300$ raise `ValidationError` (biologically impossible). Forward-filled if missing. |
| `spo2` | `integer` | Optional | $0 - 100\,\%$ | Values $<0$ or $>100$ raise `ValidationError`. Forward-filled if missing. |
| `bp_sys` | `integer` | Optional | $0 - 300\text{ mmHg}$ | Systolic blood pressure. Forward-filled if missing. |
| `bp_dia` | `integer` | Optional | $0 - 200\text{ mmHg}$ | Diastolic blood pressure. Constrained: $\text{bp\_dia} \le \text{bp\_sys}$. |
| `temp` | `float` | Optional | $30.0 - 45.0\,^\circ\text{C}$ | Core body temperature. Values $<30.0$ or $>45.0$ are rejected. Forward-filled with `temp_staleness_ms` tracking. |
| `ecg_lead_ok` | `boolean` | **Yes** (defaults `true`) | `true` or `false` | Hardware electrode impedance status. `false` indicates physical lead detachment. |

### 2.3 Edge Case Defenses at Ingestion

1. **Reorder Defense:**  
   Network jitter can cause packets to arrive out of order. The ingestion layer maintains a 5-tick rolling reorder window sorted by `seq`. Late packets within 5 ticks are reordered; duplicate sequence numbers are dropped immediately. Sequence jumps $>5$ ticks set `seq_gap_flag = True`.
2. **Rate Mismatch & Forward Filling:**  
   Non-invasive blood pressure (NIBP) and temperature are sampled less frequently than ECG. When a tick omits `hr`, `spo2`, `bp_sys`, `bp_dia`, or `temp`, the ingestion service forward-fills the value from `last_known_vitals` and records the elapsed time in `staleness_ms`. If no prior value exists, physiological baselines (HR: 75, SpO2: 98, BP: 120/80, Temp: 37.0) are utilized.
3. **Sensor Disconnect & Stuck-Sensor Guard:**  
   If a vital channel displays zero numerical variance across 20 consecutive ticks (2.0 seconds at 10 Hz), the channel is marked as stuck/disconnected, triggering `drift_flag = "tamper"`, which immediately trips Tier-1 alert status.
4. **Hardware Lead Disconnect:**  
   If `ecg_lead_ok == false`, the system bypasses all downstream ML and debouncing, immediately firing Tier-1 with reason `"CRITICAL: ECG lead disconnected — no signal"`.

---

## 3. Machine Learning Input & Output Specification

### 3.1 10-Second Sliding Window
The ML model expects an exact **100-sample (10-second @ 10 Hz)** rolling biological window across 3 channels:
$$\mathbf{X}_{\text{raw}} \in \mathbb{R}^{3 \times 100} \quad \text{Channels: } [0: \text{HR}, 1: \text{SpO2}, 2: \text{BP\_sys}]$$

- **Cold Start Window:** For the first 10 seconds of a bed being monitored (or after a buffer reset), `ring_buffer.is_ready(bed_id)` is `False`. The triage engine returns `ml_score = 0.0`, `is_cold_start = True`, and `reason = "cold_start"`. Hard thresholds remain 100% active during cold start.
- **Normalization:** Prior to inference, raw values are scaled to $[0.0, 1.0]$:
  $$\text{scaled} = \text{clip}\left(\frac{\text{raw} - \min}{\max - \min}, 0.0, 1.0\right)$$
  - HR bounds: $[0, 300]$
  - SpO2 bounds: $[0, 100]$
  - BP_sys bounds: $[0, 300]$

### 3.2 ML Autoencoder Outputs
The 1D-CNN autoencoder produces a reconstructed tensor $\hat{\mathbf{X}} \in \mathbb{R}^{1 \times 3 \times 100}$.

1. **Per-Channel MSE:**
   $$\text{MSE}_c = \frac{1}{100} \sum_{t=1}^{100} (X_{c,t} - \hat{X}_{c,t})^2 \quad \text{for } c \in \{\text{hr}, \text{spo2}, \text{bp\_sys}\}$$
2. **Normalized Anomaly Scores (`norm_errors`):**
   $$\text{norm\_score}_c = \text{clip}\left(\frac{\text{MSE}_c - \text{offset}_c}{\text{scale}_c}, 0.0, 1.0\right)$$
   *(Offsets and scales are read from `backend/app/ml/calibration_v1.json`)*
3. **ML Confidence:** $\text{ml\_score} = \max(\text{norm\_score}_{\text{hr}}, \text{norm\_score}_{\text{spo2}}, \text{norm\_score}_{\text{bp\_sys}})$
4. **Attributing Vital:** $\text{attributing\_vital} = \text{argmax}_c(\text{norm\_score}_c)$

---

## 4. Triage Decision & Alert Cascade (TriageDecision)

The `TriageService` synthesizes hard thresholds and ML anomaly scores into a clean, unified payload emitted on every tick.

### 4.1 Triage Output JSON Schema

```json
{
  "bed_id": "bed-01",
  "ts": "2026-09-25T18:38:37.123Z",
  "tier": 2,
  "confidence": 0.7421,
  "reason": "WARNING: SPO2 divergent from expected pattern",
  "attributing_vital": "spo2",
  "drift_flag": "none",
  "is_cold_start": false,
  "hard_breach": false,
  "raw_tier": 2,
  "audio_muted": false,
  "remaining_mute_s": 0,
  "visual_escalation": false,
  "schema_version": "1.0"
}
```

### 4.2 3-Tier Classification & Clinician Action Matrix

| Alert Tier | Visual State | Audio Siren | Trigger Conditions | Debounce / Delay | Clinician Action |
| :---: | :---: | :---: | :--- | :---: | :--- |
| **Tier 1<br>(CRITICAL)** | Pulsing Red Banner & Ward Beacon | Continuous 85dB High-Pitch Emergency Siren | 1. $SpO_2 < 85\%$ or $HR < 20$ or $HR > 220$<br>2. $BP_{sys} < 60$ (hypotension)<br>3. $BP_{sys} > 200$ or $BP_{dia} > 120$ (hypertensive crisis)<br>4. Hardware ECG lead disconnect (`ecg_lead_ok=false`)<br>5. Sensor tamper / stuck zero variance<br>6. ML Confidence $> 0.90$ | **0 seconds** (Immediate unconditional bypass) | Immediate bedside resuscitation response. Crash cart alert. |
| **Tier 2<br>(WARNING)** | Solid Amber Banner | Periodic Chime (2 beeps every 30s) | ML Confidence between $0.50$ and $0.90$ (trajectory divergence from homeostatic attractor) | **3 consecutive ticks (300 ms)** anti-flicker debouncing | Bedside nursing review. Vital trend verification. |
| **Tier 3<br>(BASELINE)** | Clean Dark / Green Status | Silent | ML Confidence $< 0.50$ OR active cold start window | **3 consecutive ticks (300 ms)** anti-flicker debouncing | Routine monitoring. Zero alarm fatigue. |

### 4.3 Alarm Mute Clamping Policy (Option B Invariant)
1. **Server-Enforced Ceiling:** Clinicians may mute auditory alarms for bedside intervention via `POST /api/v1/alerts/{id}/mute`. The duration is **strictly capped server-side at 300 seconds (5 minutes)**. Requests specifying $>300$ seconds are clamped to 300s.
2. **Unsuppressable Visual Escalation:** While audio is silenced (`audio_muted = true`), `visual_escalation` remains permanently `true`. The UI must pulse red visually.
3. **Forced Unmute:** Once `remaining_mute_s` counts down to 0, if the patient remains in Tier 1, the siren is automatically and forcibly re-enabled.

---

## 5. Database Schema Design (PostgreSQL / SQLite)

To support real-time triage, time-series historical graphing, clinical auditing, and DPDP compliance, the database requires the following schema:

```
 ┌──────────────────────┐         ┌──────────────────────┐
 │        beds          │1       *│       patients       │
 │──────────────────────├─────────┤──────────────────────│
 │ bed_id (PK)          │         │ id (PK, UUID)        │
 │ room_number          │         │ mrn (Unique)         │
 │ max_capacity         │         │ full_name            │
 │ status               │         │ assigned_bed_id (FK) │
 └──────────┬───────────┘         └──────────┬───────────┘
            │1                               │1
            │                                │
            │*                               │*
 ┌──────────┴───────────┐         ┌──────────┴───────────┐
 │ patient_vitals_ts    │         │       alerts         │
 │──────────────────────│         │──────────────────────│
 │ id (BigInt PK)       │         │ id (UUID PK)         │
 │ bed_id (FK)          │         │ patient_id (FK)      │
 │ patient_id (FK)      │         │ bed_id (FK)          │
 │ ts (Timestamp UTC)   │         │ tier (Int)           │
 │ seq (Int)            │         │ reason (Text)        │
 │ hr, spo2, bp_sys...  │         │ attributing_vital    │
 │ raw_tier, tier       │         │ ml_confidence        │
 └──────────────────────┘         │ hard_breach          │
                                  │ triggered_at         │
                                  │ resolved_at          │
                                  └──────────┬───────────┘
                                             │1
                                             │
                                             │*
                                  ┌──────────┴───────────┐
                                  │    alert_mutes       │
                                  │──────────────────────│
                                  │ id (UUID PK)         │
                                  │ alert_id (FK)        │
                                  │ bed_id (FK)          │
                                  │ clinician_id         │
                                  │ duration_seconds     │
                                  │ expires_at           │
                                  │ forced_unmuted       │
                                  └──────────────────────┘
```

### 5.1 DDL Migration Script (`schema.sql`)

```sql
-- 1. Bed Infrastructure Table
CREATE TABLE beds (
    bed_id VARCHAR(16) PRIMARY KEY, -- e.g. 'bed-01', 'bed-10'
    room_number VARCHAR(32) NOT NULL,
    ward_name VARCHAR(64) DEFAULT 'ICU-Main',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. Patient Demographics & Bed Assignment Table
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mrn VARCHAR(64) UNIQUE NOT NULL, -- Medical Record Number
    full_name VARCHAR(128) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(16) NOT NULL,
    assigned_bed_id VARCHAR(16) REFERENCES beds(bed_id) ON DELETE SET NULL,
    primary_doctor_id VARCHAR(64) NOT NULL,
    admission_ts TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    discharge_ts TIMESTAMPTZ NULL,
    status VARCHAR(32) DEFAULT 'admitted' -- 'admitted', 'transferred', 'discharged'
);

CREATE INDEX idx_patients_bed ON patients(assigned_bed_id) WHERE status = 'admitted';

-- 3. Telemetry Time-Series Hypertable / Partition Table
CREATE TABLE patient_vitals_timeseries (
    id BIGSERIAL,
    ts TIMESTAMPTZ NOT NULL,
    bed_id VARCHAR(16) NOT NULL REFERENCES beds(bed_id),
    patient_id UUID NOT NULL REFERENCES patients(id),
    seq INT NOT NULL,
    hr REAL NOT NULL,
    spo2 REAL NOT NULL,
    bp_sys REAL NOT NULL,
    bp_dia REAL NOT NULL,
    temp REAL NULL,
    ecg_lead_ok BOOLEAN NOT NULL DEFAULT TRUE,
    drift_flag VARCHAR(16) NOT NULL DEFAULT 'none',
    is_cold_start BOOLEAN NOT NULL DEFAULT FALSE,
    raw_tier INT NOT NULL,
    confirmed_tier INT NOT NULL,
    ml_confidence REAL NOT NULL DEFAULT 0.0,
    attributing_vital VARCHAR(16) NOT NULL DEFAULT 'none',
    temp_staleness_ms REAL DEFAULT 0.0,
    PRIMARY KEY (ts, bed_id, id)
);

-- Optimization: Partition by ts or create standard b-tree composite indexes
CREATE INDEX idx_vitals_bed_ts ON patient_vitals_timeseries(bed_id, ts DESC);
CREATE INDEX idx_vitals_patient_ts ON patient_vitals_timeseries(patient_id, ts DESC);

-- 4. Alerts Table
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bed_id VARCHAR(16) NOT NULL REFERENCES beds(bed_id),
    patient_id UUID NOT NULL REFERENCES patients(id),
    tier INT NOT NULL CHECK (tier IN (1, 2)),
    reason TEXT NOT NULL,
    attributing_vital VARCHAR(16) NOT NULL,
    ml_confidence REAL NOT NULL,
    hard_breach BOOLEAN NOT NULL,
    triggered_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ NULL,
    acknowledged_by VARCHAR(64) NULL,
    acknowledged_at TIMESTAMPTZ NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active' -- 'active', 'acknowledged', 'resolved'
);

CREATE INDEX idx_alerts_active ON alerts(bed_id, status) WHERE status = 'active';

-- 5. Siren Mutes Ledger Table
CREATE TABLE alert_mutes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    bed_id VARCHAR(16) NOT NULL REFERENCES beds(bed_id),
    clinician_id VARCHAR(64) NOT NULL,
    muted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INT NOT NULL CHECK (duration_seconds <= 300),
    expires_at TIMESTAMPTZ NOT NULL,
    forced_unmuted BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_mutes_active ON alert_mutes(bed_id, is_active) WHERE is_active = TRUE;

-- 6. Cryptographically Chained Audit Ledger (DPDP 2023 Compliance)
CREATE TABLE audit_ledger (
    id BIGSERIAL PRIMARY KEY,
    prev_hash VARCHAR(64) NOT NULL,
    curr_hash VARCHAR(64) NOT NULL,
    ts TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(64) NOT NULL, -- 'ALERT_MUTE', 'TRANSFER_APPROVAL', 'EMERGENCY_ACCESS'
    bed_id VARCHAR(16) NOT NULL,
    clinician_id VARCHAR(64) NOT NULL,
    payload_json JSONB NOT NULL
);

CREATE INDEX idx_audit_ts ON audit_ledger(ts DESC);
```

### 5.2 Storage & Retention Strategy
- **Raw Telemetry Ticks (10 Hz):** Store in Redis rolling 10-second memory lists for real-time triage. In PostgreSQL/TimescaleDB, retain full 10 Hz ticks for **24 hours**.
- **Downsampled Rollups:** Run automated database workers every hour to downsample 24h+ data into 1-minute averages (`avg_hr`, `min_spo2`, `max_bp_sys`) for 30-day clinical trend charts.
- **Alerts & Audit Logs:** Retain permanently for medical liability and legal audits.

---

## 6. Frontend UI/UX Integration Guidelines

### 6.1 WebSocket Consumer (`/ws/monitor`)
The React frontend opens a persistent WebSocket connection upon dashboard mount:

```typescript
// types/telemetry.ts
export interface TriageDecision {
  bed_id: string;
  ts: string;
  tier: 1 | 2 | 3;
  confidence: number;
  reason: string;
  attributing_vital: "hr" | "spo2" | "bp_sys" | "none";
  drift_flag: "none" | "drift" | "tamper";
  is_cold_start: boolean;
  hard_breach: boolean;
  raw_tier: 1 | 2 | 3;
  audio_muted: boolean;
  remaining_mute_s: number;
  visual_escalation: boolean;
  schema_version: string;
}

// React Hook: useBedMonitor.ts
export function useBedMonitor(bedId: string) {
  const [latestTick, setLatestTick] = useState<TriageDecision | null>(null);

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.host}/ws/monitor?bed=${bedId}`);
    ws.onmessage = (event) => {
      const decision: TriageDecision = JSON.parse(event.data);
      setLatestTick(decision);
      
      // Audio siren control
      if (decision.tier === 1 && !decision.audio_muted) {
        AlarmSoundManager.playEmergencySiren();
      } else {
        AlarmSoundManager.stopEmergencySiren();
      }
    };
    return () => ws.close();
  }, [bedId]);

  return latestTick;
}
```

### 6.2 Frontend Display Rules

1. **Cold Start Badge (`is_cold_start: true`):**
   - Display amber outline badge: `[COLD START: BUFFERING VITAL WINDOW (Xs)]`.
   - Suppress ML anomaly warnings, but keep vitals visible.
2. **Tier-1 Critical Siren & Visual Escalation:**
   - Header banner flashes high-contrast pulsing red (`#DC2626`).
   - If `audio_muted: true`: Render mute countdown timer `[SIREN MUTED (Xs REMAINING)]` with orange badge, but **KEEP the red pulsing visual banner active**.
3. **Vital Attributing Badge:**
   - In Tier 2 and Tier 1 ML alerts, highlight the specific vital component card corresponding to `attributing_vital` with a flashing highlight border to immediately guide nursing attention to the culprit vital.
4. **ECG Lead Disconnect State:**
   - If `reason` contains `"CRITICAL: ECG lead disconnected"`, replace the ECG waveform chart with a flat dashed line and flashing label: `NO ECG SIGNAL - CHECK ELECTRODES`.

---

## 7. REST API Endpoints Reference

| Method | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/patients/{id}` | Clinical details including current vitals (`hr`, `spo2`, `bp_sys`, `bp_dia`, `temp`), active alert tier, and staleness. |
| `GET` | `/api/v1/patients/{id}/vitals/history?seconds=60` | Retrieve high-frequency historical ticks (up to 600 samples) for smooth waveform graph rendering. |
| `POST` | `/api/v1/alerts/{id}/mute` | Request temporary audio silencing. Payload: `{"duration_s": 120}`. Backend clamps to $\le 300\text{s}$. |
| `POST` | `/api/v1/alerts/{id}/ack` | Clinician acknowledges an alert. Writes forward-linked hash entry to `audit_ledger`. |
| `GET` | `/api/v1/ward/config` | Returns ward parameters including `max_beds`, `sampling_rate_hz`, and active connection status. |
