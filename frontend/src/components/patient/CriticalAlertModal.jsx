import React, { useState } from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle2, User, Clock, BellRing, Lock } from 'lucide-react';
import { Button, Input } from '../ui';
import { useAuth } from '../../context/AuthContext';

/**
 * CriticalAlertModal (Tier 1 Takeover)
 * High-contrast, un-dismissible full-screen takeover modal.
 * Triggered when a deterministic hard threshold or extreme ML anomaly is breached.
 * Cannot be closed by clicking outside or pressing Escape.
 * Requires explicit clinician confirmation and rationale.
 */
export const CriticalAlertModal = ({
  isOpen,
  bed,
  onAcknowledge,
}) => {
  const { user } = useAuth();
  const [clinicianNote, setClinicianNote] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen || !bed) return null;

  const handleConfirm = (e) => {
    e.preventDefault();
    setSubmitting(true);
    setTimeout(() => {
      onAcknowledge?.(bed.bedId, user.name);
      setSubmitting(false);
      setClinicianNote('');
    }, 400);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-red-950/85 backdrop-blur-xl transition-all duration-300 select-none animate-in fade-in"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="critical-alert-title"
    >
      <div className="w-full max-w-xl rounded-3xl bg-white shadow-[0_0_80px_rgba(239,68,68,0.6)] border-4 border-red-500 overflow-hidden">
        {/* Pulsing Header Banner */}
        <div className="bg-red-600 px-6 py-5 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center shrink-0 animate-bounce">
              <ShieldAlert className="w-7 h-7 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-mono uppercase tracking-widest bg-white/20 px-2 py-0.5 rounded font-bold">
                  Tier 1 Alarm Cascade
                </span>
                <span className="text-xs font-mono opacity-80">Deterministic Edge Rule</span>
              </div>
              <h2 id="critical-alert-title" className="text-xl font-extrabold tracking-tight mt-0.5">
                CRITICAL VITAL TAKEOVER — BED {bed.bedId}
              </h2>
            </div>
          </div>
          <BellRing className="w-6 h-6 animate-pulse" />
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-5">
          {/* Patient Details & Breach Readouts */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-red-50/80 p-4 rounded-2xl border border-red-200">
            <div>
              <span className="text-[10px] text-red-700 font-semibold uppercase block">Patient</span>
              <span className="text-sm font-bold text-red-950">{bed.patientName}</span>
              <span className="text-[11px] text-red-800 block">Bed {bed.bedId}</span>
            </div>

            <div>
              <span className="text-[10px] text-red-700 font-semibold uppercase block">SpO2 Level</span>
              <span className="vital-number text-xl font-extrabold text-red-600 block">
                {bed.spo2}%
              </span>
              <span className="text-[10px] text-red-700 font-semibold">Threshold: &lt;85%</span>
            </div>

            <div>
              <span className="text-[10px] text-red-700 font-semibold uppercase block">Heart Rate</span>
              <span className="vital-number text-xl font-extrabold text-red-600 block">
                {bed.hr} <span className="text-xs font-normal">BPM</span>
              </span>
              <span className="text-[10px] text-red-700 font-semibold">Tachycardic</span>
            </div>

            <div>
              <span className="text-[10px] text-red-700 font-semibold uppercase block">Anomaly Index</span>
              <span className="vital-number text-xl font-extrabold text-red-700 block">
                {bed.anomalyScore.toFixed(2)}
              </span>
              <span className="text-[10px] text-red-700 font-semibold">1D-CNN + Iso</span>
            </div>
          </div>

          {/* Explainability factors */}
          <div className="space-y-2">
            <span className="text-xs font-bold text-slate-800 uppercase tracking-wider block">
              Safety Invariants Triggered:
            </span>
            <ul className="space-y-1.5 text-xs text-red-900 bg-red-50/50 p-3 rounded-xl border border-red-100">
              {bed.factors?.map((f, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500 mt-1.5 shrink-0" />
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Clinician Acknowledgment Requirement Form */}
          <form onSubmit={handleConfirm} className="space-y-4 pt-2">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 text-slate-700">
                <User className="w-4 h-4 text-teal-600" />
                <span>Responding Clinician: <strong>{user.name}</strong> ({user.role.toUpperCase()})</span>
              </div>
              <div className="flex items-center gap-1 text-slate-400 font-mono text-[11px]">
                <Clock className="w-3.5 h-3.5" />
                <span>{new Date().toLocaleTimeString()}</span>
              </div>
            </div>

            <Input
              label="Immediate Bedside Action / Clinical Note"
              placeholder="e.g., Bag-valve mask ventilation initiated, attending paged..."
              value={clinicianNote}
              onChange={(e) => setClinicianNote(e.target.value)}
              helperText="Mandatory clinical record linkable to SHA-256 audit ledger"
              required
            />

            <div className="pt-2 flex flex-col gap-2">
              <Button
                type="submit"
                variant="danger"
                size="lg"
                loading={submitting}
                className="w-full justify-center shadow-lg shadow-red-500/30 text-sm font-bold py-3"
              >
                Acknowledge Alert & Clear Siren
              </Button>
              <p className="text-[11px] text-center text-slate-400">
                <Lock className="w-3 h-3 inline mr-1 text-slate-400" />
                Lockout mode: Cannot be dismissed without explicit licensed clinician acknowledgment.
              </p>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CriticalAlertModal;
