import React, { useState } from 'react';
import { FileText, Stethoscope, Activity, Plus, Search } from 'lucide-react';
import { ClinicalNotesTimeline } from '../components/patient/ClinicalNotesTimeline';
import { Badge, Input, Select } from '../components/ui';

export const ClinicalNotesPage = ({ beds }) => {
  const [selectedBedId, setSelectedBedId] = useState('04');
  const selectedBed = beds.find(b => b.bedId === selectedBedId) || beds[0];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              Clinical Notes & Shift Handover Ledger
            </h1>
            <Badge variant="normal" size="sm">
              Ward 4 Records
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Chronological physician progress notes, nursing shift observations, and alarm cascade acknowledgments
          </p>
        </div>

        {/* Patient Bed Selector */}
        <div className="w-full sm:w-64">
          <Select
            label="Filter Notes by Patient Bed"
            value={selectedBedId}
            onChange={(e) => setSelectedBedId(e.target.value)}
            options={beds.map(b => ({
              value: b.bedId,
              label: `Bed ${b.bedId} — ${b.patientName} (${b.tier.toUpperCase()})`
            }))}
          />
        </div>
      </div>

      {/* Selected Bed Header Banner */}
      {selectedBed && (
        <div className="p-4 rounded-2xl bg-teal-50/70 border border-teal-200/70 flex items-center justify-between text-xs">
          <div>
            <span className="text-[10px] text-teal-700 font-semibold uppercase block">Active Subject</span>
            <span className="font-bold text-teal-950 text-sm">{selectedBed.patientName}</span>
            <span className="text-teal-800 ml-2 font-mono">Bed {selectedBed.bedId} • {selectedBed.diagnosis}</span>
          </div>
          <Badge variant={selectedBed.tier === 'tier1' ? 'tier1' : selectedBed.tier === 'tier2' ? 'tier2' : 'normal'} size="sm" dot>
            {selectedBed.tier.toUpperCase()}
          </Badge>
        </div>
      )}

      {/* Timeline Component */}
      <ClinicalNotesTimeline bedId={selectedBed?.bedId} patientName={selectedBed?.patientName} />
    </div>
  );
};

export default ClinicalNotesPage;
