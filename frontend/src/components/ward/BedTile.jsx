import React from 'react';
import { HeartPulse, Activity, AlertTriangle, ShieldAlert, WifiOff, ChevronRight } from 'lucide-react';
import { Badge } from '../ui/Badge';

/**
 * BedTile Component
 * Visual unit for a single patient bed in Ward Dashboard:
 * - Patient initials & Bed ID
 * - Mini live ECG waveform ticking via mock WebSocket every 1s
 * - High-legibility numeric readouts for HR, SpO2, and BP
 * - Colored status ring (teal=normal, amber=Tier 2, red=Tier 1 pulsing, gray=No Signal)
 * - Subtle continuous pulse glow animation on Tier 1
 */
export const BedTile = ({
  bed,
  waveformPoints = [],
  onClick,
}) => {
  const isTier1 = bed.tier === 'tier1';
  const isTier2 = bed.tier === 'tier2';
  const isNoSignal = bed.tier === 'no-signal';
  const isNormal = bed.tier === 'normal';

  // Ring and border styling per tier
  const borderClasses = isTier1
    ? 'border-2 border-red-500 tier1-pulse-border bg-gradient-to-b from-white to-red-50/30'
    : isTier2
    ? 'border-2 border-amber-400 shadow-md shadow-amber-500/10 bg-gradient-to-b from-white to-amber-50/20'
    : isNoSignal
    ? 'border-2 border-slate-300 opacity-75 bg-slate-50'
    : 'border border-slate-200/90 hover:border-teal-400 bg-white shadow-sm';

  // Waveform line color
  const waveformStroke = isTier1
    ? '#EF4444'
    : isTier2
    ? '#F59E0B'
    : isNoSignal
    ? '#94A3B8'
    : '#0EA5B7';

  // Convert 30 array points to SVG polyline coordinates (width 180, height 40)
  const polylinePoints = waveformPoints.length > 0
    ? waveformPoints
        .map((y, idx) => {
          const x = (idx / (waveformPoints.length - 1)) * 180;
          return `${x.toFixed(1)},${y}`;
        })
        .join(' ')
    : '0,20 180,20';

  return (
    <div
      onClick={onClick}
      className={`relative rounded-2xl p-4 cursor-pointer transition-all duration-200 hover:-translate-y-1 hover:shadow-lg ${borderClasses}`}
      role="button"
      tabIndex={0}
      aria-label={`Bed ${bed.bedId}, Patient ${bed.patientName}, Status: ${bed.tier}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick?.();
        }
      }}
    >
      {/* Top row: Bed ID, Initials, Tier Pill */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs ${
            isTier1 
              ? 'bg-red-500 text-white' 
              : isTier2 
              ? 'bg-amber-500 text-white' 
              : isNoSignal 
              ? 'bg-slate-300 text-slate-700' 
              : 'bg-teal-50 text-[#0D8A9A] border border-teal-200'
          }`}>
            {bed.bedId}
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-sm text-slate-900 leading-tight">
                {bed.initials}
              </span>
              <span className="text-[11px] text-slate-400">• {bed.age}y</span>
            </div>
            <span className="text-[10px] text-slate-500 block truncate max-w-[110px]" title={bed.diagnosis}>
              {bed.diagnosis}
            </span>
          </div>
        </div>

        {/* Tier badge */}
        <div>
          {isTier1 && (
            <Badge variant="tier1" size="sm" dot pulseDot>
              Tier 1
            </Badge>
          )}
          {isTier2 && (
            <Badge variant="tier2" size="sm" dot>
              Tier 2
            </Badge>
          )}
          {isNormal && (
            <Badge variant="normal" size="sm" dot>
              Normal
            </Badge>
          )}
          {isNoSignal && (
            <Badge variant="tier3" size="sm">
              No Signal
            </Badge>
          )}
        </div>
      </div>

      {/* Live Mini Waveform (1s WebSocket Heartbeat line) */}
      <div className="h-10 w-full bg-slate-50 rounded-lg p-1 relative overflow-hidden flex items-center border border-slate-100 mb-3">
        {isNoSignal ? (
          <div className="w-full flex items-center justify-center gap-1 text-[11px] font-medium text-slate-400">
            <WifiOff className="w-3.5 h-3.5" />
            <span>Telemetry Disconnected</span>
          </div>
        ) : (
          <svg className="w-full h-full" viewBox="0 0 180 40" preserveAspectRatio="none">
            {/* Subtle grid lines */}
            <line x1="0" y1="20" x2="180" y2="20" stroke="#E2E8F0" strokeWidth="0.5" strokeDasharray="2,2" />
            <polyline
              fill="none"
              stroke={waveformStroke}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={polylinePoints}
            />
          </svg>
        )}
      </div>

      {/* Numeric Vital Readouts: High legibility */}
      <div className="grid grid-cols-3 gap-2 text-center pt-1 border-t border-slate-100">
        {/* Heart Rate */}
        <div className="bg-slate-50/70 rounded-xl p-1.5">
          <span className="text-[9px] uppercase tracking-wider text-slate-400 font-semibold block">HR</span>
          <div className={`vital-number text-base leading-tight ${
            bed.hr > 120 || (bed.hr < 50 && !isNoSignal) ? 'text-red-600 font-bold' : 'text-slate-800'
          }`}>
            {isNoSignal ? '--' : bed.hr}
          </div>
          <span className="text-[9px] text-slate-400 font-medium">BPM</span>
        </div>

        {/* SpO2 */}
        <div className="bg-slate-50/70 rounded-xl p-1.5">
          <span className="text-[9px] uppercase tracking-wider text-slate-400 font-semibold block">SpO2</span>
          <div className={`vital-number text-base leading-tight ${
            bed.spo2 < 85 && !isNoSignal ? 'text-red-600 font-bold animate-pulse' :
            bed.spo2 < 93 && !isNoSignal ? 'text-amber-600 font-bold' :
            'text-teal-600'
          }`}>
            {isNoSignal ? '--' : `${bed.spo2}%`}
          </div>
          <span className="text-[9px] text-slate-400 font-medium">O2 Sat</span>
        </div>

        {/* BP */}
        <div className="bg-slate-50/70 rounded-xl p-1.5">
          <span className="text-[9px] uppercase tracking-wider text-slate-400 font-semibold block">BP</span>
          <div className="vital-number text-xs leading-tight mt-1 text-slate-800 truncate">
            {isNoSignal ? '--' : `${bed.bpSys}/${bed.bpDia}`}
          </div>
          <span className="text-[9px] text-slate-400 font-medium">mmHg</span>
        </div>
      </div>

      {/* Hover prompt footer */}
      <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-400 pt-1.5 border-t border-slate-100/60">
        <span className="truncate max-w-[120px] font-medium">{bed.assignedDoctor}</span>
        <span className="text-[#0EA5B7] font-semibold flex items-center gap-0.5 group-hover:translate-x-0.5 transition-transform">
          Details <ChevronRight className="w-3 h-3" />
        </span>
      </div>
    </div>
  );
};

export default BedTile;
