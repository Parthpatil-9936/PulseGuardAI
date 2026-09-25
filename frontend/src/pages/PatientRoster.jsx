import React, { useState } from 'react';
import { Users, Search, ChevronRight, HeartPulse, Stethoscope, AlertTriangle, ShieldAlert } from 'lucide-react';
import { Badge, Button, Input } from '../components/ui';
import { useAuth } from '../context/AuthContext';

export const PatientRoster = ({ beds, onSelectBed }) => {
  const { user, role } = useAuth();
  const [search, setSearch] = useState('');
  const [tierFilter, setTierFilter] = useState('all');

  const filtered = beds.filter(b => {
    if (tierFilter !== 'all' && b.tier !== tierFilter) return false;
    if (search.trim()) {
      const q = search.toLowerCase();
      return b.patientName.toLowerCase().includes(q) || b.bedId.toLowerCase().includes(q) || b.diagnosis.toLowerCase().includes(q);
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Ward 4 Patient Census & Roster
            </h1>
            <Badge variant="normal" size="sm">
              {beds.length} Total Patients
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time census, attending assignments, admission diagnoses, and code statuses
          </p>
        </div>

        <div className="w-full sm:w-64">
          <Input
            placeholder="Search patient, bed, diagnosis..."
            icon={Search}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="py-1.5 text-xs"
          />
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2">
        {['all', 'tier1', 'tier2', 'normal', 'no-signal'].map(t => (
          <button
            key={t}
            type="button"
            onClick={() => setTierFilter(t)}
            className={`px-3 py-1.5 text-xs font-semibold rounded-xl capitalize transition-colors ${
              tierFilter === t
                ? 'bg-slate-900 text-white shadow-xs'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200/80'
            }`}
          >
            {t === 'all' ? 'All Patients' : t.replace('-', ' ')}
          </button>
        ))}
      </div>

      {/* Roster Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3.5 px-4">Bed ID</th>
                <th className="py-3.5 px-4">Patient Name</th>
                <th className="py-3.5 px-4">Demographics</th>
                <th className="py-3.5 px-4">Admit Diagnosis</th>
                <th className="py-3.5 px-4">Attending Doctor</th>
                <th className="py-3.5 px-4">Current Vitals</th>
                <th className="py-3.5 px-4">Telemetry Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filtered.map(bed => {
                const isTier1 = bed.tier === 'tier1';
                const isTier2 = bed.tier === 'tier2';
                const isNoSignal = bed.tier === 'no-signal';

                return (
                  <tr 
                    key={bed.bedId} 
                    className="hover:bg-slate-50/80 transition-colors cursor-pointer"
                    onClick={() => onSelectBed(bed.bedId)}
                  >
                    <td className="py-3.5 px-4">
                      <span className="font-mono font-bold text-xs bg-slate-100 text-slate-800 px-2 py-1 rounded-lg">
                        {bed.bedId}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 font-bold text-slate-900">
                      {bed.patientName}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500">
                      {bed.age}y • {bed.gender}
                    </td>
                    <td className="py-3.5 px-4 text-slate-700 max-w-xs truncate" title={bed.diagnosis}>
                      {bed.diagnosis}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-800">
                      {bed.assignedDoctor}
                    </td>
                    <td className="py-3.5 px-4 font-mono">
                      {isNoSignal ? (
                        <span className="text-slate-400">Disconnected</span>
                      ) : (
                        <span className="space-x-2">
                          <span className={bed.hr > 120 ? 'text-red-600 font-bold' : 'text-slate-800'}>
                            {bed.hr} bpm
                          </span>
                          <span className="text-slate-300">•</span>
                          <span className={bed.spo2 < 85 ? 'text-red-600 font-bold' : 'text-teal-600 font-bold'}>
                            {bed.spo2}% SpO2
                          </span>
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <Badge 
                        variant={isTier1 ? 'tier1' : isTier2 ? 'tier2' : isNoSignal ? 'tier3' : 'normal'}
                        size="sm"
                        dot
                        pulseDot={isTier1}
                      >
                        {isTier1 ? 'Tier 1 Critical' : isTier2 ? 'Tier 2 Warning' : isNoSignal ? 'No Signal' : 'Normal'}
                      </Badge>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <span className="text-[#0EA5B7] font-semibold flex items-center justify-end gap-1 text-xs">
                        Open <ChevronRight className="w-3.5 h-3.5" />
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default PatientRoster;
