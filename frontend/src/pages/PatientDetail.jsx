import React, { useState, useMemo } from 'react';
import { 
  ArrowLeft, 
  HeartPulse, 
  Activity, 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowLeftRight, 
  Clock, 
  User, 
  Calendar, 
  FileText, 
  Sparkles, 
  Stethoscope, 
  BellRing 
} from 'lucide-react';
import { Button, Badge, Card, CardHeader, CardTitle, CardContent } from '../components/ui';
import { AnomalyGauge } from '../components/patient/AnomalyGauge';
import { ExplainabilityPanel } from '../components/patient/ExplainabilityPanel';
import { VitalCharts } from '../components/patient/VitalCharts';
import { ClinicalNotesTimeline } from '../components/patient/ClinicalNotesTimeline';
import { RequestTransferModal } from '../components/transfer/RequestTransferModal';
import { generateHistoryData } from '../hooks/useTelemetrySimulator';
import { useAuth } from '../context/AuthContext';

export const PatientDetail = ({
  bed,
  onBack,
  onAcknowledgeTier2,
  onTriggerTier1Modal,
}) => {
  const { user, role } = useAuth();
  const [transferModalOpen, setTransferModalOpen] = useState(false);

  // Generate 10 minutes of synthetic historical telemetry for this patient
  const historyData = useMemo(() => {
    if (!bed) return [];
    const isAnomaly = bed.tier === 'tier1' || bed.tier === 'tier2';
    return generateHistoryData(bed.hr, bed.spo2, bed.bpSys, bed.bpDia, isAnomaly);
  }, [bed?.bedId, bed?.tier]);

  if (!bed) {
    return (
      <div className="p-8 text-center bg-white rounded-2xl border border-slate-200">
        <p className="text-sm font-semibold text-slate-700">Patient bed not found</p>
        <Button variant="outline" size="sm" onClick={onBack} className="mt-4">
          Return to Ward
        </Button>
      </div>
    );
  }

  const isTier1 = bed.tier === 'tier1';
  const isTier2 = bed.tier === 'tier2';

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Navigation & Patient Demographics Banner */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onBack}
              className="p-2 rounded-xl border border-slate-200 hover:bg-slate-100 text-slate-600 transition-colors"
              title="Return to Ward Dashboard"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-mono font-bold bg-teal-50 text-[#0D8A9A] border border-teal-200 px-2 py-0.5 rounded-lg">
                  BED {bed.bedId}
                </span>
                <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                  {bed.patientName}
                </h1>
                <Badge 
                  variant={isTier1 ? 'tier1' : isTier2 ? 'tier2' : 'normal'} 
                  size="sm" 
                  dot 
                  pulseDot={isTier1}
                >
                  {isTier1 ? 'Tier 1 Critical' : isTier2 ? 'Tier 2 Warning' : 'Normal Telemetry'}
                </Badge>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                {bed.diagnosis} • Admitted {bed.admissionDate}
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            {/* Request Transfer Button (Doctor-only) */}
            {role === 'doctor' && (
              <Button
                variant="outline"
                size="sm"
                icon={ArrowLeftRight}
                onClick={() => setTransferModalOpen(true)}
                className="text-slate-700 hover:text-slate-900 border-slate-200"
              >
                Request Transfer
              </Button>
            )}

            {isTier1 && !bed.acknowledged && (
              <Button
                variant="danger"
                size="sm"
                icon={ShieldAlert}
                onClick={() => onTriggerTier1Modal?.(bed)}
                className="shadow-sm shadow-red-500/20 animate-pulse"
              >
                Critical Takeover Active
              </Button>
            )}
          </div>
        </div>

        {/* Patient Clinical Info Strip */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 pt-3 border-t border-slate-100 text-xs">
          <div>
            <span className="text-[10px] text-slate-400 font-semibold uppercase block">Age / Gender</span>
            <span className="font-bold text-slate-800">{bed.age} Years • {bed.gender}</span>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-semibold uppercase block">Attending Physician</span>
            <span className="font-bold text-slate-800 truncate block">{bed.assignedDoctor}</span>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-semibold uppercase block">Code Status</span>
            <span className="font-bold text-slate-800">{bed.codeStatus}</span>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-semibold uppercase block">Telemetry Lead</span>
            <span className="font-bold text-emerald-600">Lead II / V5 (Active)</span>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-semibold uppercase block">Current SpO2</span>
            <span className={`vital-number font-bold text-sm ${bed.spo2 < 85 ? 'text-red-600' : 'text-teal-600'}`}>
              {bed.spo2}%
            </span>
          </div>
          <div>
            <span className="text-[10px] text-slate-400 font-semibold uppercase block">Heart Rate</span>
            <span className={`vital-number font-bold text-sm ${bed.hr > 120 ? 'text-red-600' : 'text-slate-900'}`}>
              {bed.hr} BPM
            </span>
          </div>
        </div>
      </div>

      {/* Main Grid: Telemetry Charts (Left) + Anomaly & Alert Acknowledgment (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (8 cols): Vital History Charts (Recharts) */}
        <div className="lg:col-span-8 space-y-6">
          <VitalCharts
            data={historyData}
            currentVitals={{ hr: bed.hr, spo2: bed.spo2, bpSys: bed.bpSys, bpDia: bed.bpDia }}
          />

          {/* Clinical Notes Timeline */}
          <ClinicalNotesTimeline bedId={bed.bedId} patientName={bed.patientName} />
        </div>

        {/* Right Column (4 cols): Anomaly Gauge, XAI Explainability & Alert Acknowledgment Card */}
        <div className="lg:col-span-4 space-y-6">
          {/* Tier 2 Alert Acknowledgment Side-Panel Card */}
          {isTier2 && !bed.acknowledged && (
            <div className="bg-amber-50 rounded-2xl p-5 border-2 border-amber-300 shadow-md shadow-amber-500/10 space-y-3 animate-in fade-in">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-6 h-6 text-amber-600 shrink-0 mt-0.5 animate-bounce" />
                <div className="space-y-1">
                  <h3 className="text-sm font-bold text-amber-950">
                    Tier 2 Warning Alert Pending
                  </h3>
                  <p className="text-xs text-amber-800 leading-relaxed">
                    SpO2 deterioration or multi-vital anomaly detected. Clinician acknowledgment is required to log bedside review.
                  </p>
                </div>
              </div>

              <div className="pt-2">
                <Button
                  variant="primary"
                  size="md"
                  onClick={() => onAcknowledgeTier2?.(bed.bedId, user.name)}
                  className="w-full justify-center bg-amber-500 hover:bg-amber-600 text-white shadow-xs"
                >
                  Acknowledge Warning
                </Button>
                <span className="text-[10px] text-amber-700 block text-center mt-1.5">
                  Logged by: {user.name} ({user.role.toUpperCase()})
                </span>
              </div>
            </div>
          )}

          {/* Acknowledged Badge Card if already acknowledged */}
          {bed.acknowledged && (isTier1 || isTier2) && (
            <div className="p-3.5 bg-emerald-50 rounded-2xl border border-emerald-200 text-xs text-emerald-800 flex items-center gap-2.5">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
              <div>
                <span className="font-bold block">Alert Acknowledged</span>
                <span className="text-[11px] text-emerald-700">
                  By {bed.acknowledgedBy || user.name} at {bed.acknowledgedAt || 'Recently'}
                </span>
              </div>
            </div>
          )}

          {/* Anomaly Score Arc Gauge */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">
              Multi-Vital Anomaly Gauge
            </h3>
            <AnomalyGauge score={bed.anomalyScore} />
          </div>

          {/* Explainability Panel (XAI) */}
          <ExplainabilityPanel
            factors={bed.factors}
            anomalyScore={bed.anomalyScore}
            tier={bed.tier}
          />
        </div>
      </div>

      {/* Doctor Transfer Modal */}
      <RequestTransferModal
        isOpen={transferModalOpen}
        onClose={() => setTransferModalOpen(false)}
        patient={bed}
      />
    </div>
  );
};

export default PatientDetail;
