import React, { useState } from 'react';
import { 
  HeartPulse, 
  Activity, 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  Search, 
  SlidersHorizontal,
  RefreshCw,
  Zap,
  Filter
} from 'lucide-react';
import { BedTile } from '../components/ward/BedTile';
import { Button, Input, Badge } from '../components/ui';
import { useAuth } from '../context/AuthContext';

export const WardDashboard = ({
  beds,
  waveforms,
  onSelectBed,
  onInjectHypoxia,
  onResetBeds,
}) => {
  const { user, role } = useAuth();
  const [filterMode, setFilterMode] = useState('all'); // 'all' | 'alerts' | 'assigned'
  const [searchQuery, setSearchQuery] = useState('');

  // Stats calculation
  const totalBeds = beds.length;
  const tier1Count = beds.filter(b => b.tier === 'tier1').length;
  const tier2Count = beds.filter(b => b.tier === 'tier2').length;
  const normalCount = beds.filter(b => b.tier === 'normal').length;

  // Filter beds
  const filteredBeds = beds.filter(bed => {
    // Search query match
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchName = bed.patientName.toLowerCase().includes(q);
      const matchBed = bed.bedId.toLowerCase().includes(q);
      const matchDiag = bed.diagnosis.toLowerCase().includes(q);
      if (!matchName && !matchBed && !matchDiag) return false;
    }

    // Filter mode
    if (filterMode === 'alerts') {
      return bed.tier === 'tier1' || bed.tier === 'tier2';
    }
    if (filterMode === 'assigned') {
      if (role === 'doctor') {
        return bed.assignedDoctor.includes('Chen');
      }
      return true;
    }

    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header Stat Strip & Quick Filter Bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
        <div className="flex items-center gap-4 flex-wrap">
          <div>
            <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <span>Ward Telemetry Monitor</span>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Real-time multi-vital triage • 10 ICU Beds Active
            </p>
          </div>

          <div className="h-8 w-px bg-slate-200 hidden sm:block" />

          {/* Quick Metrics */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setFilterMode('all')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                filterMode === 'all'
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              <span>Total Beds</span>
              <span className="bg-white/20 text-white px-1.5 py-0.2 rounded-md font-mono text-[11px]">{totalBeds}</span>
            </button>

            <button
              type="button"
              onClick={() => setFilterMode('alerts')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                filterMode === 'alerts'
                  ? 'bg-red-600 text-white shadow-xs'
                  : 'bg-red-50 text-red-700 hover:bg-red-100 border border-red-200/60'
              }`}
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>Active Alerts</span>
              <span className="bg-red-600 text-white px-1.5 py-0.2 rounded-md font-mono text-[11px]">{tier1Count + tier2Count}</span>
            </button>

            {role === 'doctor' && (
              <button
                type="button"
                onClick={() => setFilterMode('assigned')}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors ${
                  filterMode === 'assigned'
                    ? 'bg-[#0D8A9A] text-white shadow-xs'
                    : 'bg-teal-50 text-teal-800 hover:bg-teal-100 border border-teal-200/60'
                }`}
              >
                <span>My Assigned Beds</span>
                <span className="bg-teal-700 text-white px-1.5 py-0.2 rounded-md font-mono text-[11px]">5</span>
              </button>
            )}
          </div>
        </div>

        {/* Search & Demo Telemetry Injector Controls */}
        <div className="flex items-center gap-3">
          <div className="w-48 sm:w-56">
            <Input
              placeholder="Search Bed / Patient..."
              icon={Search}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="py-1.5 text-xs"
            />
          </div>

          {/* Anomaly Injector Button (Demo Testing) */}
          <Button
            variant="outline"
            size="sm"
            icon={Zap}
            onClick={onInjectHypoxia}
            className="text-red-600 border-red-200 hover:bg-red-50"
            title="Inject acute desaturation into Bed 04 to test Tier 1 alarm cascade"
          >
            Inject Hypoxia
          </Button>

          <Button
            variant="ghost"
            size="sm"
            icon={RefreshCw}
            onClick={onResetBeds}
            title="Reset telemetry baseline"
          >
            Reset
          </Button>
        </div>
      </div>

      {/* Responsive 10-Bed Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {filteredBeds.map(bed => (
          <BedTile
            key={bed.bedId}
            bed={bed}
            waveformPoints={waveforms[bed.bedId] || []}
            onClick={() => onSelectBed(bed.bedId)}
          />
        ))}
      </div>

      {filteredBeds.length === 0 && (
        <div className="text-center py-16 bg-white rounded-2xl border border-slate-200">
          <p className="text-sm font-semibold text-slate-700">No patient beds matched your filter</p>
          <p className="text-xs text-slate-400 mt-1">Try resetting the search query or filter selection</p>
          <Button variant="outline" size="sm" onClick={() => { setFilterMode('all'); setSearchQuery(''); }} className="mt-4">
            Reset Filters
          </Button>
        </div>
      )}
    </div>
  );
};

export default WardDashboard;
