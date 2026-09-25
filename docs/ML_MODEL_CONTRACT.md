# PulseGuard-AI — ML Model & Ingestion Contract Specification

**Document Version:** 1.0  
**Target Audience:** Backend Developers, ML Engineers, Frontend Developers  
**Scope:** Telemetry Input Format, 1D-CNN Autoencoder Interface, Per-Channel Scaling, & Output Triage Contract

---

## 1. Executive Summary

This document specifies the exact data inputs, internal tensor shapes, scaling transformations, and output contracts for the **PulseGuard-AI 1D-CNN Telemetry Autoencoder** and **3-Tier Decision Engine**.

---

## 2. Model Input Specification (What the Model Receives)

### 2.1 Raw Telemetry Data Payload (Monitor → Gateway)

Each 10 Hz telemetry tick received from a bedside monitor has the following JSON structure:

```json
{
  "bed_id": "bed-01",
  "ts": "2026-09-25T18:38:37.123Z",
  "hr": 78,
  "spo2": 98,
  "bp_sys": 120,
  "bp_dia": 80,
  "temp": 36.8,
  "ecg_lead_ok": true,
  "seq": 10452
}
```

### 2.2 Feature Scaling Transformation

Raw biological vitals are min-max scaled to the $[0.0, 1.0]$ range using biological bounds before being passed to PyTorch:

$$\text{scaled}_c = \text{clip}\left(\frac{\text{raw}_c - \text{min}_c}{\text{max}_c - \text{min}_c}, 0.0, 1.0\right)$$

| Channel Index | Vital Parameter | Raw Unit | Min Bound ($\text{min}_c$) | Max Bound ($\text{max}_c$) |
|---|---|---|---|---|
| **Channel 0** | Heart Rate (`hr`) | bpm | 0.0 | 300.0 |
| **Channel 1** | SpO2 (`spo2`) | % | 0.0 | 100.0 |
| **Channel 2** | Systolic BP (`bp_sys`) | mmHg | 0.0 | 300.0 |

### 2.3 PyTorch Model Tensor Shape

The autoencoder accepts a 3D float32 PyTorch Tensor representing a 10-second rolling window (100 timesteps @ 10 Hz):

$$\mathbf{X} \in \mathbb{R}^{\text{batch\_size} \times 3 \times 100}$$

- **Dimension 0 (`batch_size`)**: Number of parallel window samples (e.g. 1 or 64)
- **Dimension 1 (`channels = 3`)**: `[0: HR, 1: SpO2, 2: BP_sys]`
- **Dimension 2 (`timesteps = 100`)**: Ordered chronologically (column 0 = oldest sample, column 99 = newest sample)

---

## 3. Model Output Specification (What the Model Produces)

### 3.1 Reconstructed Output Tensor

The PyTorch autoencoder (`TelemetryAutoencoder`) returns a reconstructed tensor with the exact same shape, strictly bounded in $[0.0, 1.0]$ via a final Sigmoid activation:

$$\hat{\mathbf{X}} \in \mathbb{R}^{\text{batch\_size} \times 3 \times 100}, \quad \hat{\mathbf{X}} \in [0.0, 1.0]$$

### 3.2 Per-Channel Reconstruction Error (MSE)

Reconstruction error is calculated **separately per vital channel** across the 100 timesteps (NOT averaged into a single scalar):

$$\text{MSE}_c = \frac{1}{100} \sum_{t=1}^{100} \left(X_{c,t} - \hat{X}_{c,t}\right)^2 \quad \text{for } c \in \{\text{hr}, \text{spo2}, \text{bp\_sys}\}$$

Output Tensor Shape: `(batch_size, 3)` where:
- Column 0: $\text{MSE}_{\text{hr}}$
- Column 1: $\text{MSE}_{\text{spo2}}$
- Column 2: $\text{MSE}_{\text{bp\_sys}}$

### 3.3 Normalized Anomaly Score & Factor Attribution

Each channel's raw MSE is normalized using multi-seed calibrated `offset` ($P_5$) and `scale` ($P_{95} - P_5$) constants saved in `autoencoder_v1.pt`:

$$\text{norm\_score}_c = \text{clip}\left(\frac{\text{MSE}_c - \text{offset}_c}{\text{scale}_c}, 0.0, 1.0\right)$$

- **Overall ML Confidence Score**: $\text{ml\_score} = \max\left(\text{norm\_score}_{\text{hr}}, \text{norm\_score}_{\text{spo2}}, \text{norm\_score}_{\text{bp\_sys}}\right) \in [0.0, 1.0]$
- **Factor Attribution**: `attributing_vital` = channel name with highest normalized score (`"hr"`, `"spo2"`, or `"bp_sys"`).

---

## 4. Final Triage Decision Output Contract (`TriageDecision`)

The `TriageService` evaluates hard physiological thresholds alongside ML scores and outputs a JSON `TriageDecision` payload to the backend & WebSocket broadcast:

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
  "schema_version": "1.0"
}
```

### Field Definitions:

| Field Name | Type | Description |
|---|---|---|
| `bed_id` | string | Bed identifier matching `^bed-(0[1-9]\|10)$` |
| `ts` | string (ISO-8601) | Timestamp of evaluated tick |
| `tier` | integer | Alert Tier: `1` (Catastrophic Red), `2` (Warning Yellow), `3` (Baseline Green) |
| `confidence` | float | Normalized ML anomaly score ($0.0 - 1.0$) |
| `reason` | string | Plain-language clinical reason with vital factor attribution |
| `attributing_vital`| string | Primary vital channel driving alert (`"hr"`, `"spo2"`, `"bp_sys"`, or `"none"`) |
| `drift_flag` | string | Sensor pre-filter status: `"none"`, `"drift"`, `"tamper"` |
| `is_cold_start` | boolean | `true` if bed buffer has $<100$ samples (cold start calibration mode) |
| `hard_breach` | boolean | `true` if a hard physiological safety threshold was breached |

---

## 5. Summary Matrix

```
[ Raw JSON Tick ] ──► [ Scale [0,1] ] ──► [ (3,100) Tensor ] ──► [ 1D-CNN Autoencoder ]
                                                                        │
                                                                        ▼
[ TriageDecision JSON ] ◄── [ 3-Tier Matrix ] ◄── [ Per-Channel MSE ] ◄─┘
```
