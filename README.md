# PulseGuard-AI

### **Deterministic Edge-Triage & DPDP-Compliant Resilience Gateway for Critical Care IoT**
*Version 3.0 — Extended Hackathon Edition (NexHack 2.0)*

[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.x-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.x-646CFF.svg)](https://vitejs.dev/)
[![Redis](https://img.shields.io/badge/Redis-7.x-DC382D.svg)](https://redis.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16.x-336791.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Zero WAN Dependency](https://img.shields.io/badge/Safety%20Path-100%25%20Local%20Edge-success.svg)](#core-invariants)

---

> 🚨 **Hackathon MVP Notice**  
> PulseGuard-AI is an on-premise critical care monitoring prototype engineered for the **NexHack 2.0** hackathon. It demonstrates real-time physiological telemetry edge triage, noise-filtering alarm cascades, tamper-evident audit trails, and multi-tier hospital workflows. **It is not an autonomous diagnostic medical device and is not yet cleared for clinical production.**

---

## 📋 Table of Contents
- [The Problem](#-the-problem)
- [System Overview & Core Invariants](#-system-overview--core-invariants)
- [Key Features (v3.0 Scope Extension)](#-key-features-v30-scope-extension)
- [System Architecture](#-system-architecture)
- [3-Tier Alarm Cascade](#-3-tier-alarm-cascade)
- [Role-Based Access Control (RBAC)](#-role-based-access-control-rbac)
- [Security, DPDP Compliance & Cryptographic Audit](#-security-dpdp-compliance--cryptographic-audit)
- [Fault Tolerance & Resilience Matrix](#-fault-tolerance--resilience-matrix)
- [Backend API & Integration Contracts](#-backend-api--integration-contracts)
- [UI Demo & Previews](#-ui-demo--previews)
- [Quick Start & Installation](#-quick-start--installation)
- [Verification & Demo Scenarios](#-verification--demo-scenarios)
- [Troubleshooting & FAQs](#-troubleshooting--faqs)
- [Team & Acknowledgements](#-team--acknowledgements)

---

## ⚡ The Problem

1. **Alarm Fatigue is a Patient Safety Crisis:**  
   Between **72% and 99% of clinical ICU alarms are non-actionable false alarms** (NIH / AACN). Clinicians become desensitized to constant chirping, leading to delayed responses to genuine life-threatening crises. ECRI repeatedly ranks alarm fatigue on its *Top 10 Health Technology Hazards*.
2. **Fragility of Cloud-Dependent Healthcare Gateways:**  
   Many modern telemetry dashboards rely on cloud WAN connectivity for signal processing or alert routing. When network cables are severed, routers crash, or hospital WANs experience DDoS or outages, cloud-dependent platforms go dark.
3. **Data Privacy & Compliance Obligations (DPDP Act):**  
   Streaming unencrypted or identifiable high-frequency physiological vitals across remote networks poses severe compliance liabilities. Healthcare facilities need localized, privacy-preserving minimization architectures.

---

## 🎯 System Overview & Core Invariants

**PulseGuard-AI** is an on-premise hospital ward monitoring and resilience gateway that executes real-time multi-vital triage at the local network edge. 

### 🛡️ Core System Invariants
- **100% Local Critical Safety Path:** Zero WAN dependency for real-time detection, anomaly scoring, and alarm siren triggering. Local monitoring continues uninterrupted during complete external internet failure.
<<<<<<< HEAD
- **Fail-Safe Deterministic OR Logic:** Hard physiological thresholds (e.g., $SpO_2 < 85\%$, Extreme Tachycardia/Bradycardia) run alongside ML anomaly scoring with strict `OR` Boolean logic. **A machine learning model can NEVER suppress a hard-threshold vital breach.**
=======
- **Fail-Safe Deterministic OR Logic:** Hard physiological and hardware thresholds ($SpO_2 < 85\%$, HR $< 20$ or $> 220\,\text{bpm}$, Profound Hypotension with $\text{BP}_{\text{sys}} < 60\,\text{mmHg}$, Hypertensive Crisis with $\text{BP}_{\text{sys}} > 200\,\text{mmHg}$ or $\text{BP}_{\text{dia}} > 120\,\text{mmHg}$, and Hardware ECG Lead Disconnect $\text{ecg\_lead\_ok} == \text{false}$) evaluate unconditionally on every tick with zero hysteresis delay and run alongside ML anomaly scoring with strict `OR` Boolean logic. **A machine learning model can NEVER suppress a hard-threshold vital breach or lead disconnect.**
- **Deterministic Mute Clamping & Persistent Visual Escalation:** Auditory sirens can be temporarily paused for bedside clinical intervention, but the duration is strictly hard-capped server-side at a maximum of **300 seconds (5 minutes)** with forced automatic unmute. Visual alarm escalation remains **unsuppressable** and continuously prominent on all clinician dashboards while audio is silenced.
>>>>>>> origin/ml
- **Sub-5ms Scoring Target:** The critical edge scoring path executes in $<5\,\text{ms}$ on commodity edge hardware.
- **Fail-Closed for Security, Fail-Safe for Safety:** Authorization strictly fails closed at the backend layer, while the physiological alarm path falls back to resilient local ring buffers if upstream services crash.

---

## 🌟 Key Features (v3.0 Scope Extension)

Version 3.0 extends the deterministic v2.0 edge triage engine into a full **Hospital Workflow & Governance Layer**:

<<<<<<< HEAD
- 🏥 **Role-Specific Ward Dashboards:** Tailored interfaces with backend-enforced RBAC for **Doctor** and **Admin** users.
- 🔀 **Doctor-to-Doctor Patient Transfer Workflow:** Secure state-machine (`PENDING ➔ APPROVED / REJECTED / CANCELLED`) with database transactions preventing split-brain primary assignments.
- ⏳ **Break-Glass Emergency Temporary Access:** Admin-provisioned, time-bounded emergency patient access with mandatory clinical rationale, automated session expiration, and audit logging.
- 🧠 **Explainable Alert Context (XAI):** Real-time anomaly scores ($0.0 - 1.0$) with dynamic factor attribution (e.g., rapid $SpO_2$ decline coupled with HR acceleration) clearly distinguished from deterministic threshold violations.
- 📝 **Shift Handover Summaries & Clinical Notes:** Automated rolling-window patient handover summaries aggregating alerts, vitals, and physician progress and consultation logs.
- 🔕 **Server-Enforced Mute Clamping:** Anti-tamper alarm silencing capped at a maximum of **300 seconds (5 minutes)** with automatic siren unmute.
=======
- 🏥 **Role-Specific Ward Dashboards:** Tailored interfaces with backend-enforced RBAC for **Admin**, **Doctor**, and **Nurse** users.
- 🔀 **Doctor-to-Doctor Patient Transfer Workflow:** Secure state-machine (`PENDING ➔ APPROVED / REJECTED / CANCELLED`) with database transactions preventing split-brain primary assignments.
- ⏳ **Break-Glass Emergency Temporary Access:** Admin-provisioned, time-bounded emergency patient access with mandatory clinical rationale, automated session expiration, and audit logging.
- 🧠 **Explainable Alert Context (XAI):** Real-time anomaly scores ($0.0 - 1.0$) with dynamic factor attribution (e.g., rapid $SpO_2$ decline coupled with HR acceleration) clearly distinguished from deterministic threshold violations.
- 📝 **Shift Handover Summaries & Clinical Notes:** Automated rolling-window patient handover summaries aggregating alerts, vitals, and physician/nurse observation logs.
- 🔕 **Server-Enforced Mute Clamping & Persistent Visual Escalation:** Bedside auditory siren silencing is capped server-side at a maximum of **300 seconds (5 minutes)** with forced automatic unmute. Visual alarm escalation remains unsuppressable and persistently prominent across all dashboards throughout the muted period.
>>>>>>> origin/ml
- 🔗 **DPDP-Compliant SHA-256 Audit Ledger:** Cryptographically linked, tamper-evident audit chain verifying all sensitive actions.

---

## 🏗️ System Architecture

```
                          [ ICU Sensors / Synthetic Telemetry ]
                                            │
                                            ▼
                          [ FastAPI Edge Gateway (:8000) ]
                            │                           │
          (Volatile 10s FIFO) │                           │ (WebSocket Stream)
                            ▼                           ▼
                     [ Redis 7.x ]             [ React + Vite UI (:3000) ]
<<<<<<< HEAD
                            │                   (Doctor / Admin Panels)
=======
                            │                   (Doctor / Nurse / Admin Panels)
>>>>>>> origin/ml
                            ▼                           ▲
                 [ Feature Extraction ]                 │
                            │                           │
                            ▼                           │
              [ Local ML Anomaly Engine ]               │
            (1D-CNN Autoencoder + IsoForest)            │
                            │                           │
                            ▼                           │
           [ Hard Thresholds + ML (OR Logic) ] ─────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
     [ 3-Tier Alert Engine ]     [ PostgreSQL 16 Store ]
     - Tier 1: Siren             - Patient Records & RBAC
     - Tier 2: Escalation        - Immutable Audit Ledger
     - Tier 3: Noise Filter      - Transfer State Machine
```

---

## 🚨 3-Tier Alarm Cascade

PulseGuard-AI routes all incoming telemetry through a tiered triage cascade to eliminate alarm desensitization while guaranteeing patient safety:

| Tier | Classification | Trigger Condition | System Action | Clinician Workflow |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1** | **Critical Alarm** | Hard threshold breach ($SpO_2 < 85\%$, $\text{HR} < 20$ or $> 220\,\text{bpm}$, $\text{BP}_{\text{sys}} < 60\,\text{mmHg}$, $\text{BP}_{\text{sys}} > 200\,\text{mmHg}$ or $\text{BP}_{\text{dia}} > 120\,\text{mmHg}$, Hardware Lead Disconnect $\text{ecg\_lead\_ok} == \text{false}$) **OR** ML Anomaly Score $> 0.90$ | Instant local audio/visual siren; pushes immediate WebSocket broadcast | **Unsuppressable Visual Escalation.** Visual alarm banner cannot be dismissed by UI. Auditory siren can be temporarily silenced for bedside care, strictly hard-capped server-side to $\le 300\text{s}$ with mandatory auto-unmute. |
| **Tier 2** | **Warning / Drift** | 2+ vitals drifting simultaneously; ML Anomaly Score $0.50 - 0.90$ | Emits high-priority visual alert banner on assigned clinician’s dashboard | Requires active clinician acknowledgement with auditable timestamp. |
| **Tier 3** | **Transient Noise** | Single brief spike / artifact; ML Anomaly Score $< 0.50$ | Suppressed from audible siren; incremented in noise-reduction counter | Logged silently to audit store; available for trend analytics. |

---

## 👥 Role-Based Access Control (RBAC)

Authorization is strictly enforced **server-side** at the FastAPI endpoint layer—hidden UI buttons never substitute for backend security:

| Capability | Admin | Doctor |
| :--- | :---: | :---: |
| **View Ward Overview** | ✅ Full Ward | Assigned (or Ward Oversight) |
| **Live Vital Waveforms & Charts** | ✅ Admin View | ✅ Assigned Patients |
| **Acknowledge Alarms** | ❌ (Administrative) | ✅ Tier 1 & Tier 2 |
| **Submit Clinical Notes** | ❌ | ✅ Doctor Notes & Consults |
| **Initiate Patient Transfer** | ❌ | ✅ |
| **Approve / Reject Transfers** | ✅ | ❌ |
| **Grant Emergency Access** | ✅ | ❌ |
| **View Audit Trail & Tamper Status** | ✅ Full Cryptographic Log | ❌ |
| **Ward Analytics & Noise Metrics** | ✅ Full Analytics | 📊 Clinical Metrics |

---

## 🔒 Security, DPDP Compliance & Cryptographic Audit

PulseGuard-AI incorporates the principles of India's **Digital Personal Data Protection (DPDP) Act 2023** and global zero-trust healthcare standards:

1. **Data Minimization:** High-frequency waveform telemetry payloads carry only ephemeral bed/device IDs. Direct Patient Identifiable Information (PII) is isolated in the relational database.
2. **Volatile In-Memory Processing:** Raw multi-vital arrays reside exclusively in volatile Redis 10-second FIFO sliding windows and are never unnecessarily written to disk.
3. **Cryptographically Chained Audit Ledger:**  
   Every sensitive clinician action (alert acknowledgement, transfer approval, emergency break-glass grant, alarm mute) generates an immutable, forward-linked hash entry:
   $$\text{Hash}_n = \text{SHA-256}\left(\text{Hash}_{n-1} + \text{Timestamp} + \text{Action} + \text{BedID} + \text{ClinicianID}\right)$$
   *Any post-hoc modification or record deletion breaks the hash chain, triggering an immediate alert on the Admin Dashboard.*
4. **Zero-Trust Model Deserialization:** No pickle deserialization is used anywhere in the inference path. Model weights are stored in PyTorch checkpoint format loaded strictly with `weights_only=True`, and calibration parameters are stored in transparent JSON (`calibration_v1.json`), preventing arbitrary code execution vulnerabilities.

---

## 🛠️ Fault Tolerance & Resilience Matrix

The edge gateway is engineered to degrade gracefully during hardware or network failures:

| Subsystem Failure | Fail-Safe Behavior | Safety Guarantee |
| :--- | :--- | :--- |
| **WAN / Cloud Outage** | Gateway continues local telemetry triage, ML scoring, and bedside sirens; queues cloud sync locally. | **Zero interruption** to ward patient monitoring. |
| **Redis Crash** | Coordinated fallback to in-process `collections.deque` buffers; emits structured `[ring_buffer_fallback_event]`. **Blast radius:** volatile 10-second rolling windows are wiped for **ALL beds** sharing that Redis instance simultaneously, causing ML-based Tier 2/3 anomaly scoring to go **dark** across the ward during the ~10s refill window (100 ticks @ 10Hz). | **Zero gap in patient safety.** Deterministic hard-threshold evaluation ($SpO_2 < 85\%$, HR extremes, BP hypotension/crisis, lead disconnect) continues unconditionally per tick with 0 delay. Catastrophic Tier-1 sirens remain 100% active throughout the Redis crash and refill window. |
| **PostgreSQL Crash** | Events buffer in memory and flush upon reconnection with a marked sequence gap. | Critical alarm sirens **never deadlock** on database write timeouts. |
| **Sensor Disconnect / Packet Drop** | Sequence gap or timeout detected after 3 missed frames; displays explicit **`NO SIGNAL`** badge. | Prevents silent failure or misleading "normal/green" vital states. |
| **WebSocket Disconnect** | Backend monitoring and siren routines persist; frontend displays banner and auto-reconnects with state rehydration. | Audio alarm triggers even if browser window freezes or closes. |
| **Transfer Split-Brain** | Database transaction wrapping assignment revocation and new grant. | Ensures **exactly one** primary doctor is responsible for a patient at any moment. |

---

## 🔌 Backend API & Integration Contracts

The RESTful API is structured for high throughput and modularity:

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/login` | Authenticate clinician/admin and issue JWT | Public |
| `GET` | `/me` | Retrieve active authenticated session and permissions | Clinician / Admin |
| `GET` | `/patients` | List accessible patients based on role and assignment | Role + Assignment |
| `GET` | `/patients/{id}` | Retrieve patient clinical summary, multi-vital history (`hr`, `spo2`, `bp_sys`, `bp_dia`, `temp`), active alerts, and attribution | Role + Assignment |
| `POST` | `/patients/{id}/notes` | Post clinical progress notes or consults | Role Permitted |
| `POST` | `/transfers` | Submit a doctor-to-doctor transfer request | Doctor |
| `GET` | `/transfers?status=pending` | List pending transfer requests awaiting admin approval | Admin |
| `POST` | `/transfers/{id}/approve` | Approve transfer request (atomic database transaction) | Admin |
| `POST` | `/transfers/{id}/reject` | Reject transfer request with recorded reason | Admin |
| `POST` | `/emergency-access` | Grant temporary, time-bounded emergency access | Admin |
| `DELETE`| `/emergency-access/{id}` | Revoke active emergency grant early | Admin |
| `GET` | `/audit-logs` | Retrieve cryptographically chained audit ledger | Admin |
| `GET` | `/analytics/ward` | Ward metrics: active beds, alarm breakdown, noise reduction % | Admin / Authorized |
| `WS` | `/ws/monitor` | Full-duplex WebSocket stream for live waveforms & alerts | Authenticated Token |

---

## 📸 UI Demo & Previews

The modern React frontend features an interactive, dark-mode ICU command dashboard:

<p align="center">
  <img src="Assets/Quiet-Dashboard.jpeg" alt="PulseGuard Normal Monitoring Mode" width="85%" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
  <br><em>Figure 1: Baseline Ward Monitoring with Active Noise Suppression Counter & Multi-Bed Vitals.</em>
</p>

<p align="center">
  <img src="Assets/Tier-1.png" alt="PulseGuard Tier 1 Critical Alert" width="85%" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
  <br><em>Figure 2: Tier-1 Critical Siren Firing (Unsuppressable Emergency Alarm with Vital Waveforms).</em>
</p>

<p align="center">
  <img src="Assets/Cloud.png" alt="PulseGuard Cloud Outage Graceful Degradation" width="85%" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.4);">
  <br><em>Figure 3: Simulated WAN Loss Mode — Local-First Edge Gateway Continues Real-Time Ward Triage.</em>
</p>

---

## 🚀 Quick Start & Installation

### Prerequisites
- **Git** installed on your workstation.
- **Python 3.11 or 3.12** *(Recommended — pre-compiled binary wheels for `scikit-learn`, `numpy`, and `asyncpg` are available).*
- **Node.js 18+ & npm** (for the Vite + React frontend).
- *(Optional)* **Docker & Docker Compose** for containerized ward host deployment.

> **Configuration Note:** Ward bed capacity is fully configurable via the `MAX_BEDS` setting/environment variable (e.g. `export MAX_BEDS=20`, defaulting to 10) and is not a hard architectural ceiling. Dynamic telemetry schemas and ingestion validators automatically scale to match the configured limit.
---

### Option A: 1-Click Unified Launch (Recommended)

The automated root runner checks dependencies, creates/activates virtual environments, cleans conflicting ports, boots FastAPI & Vite in parallel, and opens your browser:

#### 🪟 Windows (Command Prompt or PowerShell)
```cmd
.\start.bat
```
*(Or in PowerShell: `.\start.ps1`)*

#### 🍎 macOS / 🐧 Linux
```bash
chmod +x start.sh
./start.sh
```

#### 💻 Cross-Platform (Any Operating System)
```bash
python run.py
```
> The launcher will automatically open **http://localhost:3000** in your browser with live backend connection at **http://localhost:8000**.

To cleanly stop all servers and free ports `8000` & `3000`, run `stop.bat` (Windows) or `./stop.sh` (macOS/Linux).

---

### Option B: Manual Step-by-Step Setup

#### 1. Setup Backend (FastAPI)
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Start FastAPI server on port 8000
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Setup Frontend (React + Vite)
```bash
# In a new terminal window, navigate to frontend directory
cd frontend

# Install npm packages
npm install

# Start Vite dev server on port 3000
npm run dev
```

---

### Option C: Production Docker Compose Deployment

To deploy the full containerized on-premise ward environment:

```bash
docker-compose up --build -d
docker-compose ps
```

---

## 🧪 Verification & Demo Scenarios

You can validate key v3.0 requirements and fault behaviors live in the dashboard or via automated tests:

1. **Automated Backend Test Suite:**
   ```bash
   cd backend
   pytest tests/test_pulseguard.py -v
   ```
2. **Simulate a Tier-1 Critical Event (Hypoxia):**  
   Use the built-in **Demo Injector** on the dashboard to trigger acute desaturation ($SpO_2 < 85\%$). Observe immediate unsuppressable siren trigger and waveform deflection.
3. **Simulate Cloud/WAN Disconnect:**  
   Disconnect external Wi-Fi or trigger WAN outage mode. Notice the dashboard displays **Offline Sync Queued** while local vitals and audio sirens remain 100% active.
4. **Test Mute Abuse Clamping:**  
   Click the siren mute button. Observe the 5-minute countdown timer and note that visual alarm escalation remains unsuppressable and prominently active while audio is silenced; notice that after 300 seconds, the system automatically forces an unmute if vitals remain in critical condition.
5. **Doctor-to-Doctor Transfer:**  
   Log in as Doctor, request patient transfer to another physician. Log in as Admin to approve the request, and observe the instant atomic handover in the active patient grid.
6. **Audit Ledger Verification:**  
   Open the Admin Audit panel to inspect the continuous cryptographic SHA-256 hash chain linking all clinician actions.

---

## ❓ Troubleshooting & FAQs

### Q1: `Error: pg_config executable not found` or C-extension wheel build error
- **Cause:** Using Python 3.13 before pre-built wheels are published on PyPI, or missing PostgreSQL development headers.
- **Fix:** Use **Python 3.11 or 3.12**. PulseGuard supports SQLite (`aiosqlite`) out-of-the-box, meaning PostgreSQL headers are not strictly required for local standalone execution.

### Q2: Port 8000 or 3000 is already in use
- **Fix:** Execute `stop.bat` (Windows) or `./stop.sh` (Linux/macOS) to terminate lingering background processes occupying those ports.

### Q3: Do I need external Redis and PostgreSQL instances running?
- **Answer:** **No.** PulseGuard is engineered with zero-dependency standalone fallbacks. If Redis or PostgreSQL are unavailable, the gateway seamlessly falls back to an in-process volatile ring buffer and local SQLite store.

---

## 👥 Team: F_society

Developed with passion for **NexHack 2.0**:
- **Parth Patil**
- **Sarvesh**
- **Wasim**
- **Mayuresh**
- **Nishant**

---

## 📄 License
This project is released under the **MIT License** for hackathon evaluation and open medical technology research.
