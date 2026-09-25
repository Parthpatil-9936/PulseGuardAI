import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  KeyRound, 
  Clock, 
  ShieldAlert, 
  UserCheck, 
  AlertTriangle, 
  Plus, 
  XCircle,
  FileText
} from 'lucide-react';
import { Button, Badge, Modal, ModalFooter, Input, Select } from '../../components/ui';

export const EmergencyAccess = () => {
  const [grants, setGrants] = useState([
    {
      id: 'bg_901',
      clinician: 'Dr. Marcus Vance, MD',
      patient: 'Eleanor Vance (Bed 01)',
      reason: 'Urgent bedside bronchoscopy while primary attending scrubbed in OR.',
      grantedAt: '10:00 AM',
      initialMinutes: 30,
      remainingSeconds: 1140, // 19 minutes left
      status: 'active',
    },
    {
      id: 'bg_900',
      clinician: 'David Kim, RN',
      patient: 'Julian Drake (Bed 04)',
      reason: 'Critical Tier 1 resuscitation code team supplemental support.',
      grantedAt: '09:45 AM',
      initialMinutes: 15,
      remainingSeconds: 180, // 3 minutes left
      status: 'active',
    },
  ]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [clinician, setClinician] = useState('Dr. Elena Rostova, MD');
  const [patient, setPatient] = useState('Marcus Sterling (Bed 02)');
  const [duration, setDuration] = useState('30');
  const [reason, setReason] = useState('');

  // Live countdown timer for active grants
  useEffect(() => {
    const timer = setInterval(() => {
      setGrants(prev => prev.map(g => {
        if (g.status !== 'active' || g.remainingSeconds <= 0) {
          return { ...g, status: 'expired', remainingSeconds: 0 };
        }
        const next = g.remainingSeconds - 1;
        return {
          ...g,
          remainingSeconds: next,
          status: next <= 0 ? 'expired' : 'active',
        };
      }));
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleGrant = (e) => {
    e.preventDefault();
    if (!reason.trim()) return;

    const mins = parseInt(duration, 10) || 30;
    const newGrant = {
      id: `bg_${Date.now()}`,
      clinician,
      patient,
      reason: reason.trim(),
      grantedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      initialMinutes: mins,
      remainingSeconds: mins * 60,
      status: 'active',
    };

    setGrants([newGrant, ...grants]);
    setIsModalOpen(false);
    setReason('');
  };

  const handleRevoke = (id) => {
    setGrants(prev => prev.map(g => {
      if (g.id === id) {
        return { ...g, status: 'revoked', remainingSeconds: 0 };
      }
      return g;
    }));
  };

  const formatTimer = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Emergency "Break-Glass" Access Panel
            </h1>
            <Badge variant="tier2" size="sm">
              Time-Bounded Session
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Admin-provisioned emergency bypass for unassigned clinicians with mandatory rationale and auto-expiring tokens
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          icon={Plus}
          onClick={() => setIsModalOpen(true)}
        >
          Grant Emergency Access
        </Button>
      </div>

      {/* Active Grants List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {grants.map((grant) => {
          const isActive = grant.status === 'active';
          const isExpired = grant.status === 'expired';
          const isRevoked = grant.status === 'revoked';

          return (
            <div
              key={grant.id}
              className={`p-5 rounded-2xl bg-white border transition-all duration-200 shadow-xs ${
                isActive 
                  ? 'border-amber-400 ring-2 ring-amber-100' 
                  : 'border-slate-200 opacity-60 bg-slate-50'
              }`}
            >
              <div className="flex items-center justify-between mb-3 pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs ${
                    isActive ? 'bg-amber-500 text-white' : 'bg-slate-200 text-slate-600'
                  }`}>
                    <KeyRound className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="font-bold text-sm text-slate-900 block leading-tight">
                      {grant.clinician}
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      Grant: {grant.id}
                    </span>
                  </div>
                </div>

                {/* Status Badge */}
                <Badge
                  variant={isActive ? 'tier2' : isRevoked ? 'tier1' : 'tier3'}
                  size="sm"
                  dot={isActive}
                >
                  {grant.status.toUpperCase()}
                </Badge>
              </div>

              {/* Patient and Countdown */}
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500">Patient Scope:</span>
                  <span className="font-bold text-slate-900">{grant.patient}</span>
                </div>

                {/* Real-time countdown timer */}
                <div className={`p-3 rounded-xl border flex items-center justify-between ${
                  isActive ? 'bg-amber-50/70 border-amber-200' : 'bg-slate-100 border-slate-200'
                }`}>
                  <div className="flex items-center gap-2">
                    <Clock className={`w-4 h-4 ${isActive ? 'text-amber-600 animate-spin' : 'text-slate-400'}`} style={{ animationDuration: '6s' }} />
                    <span className="text-xs font-semibold text-slate-700">
                      {isActive ? 'Session Remaining:' : 'Session Ended'}
                    </span>
                  </div>
                  <span className={`font-mono text-base font-bold ${
                    isActive ? 'text-amber-800' : 'text-slate-400'
                  }`}>
                    {isActive ? formatTimer(grant.remainingSeconds) : '00:00 (Expired)'}
                  </span>
                </div>

                <div className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block mb-0.5">
                    Clinical Justification:
                  </span>
                  "{grant.reason}"
                </div>

                {isActive && (
                  <div className="pt-2 flex justify-end">
                    <Button
                      variant="outline"
                      size="sm"
                      icon={XCircle}
                      onClick={() => handleRevoke(grant.id)}
                      className="text-red-600 border-red-200 hover:bg-red-50 text-xs"
                    >
                      Revoke Access Now
                    </Button>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Grant Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Issue Emergency Break-Glass Authorization"
        description="Creates temporary time-bounded clinical access token with cryptographic audit link"
      >
        <form onSubmit={handleGrant} className="space-y-4">
          <Select
            label="Grantee Clinician"
            value={clinician}
            onChange={(e) => setClinician(e.target.value)}
            options={[
              { value: 'Dr. Elena Rostova, MD', label: 'Dr. Elena Rostova, MD (Pulmonology)' },
              { value: 'Dr. Marcus Vance, MD', label: 'Dr. Marcus Vance, MD (ICU Director)' },
              { value: 'David Kim, RN', label: 'David Kim, RN (Ward 4 RN)' },
              { value: 'Dr. Sarah Chen, MD', label: 'Dr. Sarah Chen, MD (Cardiology Attending)' },
            ]}
          />

          <Select
            label="Patient Target Scope"
            value={patient}
            onChange={(e) => setPatient(e.target.value)}
            options={[
              { value: 'Julian Drake (Bed 04)', label: 'Julian Drake — Bed 04 (Septic Shock / Hypoxemia)' },
              { value: 'Marcus Sterling (Bed 02)', label: 'Marcus Sterling — Bed 02 (Decompensated Heart Failure)' },
              { value: 'Eleanor Vance (Bed 01)', label: 'Eleanor Vance — Bed 01 (Post-CABG)' },
              { value: 'Thomas Wright (Bed 06)', label: 'Thomas Wright — Bed 06 (COPD Exacerbation)' },
            ]}
          />

          <Select
            label="Authorization Duration (Auto-Expires)"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            options={[
              { value: '15', label: '15 Minutes (Rapid Bedside Code/Procedure)' },
              { value: '30', label: '30 Minutes (Standard Emergency Consult)' },
              { value: '60', label: '1 Hour (Extended Resuscitation)' },
              { value: '240', label: '4 Hours (Shift Emergency Coverage)' },
            ]}
          />

          <Input
            label="Mandatory Clinical Rationale"
            placeholder="Document emergency rationale (e.g. Attending unavailable, acute hypoxia)..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            helperText="Recorded to immutable audit ledger under DPDP Act requirements"
            required
          />

          <ModalFooter>
            <Button variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Issue Break-Glass Token
            </Button>
          </ModalFooter>
        </form>
      </Modal>
    </div>
  );
};

export default EmergencyAccess;
