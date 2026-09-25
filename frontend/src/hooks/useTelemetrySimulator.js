import { useState, useEffect, useRef } from 'react';

// Initial 10 beds with realistic clinical profiles
const INITIAL_BEDS = [
  {
    bedId: '01',
    patientName: 'Eleanor Vance',
    initials: 'EV',
    age: 72,
    gender: 'Female',
    diagnosis: 'Post-CABG (Coronary Artery Bypass)',
    assignedDoctor: 'Dr. Sarah Chen, MD',
    admissionDate: '2026-09-23',
    codeStatus: 'Full Code',
    tier: 'normal',
    hr: 76,
    spo2: 98,
    bpSys: 122,
    bpDia: 78,
    rr: 16,
    temp: 36.8,
    anomalyScore: 0.12,
    factors: ['Sinus rhythm stable', 'SpO2 optimal at room air'],
    leadStatus: 'connected',
    acknowledged: true,
  },
  {
    bedId: '02',
    patientName: 'Marcus Sterling',
    initials: 'MS',
    age: 58,
    gender: 'Male',
    diagnosis: 'Acute Decompensated Heart Failure',
    assignedDoctor: 'Dr. Sarah Chen, MD',
    admissionDate: '2026-09-24',
    codeStatus: 'Full Code',
    tier: 'tier2', // Warning
    hr: 104,
    spo2: 92,
    bpSys: 148,
    bpDia: 96,
    rr: 22,
    temp: 37.4,
    anomalyScore: 0.58,
    factors: ['SpO2 downward drift (-3% over 180s)', 'Tachycardic trend with elevated SBP'],
    leadStatus: 'connected',
    acknowledged: false,
    alertTimestamp: '2 mins ago',
  },
  {
    bedId: '03',
    patientName: 'Harold Gomez',
    initials: 'HG',
    age: 64,
    gender: 'Male',
    diagnosis: 'Bilateral Pneumonia / ARDS',
    assignedDoctor: 'Dr. Marcus Vance, MD',
    admissionDate: '2026-09-22',
    codeStatus: 'Full Code',
    tier: 'normal',
    hr: 82,
    spo2: 96,
    bpSys: 118,
    bpDia: 74,
    rr: 18,
    temp: 37.9,
    anomalyScore: 0.28,
    factors: ['Vitals within baseline tolerance'],
    leadStatus: 'connected',
    acknowledged: true,
  },
  {
    bedId: '04',
    patientName: 'Julian Drake',
    initials: 'JD',
    age: 69,
    gender: 'Male',
    diagnosis: 'Septic Shock / Hypoxemia',
    assignedDoctor: 'Dr. Sarah Chen, MD',
    admissionDate: '2026-09-25',
    codeStatus: 'Full Code',
    tier: 'tier1', // CRITICAL ALERT
    hr: 138,
    spo2: 81, // Hard threshold breach <85%
    bpSys: 84,
    bpDia: 52,
    rr: 28,
    temp: 39.1,
    anomalyScore: 0.94,
    factors: [
      'SpO2 < 85% deterministic safety threshold breach',
      'Acute desaturation: -6.4% over 90s',
      'HR/BP covariance diverging (HR ↑ 138, MAP ↓ 62)',
      'Respiratory variability index exceeded +2.8σ'
    ],
    leadStatus: 'connected',
    acknowledged: false,
    alertTimestamp: 'Just now',
  },
  {
    bedId: '05',
    patientName: 'Rosa Martinez',
    initials: 'RM',
    age: 45,
    gender: 'Female',
    diagnosis: 'Post-operative Cholecystectomy',
    assignedDoctor: 'Dr. Marcus Vance, MD',
    admissionDate: '2026-09-25',
    codeStatus: 'Full Code',
    tier: 'normal',
    hr: 68,
    spo2: 99,
    bpSys: 116,
    bpDia: 72,
    rr: 14,
    temp: 36.6,
    anomalyScore: 0.08,
    factors: ['Post-anesthesia recovery uneventful'],
    leadStatus: 'connected',
    acknowledged: true,
  },
  {
    bedId: '06',
    patientName: 'Thomas Wright',
    initials: 'TW',
    age: 81,
    gender: 'Male',
    diagnosis: 'Severe COPD Exacerbation',
    assignedDoctor: 'Dr. Elena Rostova, MD',
    admissionDate: '2026-09-21',
    codeStatus: 'DNR / DNI',
    tier: 'tier2',
    hr: 98,
    spo2: 89,
    bpSys: 138,
    bpDia: 86,
    rr: 24,
    temp: 37.1,
    anomalyScore: 0.62,
    factors: ['Chronic hypoxemia baseline breached', 'Rapid tachypnea (RR 24)'],
    leadStatus: 'connected',
    acknowledged: false,
    alertTimestamp: '5 mins ago',
  },
  {
    bedId: '07',
    patientName: 'Aaliyah Khan',
    initials: 'AK',
    age: 33,
    gender: 'Female',
    diagnosis: 'Diabetic Ketoacidosis (DKA)',
    assignedDoctor: 'Dr. Sarah Chen, MD',
    admissionDate: '2026-09-24',
    codeStatus: 'Full Code',
    tier: 'normal',
    hr: 84,
    spo2: 97,
    bpSys: 112,
    bpDia: 70,
    rr: 18,
    temp: 37.0,
    anomalyScore: 0.18,
    factors: ['Insulin infusion stabilizing acidosis'],
    leadStatus: 'connected',
    acknowledged: true,
  },
  {
    bedId: '08',
    patientName: 'Robert Lang',
    initials: 'RL',
    age: 59,
    gender: 'Male',
    diagnosis: 'Observation / Telemetry artifact',
    assignedDoctor: 'Dr. Elena Rostova, MD',
    admissionDate: '2026-09-25',
    codeStatus: 'Full Code',
    tier: 'no-signal', // Gray
    hr: 0,
    spo2: 0,
    bpSys: 0,
    bpDia: 0,
    rr: 0,
    temp: 0,
    anomalyScore: 0.0,
    factors: ['Electrode lead-off detected (Lead II / V5 disconnected)'],
    leadStatus: 'disconnected',
    acknowledged: true,
  },
  {
    bedId: '09',
    patientName: 'Clara Oswald',
    initials: 'CO',
    age: 61,
    gender: 'Female',
    diagnosis: 'Subdural Hematoma (Neuro ICU Step-down)',
    assignedDoctor: 'Dr. Marcus Vance, MD',
    admissionDate: '2026-09-20',
    codeStatus: 'Full Code',
    tier: 'normal',
    hr: 72,
    spo2: 98,
    bpSys: 126,
    bpDia: 80,
    rr: 15,
    temp: 36.9,
    anomalyScore: 0.15,
    factors: ['ICP stable', 'Autonomic vitals intact'],
    leadStatus: 'connected',
    acknowledged: true,
  },
  {
    bedId: '10',
    patientName: 'David Zhang',
    initials: 'DZ',
    age: 50,
    gender: 'Male',
    diagnosis: 'Anterior STEMI s/p Stenting',
    assignedDoctor: 'Dr. Sarah Chen, MD',
    admissionDate: '2026-09-24',
    codeStatus: 'Full Code',
    tier: 'normal',
    hr: 74,
    spo2: 98,
    bpSys: 120,
    bpDia: 76,
    rr: 16,
    temp: 36.7,
    anomalyScore: 0.14,
    factors: ['Coronary reperfusion intact', 'No ST-segment shift'],
    leadStatus: 'connected',
    acknowledged: true,
  },
];

// Generate synthetic 10-minute historical telemetry data
export const generateHistoryData = (baselineHr = 75, baselineSpo2 = 98, baselineBpSys = 120, baselineBpDia = 80, isAnomaly = false) => {
  const points = [];
  const now = Date.now();
  const stepMs = 15000; // 15 sec interval = 40 points for 10 min

  for (let i = 40; i >= 0; i--) {
    const time = new Date(now - i * stepMs);
    const timeStr = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    
    // Gradual drift or sudden anomaly in the last 2 minutes
    let hrDrift = (Math.random() - 0.5) * 4;
    let spo2Drift = (Math.random() - 0.5) * 1;
    let bpSysDrift = (Math.random() - 0.5) * 4;
    let bpDiaDrift = (Math.random() - 0.5) * 2;

    if (isAnomaly && i < 10) {
      // Acute desaturation and tachycardia
      const severity = (10 - i) / 10;
      hrDrift += severity * 45;
      spo2Drift -= severity * 15;
      bpSysDrift -= severity * 30;
      bpDiaDrift -= severity * 20;
    }

    const hr = Math.round(Math.max(40, Math.min(180, baselineHr + hrDrift)));
    const spo2 = Math.round(Math.max(65, Math.min(100, baselineSpo2 + spo2Drift)));
    const bpSys = Math.round(Math.max(60, Math.min(220, baselineBpSys + bpSysDrift)));
    const bpDia = Math.round(Math.max(40, Math.min(130, baselineBpDia + bpDiaDrift)));
    
    points.push({
      time: timeStr,
      timestamp: time.getTime(),
      hr,
      spo2,
      bpSys,
      bpDia,
      // Threshold bands
      spo2DangerThreshold: 85,
      spo2WarningThreshold: 90,
      hrHighThreshold: 120,
      hrLowThreshold: 50,
    });
  }

  return points;
};

export const useTelemetrySimulator = () => {
  const [beds, setBeds] = useState(INITIAL_BEDS);
  const [ticks, setTicks] = useState(0);
  const [activeTier1Bed, setActiveTier1Bed] = useState(beds.find(b => b.tier === 'tier1' && !b.acknowledged) || null);

  // Generate real-time ECG line points (array of Y values for SVG waveform)
  const [waveforms, setWaveforms] = useState(() => {
    const initialMap = {};
    INITIAL_BEDS.forEach(b => {
      // 30 points representing ECG rhythm
      initialMap[b.bedId] = [20, 20, 20, 20, 18, 23, 20, 20, 6, 36, 12, 22, 20, 20, 20, 19, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20];
    });
    return initialMap;
  });

  // Ticks every 1000ms: updates live waveforms and subtle vital micro-fluctuations
  useEffect(() => {
    const interval = setInterval(() => {
      setTicks(t => t + 1);

      setBeds(prevBeds =>
        prevBeds.map(bed => {
          if (bed.tier === 'no-signal') return bed;

          // Subtle natural fluctuation (+/- 1 bpm, +/- 0.2% SpO2)
          const hrJitter = (Math.random() - 0.5) * 1.5;
          const newHr = Math.round(Math.max(45, Math.min(190, bed.hr + hrJitter)));

          return {
            ...bed,
            hr: newHr,
          };
        })
      );

      // Cycle ECG waveforms by shifting points to the left and pushing new ECG signal
      setWaveforms(prev => {
        const next = { ...prev };
        Object.keys(next).forEach(bedId => {
          const arr = [...next[bedId]];
          arr.shift();
          
          const bed = beds.find(b => b.bedId === bedId);
          if (!bed || bed.tier === 'no-signal') {
            // Flatline
            arr.push(20);
          } else {
            // Heartbeat rhythm generator based on ticks
            const beatPhase = (ticks + parseInt(bedId, 10) * 3) % 4;
            if (beatPhase === 0) {
              arr.push(Math.floor(Math.random() * 4) + 6); // QRS peak
            } else if (beatPhase === 1) {
              arr.push(Math.floor(Math.random() * 4) + 33); // S dip
            } else {
              arr.push(20 + (Math.random() - 0.5) * 2); // Baseline isoelectric line
            }
          }
          next[bedId] = arr;
        });
        return next;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [ticks, beds]);

  // Track active unacknowledged Tier 1 bed
  useEffect(() => {
    const unackedTier1 = beds.find(b => b.tier === 'tier1' && !b.acknowledged);
    setActiveTier1Bed(unackedTier1 || null);
  }, [beds]);

  // Clinician Acknowledges Tier 2 alert
  const acknowledgeTier2Alert = (bedId, clinicianName = 'Clinician') => {
    setBeds(prev => prev.map(b => {
      if (b.bedId === bedId) {
        return {
          ...b,
          acknowledged: true,
          acknowledgedBy: clinicianName,
          acknowledgedAt: new Date().toLocaleTimeString(),
        };
      }
      return b;
    }));
  };

  // Clinician Acknowledges Critical Tier 1 alert
  const acknowledgeTier1Alert = (bedId, clinicianName = 'Clinician') => {
    setBeds(prev => prev.map(b => {
      if (b.bedId === bedId) {
        return {
          ...b,
          acknowledged: true,
          acknowledgedBy: clinicianName,
          acknowledgedAt: new Date().toLocaleTimeString(),
          tier: 'tier2', // Step-down to warning status post-acknowledgment
        };
      }
      return b;
    }));
    setActiveTier1Bed(null);
  };

  // Anomaly Injection for live demo testing
  const injectHypoxia = (bedId = '02') => {
    setBeds(prev => prev.map(b => {
      if (b.bedId === bedId) {
        return {
          ...b,
          tier: 'tier1',
          spo2: 79,
          hr: 142,
          bpSys: 82,
          bpDia: 50,
          anomalyScore: 0.96,
          acknowledged: false,
          factors: [
            'SpO2 < 85% deterministic safety threshold breach',
            'Severe hypoxia triggered (SpO2: 79%)',
            'Tachycardic divergence: HR 142 bpm',
          ]
        };
      }
      return b;
    }));
  };

  const resetAllBeds = () => {
    setBeds(INITIAL_BEDS);
  };

  return {
    beds,
    setBeds,
    waveforms,
    activeTier1Bed,
    acknowledgeTier2Alert,
    acknowledgeTier1Alert,
    injectHypoxia,
    resetAllBeds,
  };
};

export default useTelemetrySimulator;
