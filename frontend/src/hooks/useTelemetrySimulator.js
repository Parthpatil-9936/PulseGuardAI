import { useState, useEffect, useRef, useCallback } from 'react';

const API_BASE = 'http://127.0.0.1:8000';

/**
 * Maps a raw bed+patient record from the backend into the UI shape expected
 * by BedTile, WardDashboard, PatientRoster, etc.
 */
function mapBedToUi(bed, patient, assignment) {
  const demo = patient?.demographics || {};
  const vitals = bed.vitals || {};

  // Derive triage tier from vitals (mirrors backend deterministic logic)
  let tier = 'normal';
  if (!bed.vitals || bed.status === 'no_signal' || vitals.lead_status === 'disconnected') {
    tier = 'no-signal';
  } else if (vitals.tier === 'tier1' || vitals.anomaly_score >= 0.85) {
    tier = 'tier1';
  } else if (vitals.tier === 'tier2' || vitals.anomaly_score >= 0.50) {
    tier = 'tier2';
  }

  const name = demo.name || `Bed ${bed.id}`;
  const initials = demo.initials || name.split(' ').map(p => p[0]).join('').slice(0, 2).toUpperCase();

  return {
    bedId: bed.id,
    patientId: patient?.id || null,
    patientName: name,
    initials,
    age: demo.age || 'â€”',
    gender: demo.gender || 'â€”',
    diagnosis: demo.diagnosis || 'â€”',
    codeStatus: demo.code_status || 'â€”',
    assignedDoctor: assignment?.doctor_name || 'â€”',
    assignedDoctorId: assignment?.doctor_id || null,
    admissionDate: patient?.created_at ? new Date(patient.created_at).toLocaleDateString() : 'â€”',
    tier,
    // Live vitals from backend telemetry; default to 0 when no signal
    hr: vitals.hr ?? 0,
    spo2: vitals.spo2 ?? 0,
    bpSys: vitals.bp_sys ?? 0,
    bpDia: vitals.bp_dia ?? 0,
    rr: vitals.rr ?? 0,
    temp: vitals.temp ?? 0,
    anomalyScore: vitals.anomaly_score ?? 0,
    factors: vitals.factors || [],
    leadStatus: vitals.lead_status || (bed.status === 'no_signal' ? 'disconnected' : 'connected'),
    acknowledged: vitals.acknowledged ?? true,
    alertTimestamp: vitals.alert_timestamp || null,
    wardStatus: bed.status,
  };
}

/**
 * Generate synthetic historical telemetry for the sparkline chart.
 * Used only as a placeholder until real historical data is fetched from the backend.
 */
export const generateHistoryData = (
  baselineHr = 75,
  baselineSpo2 = 98,
  baselineBpSys = 120,
  baselineBpDia = 80,
  isAnomaly = false
) => {
  const points = [];
  const now = Date.now();
  const stepMs = 15000;

  for (let i = 40; i >= 0; i--) {
    const time = new Date(now - i * stepMs);
    const timeStr = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    let hrDrift = (Math.random() - 0.5) * 4;
    let spo2Drift = (Math.random() - 0.5) * 1;
    let bpSysDrift = (Math.random() - 0.5) * 4;
    let bpDiaDrift = (Math.random() - 0.5) * 2;

    if (isAnomaly && i < 10) {
      const severity = (10 - i) / 10;
      hrDrift += severity * 45;
      spo2Drift -= severity * 15;
      bpSysDrift -= severity * 30;
      bpDiaDrift -= severity * 20;
    }

    points.push({
      time: timeStr,
      timestamp: time.getTime(),
      hr: Math.round(Math.max(40, Math.min(180, baselineHr + hrDrift))),
      spo2: Math.round(Math.max(65, Math.min(100, baselineSpo2 + spo2Drift))),
      bpSys: Math.round(Math.max(60, Math.min(220, baselineBpSys + bpSysDrift))),
      bpDia: Math.round(Math.max(40, Math.min(130, baselineBpDia + bpDiaDrift))),
      spo2DangerThreshold: 85,
      spo2WarningThreshold: 90,
      hrHighThreshold: 120,
      hrLowThreshold: 50,
    });
  }
  return points;
};

/**
 * Primary telemetry hook.
 *
 * Lifecycle:
 *  1. On mount â€” fetch beds + patients + assignments from the backend.
 *  2. Poll the backend every 5 s for fresh vitals/telemetry.
 *  3. Run local ECG waveform animation at 1 s intervals (purely cosmetic).
 */
export const useTelemetrySimulator = () => {
  const [beds, setBeds] = useState([]);
  const [ticks, setTicks] = useState(0);
  const [activeTier1Bed, setActiveTier1Bed] = useState(null);
  const [loading, setLoading] = useState(true);

  const [waveforms, setWaveforms] = useState({});

  // --------------------------------------------------------------------------
  // Helper â€” auth headers
  // --------------------------------------------------------------------------
  const getHeaders = () => {
    const token = localStorage.getItem('pulseguard_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  // --------------------------------------------------------------------------
  // Fetch beds + patient demographics + assignments from backend
  // --------------------------------------------------------------------------
  const fetchBeds = useCallback(async () => {
    const token = localStorage.getItem('pulseguard_token');
    if (!token) return;

    try {
      const [bedsRes, patientsRes, assignmentsRes, usersRes] = await Promise.all([
        fetch(`${API_BASE}/beds`, { headers: getHeaders() }),
        fetch(`${API_BASE}/patients`, { headers: getHeaders() }),
        fetch(`${API_BASE}/assignments`, { headers: getHeaders() }).catch(() => ({ ok: false })),
        fetch(`${API_BASE}/auth/users`, { headers: getHeaders() }).catch(() => ({ ok: false })),
      ]);

      if (!bedsRes.ok) return;

      const rawBeds = await bedsRes.json();
      const rawPatients = patientsRes.ok ? await patientsRes.json() : [];
      const rawAssignments = assignmentsRes.ok ? await assignmentsRes.json() : [];
      const rawUsers = usersRes.ok ? await usersRes.json() : [];

      // Build lookup maps
      const patientMap = Object.fromEntries(rawPatients.map(p => [p.id, p]));
      const userMap = Object.fromEntries(rawUsers.map(u => [u.id, u]));

      // Build assignment map: patient_id -> { doctor_id, doctor_name }
      const assignmentMap = {};
      for (const a of rawAssignments) {
        if (a.status === 'active') {
          const doctor = userMap[a.doctor_id];
          assignmentMap[a.patient_id] = {
            doctor_id: a.doctor_id,
            doctor_name: doctor?.name || a.doctor_id,
          };
        }
      }

      const mapped = rawBeds.map(bed => {
        const patient = bed.patient_id ? patientMap[bed.patient_id] : null;
        const assignment = patient ? assignmentMap[patient.id] : null;
        return mapBedToUi(bed, patient, assignment);
      });

      setBeds(mapped);

      // Initialise waveform buffers for any new beds
      setWaveforms(prev => {
        const next = { ...prev };
        mapped.forEach(b => {
          if (!next[b.bedId]) {
            next[b.bedId] = Array(30).fill(20);
          }
        });
        return next;
      });

      setLoading(false);
    } catch (err) {
      console.warn('Failed to fetch beds from backend:', err);
      setLoading(false);
    }
  }, []);

  // Initial fetch and 5-second polling
  useEffect(() => {
    fetchBeds();
    const poll = setInterval(fetchBeds, 5000);
    return () => clearInterval(poll);
  }, [fetchBeds]);

  // --------------------------------------------------------------------------
  // ECG waveform animation â€” runs at 1 Hz regardless of data source
  // --------------------------------------------------------------------------
  useEffect(() => {
    const interval = setInterval(() => {
      setTicks(t => t + 1);

      setWaveforms(prev => {
        const next = { ...prev };
        Object.keys(next).forEach(bedId => {
          const arr = [...next[bedId]];
          arr.shift();
          const bed = beds.find(b => b.bedId === bedId);
          if (!bed || bed.tier === 'no-signal') {
            arr.push(20); // flatline
          } else {
            const bedOffset = (bedId || '').split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
            const beatPhase = (ticks + bedOffset * 3) % 4;
            if (beatPhase === 0) {
              arr.push(Math.floor(Math.random() * 4) + 6);   // QRS peak
            } else if (beatPhase === 1) {
              arr.push(Math.floor(Math.random() * 4) + 33);  // S dip
            } else {
              arr.push(20 + (Math.random() - 0.5) * 2);      // isoelectric line
            }
          }
          next[bedId] = arr;
        });
        return next;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [ticks, beds]);

  // --------------------------------------------------------------------------
  // Track unacknowledged Tier 1 beds
  // --------------------------------------------------------------------------
  useEffect(() => {
    const unacked = beds.find(b => b.tier === 'tier1' && !b.acknowledged);
    setActiveTier1Bed(unacked || null);
  }, [beds]);

  // --------------------------------------------------------------------------
  // Acknowledge Tier 2 â€” calls backend then re-fetches
  // --------------------------------------------------------------------------
  const acknowledgeTier2Alert = async (bedId, clinicianName = 'Clinician') => {
    // Optimistic local update
    setBeds(prev => prev.map(b =>
      b.bedId === bedId
        ? { ...b, acknowledged: true, acknowledgedBy: clinicianName, acknowledgedAt: new Date().toLocaleTimeString() }
        : b
    ));

    try {
      const bed = beds.find(b => b.bedId === bedId);
      const alertRes = await fetch(`${API_BASE}/alerts?bed_id=${bedId}&status=active`, { headers: getHeaders() });
      if (alertRes.ok) {
        const alerts = await alertRes.json();
        if (alerts.length > 0) {
          await fetch(`${API_BASE}/alerts/${alerts[0].id}/acknowledge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getHeaders() },
            body: JSON.stringify({ note: `Acknowledged by ${clinicianName}` }),
          });
        }
      }
    } catch (err) {
      console.warn('Alert acknowledgment backend call failed:', err);
    }
    await fetchBeds();
  };

  // --------------------------------------------------------------------------
  // Acknowledge Tier 1 â€” step-down to tier2 + backend call
  // --------------------------------------------------------------------------
  const acknowledgeTier1Alert = async (bedId, clinicianName = 'Clinician') => {
    setBeds(prev => prev.map(b =>
      b.bedId === bedId
        ? { ...b, acknowledged: true, acknowledgedBy: clinicianName, acknowledgedAt: new Date().toLocaleTimeString(), tier: 'tier2' }
        : b
    ));
    setActiveTier1Bed(null);

    try {
      const alertRes = await fetch(`${API_BASE}/alerts?bed_id=${bedId}&status=active`, { headers: getHeaders() });
      if (alertRes.ok) {
        const alerts = await alertRes.json();
        if (alerts.length > 0) {
          await fetch(`${API_BASE}/alerts/${alerts[0].id}/acknowledge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getHeaders() },
            body: JSON.stringify({ note: `TIER1 acknowledged by ${clinicianName}` }),
          });
        }
      }
    } catch (err) {
      console.warn('Tier1 acknowledgment backend call failed:', err);
    }
    await fetchBeds();
  };

  return {
    beds,
    setBeds,
    waveforms,
    activeTier1Bed,
    loading,
    acknowledgeTier2Alert,
    acknowledgeTier1Alert,
    refreshBeds: fetchBeds,
    // Legacy stubs â€” no-ops now that data is real
    injectHypoxia: () => {},
    resetAllBeds: fetchBeds,
  };
};

export default useTelemetrySimulator;

