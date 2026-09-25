import React, { useState } from 'react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  ReferenceArea,
  ReferenceLine 
} from 'recharts';
import { HeartPulse, Activity, Gauge, Clock } from 'lucide-react';

/**
 * VitalCharts Component
 * Smooth 10-minute historical telemetry charts (Recharts)
 * Includes tier-colored threshold bands (Danger, Warning, Normal)
 */
export const VitalCharts = ({ data = [], currentVitals = {} }) => {
  const [activeTab, setActiveTab] = useState('all'); // 'all' | 'hr' | 'spo2' | 'bp'
  const [timeWindow, setTimeWindow] = useState('10m'); // '10m' | '30m' | '1h'

  const customTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;

    return (
      <div className="bg-slate-900/95 text-white p-3 rounded-xl shadow-xl text-xs font-mono space-y-1.5 backdrop-blur-md border border-slate-800">
        <div className="text-[10px] text-slate-400 font-sans pb-1 border-b border-slate-800">
          Timestamp: {label}
        </div>
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center justify-between gap-4">
            <span style={{ color: entry.color }} className="font-semibold font-sans">
              {entry.name}:
            </span>
            <span className="font-bold">
              {entry.value} {entry.name === 'SpO2' ? '%' : entry.name.includes('BP') ? 'mmHg' : 'BPM'}
            </span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Chart Controls & Time Window Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveTab('all')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
              activeTab === 'all' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            All Vitals (Stacked)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('spo2')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
              activeTab === 'spo2' ? 'bg-[#0EA5B7] text-white' : 'bg-teal-50 text-teal-800 hover:bg-teal-100'
            }`}
          >
            SpO2 (%)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('hr')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
              activeTab === 'hr' ? 'bg-[#3B82F6] text-white' : 'bg-blue-50 text-blue-800 hover:bg-blue-100'
            }`}
          >
            Heart Rate (BPM)
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('bp')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
              activeTab === 'bp' ? 'bg-purple-600 text-white' : 'bg-purple-50 text-purple-800 hover:bg-purple-100'
            }`}
          >
            Blood Pressure
          </button>
        </div>

        {/* Time Window */}
        <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium self-end sm:self-auto">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>Window:</span>
          {['10m', '30m', '1h'].map(t => (
            <button
              key={t}
              type="button"
              onClick={() => setTimeWindow(t)}
              className={`px-2 py-0.5 rounded text-[11px] font-mono ${
                timeWindow === t ? 'bg-slate-200 text-slate-900 font-bold' : 'text-slate-400 hover:text-slate-700'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Chart 1: SpO2 Oxygen Saturation with Critical Threshold Bands */}
      {(activeTab === 'all' || activeTab === 'spo2') && (
        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#0EA5B7]" />
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Pulse Oximetry (SpO2 %)
              </h4>
            </div>
            <div className="flex items-center gap-3 text-[11px] font-mono">
              <span className="flex items-center gap-1 text-red-600 font-semibold">
                <span className="w-2 h-2 rounded bg-red-100 border border-red-300" /> &lt;85% Critical
              </span>
              <span className="flex items-center gap-1 text-amber-600 font-semibold">
                <span className="w-2 h-2 rounded bg-amber-100 border border-amber-300" /> 85-90% Warning
              </span>
              <span className="font-bold text-slate-900">Current: {currentVitals.spo2}%</span>
            </div>
          </div>

          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                <YAxis domain={[65, 100]} tick={{ fontSize: 10, fill: '#94A3B8' }} />
                <Tooltip content={customTooltip} />
                
                {/* Danger Red threshold band (<85%) */}
                <ReferenceArea y1={65} y2={85} fill="#EF4444" fillOpacity={0.08} />
                {/* Warning Amber threshold band (85% - 90%) */}
                <ReferenceArea y1={85} y2={90} fill="#F59E0B" fillOpacity={0.08} />
                {/* Hard Safety Threshold Line */}
                <ReferenceLine y={85} stroke="#EF4444" strokeDasharray="3 3" label={{ value: 'Hard Fail-Safe: 85%', fill: '#EF4444', fontSize: 9, position: 'insideBottomRight' }} />

                <Line
                  type="monotone"
                  dataKey="spo2"
                  name="SpO2"
                  stroke="#0EA5B7"
                  strokeWidth={2.5}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Chart 2: Heart Rate (HR BPM) with Tachycardia/Bradycardia Bands */}
      {(activeTab === 'all' || activeTab === 'hr') && (
        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-[#3B82F6]" />
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Heart Rate (BPM)
              </h4>
            </div>
            <div className="flex items-center gap-3 text-[11px] font-mono">
              <span className="flex items-center gap-1 text-red-600 font-semibold">
                &gt;120 Tachycardia
              </span>
              <span className="flex items-center gap-1 text-amber-600 font-semibold">
                &lt;50 Bradycardia
              </span>
              <span className="font-bold text-slate-900">Current: {currentVitals.hr} BPM</span>
            </div>
          </div>

          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                <YAxis domain={[40, 160]} tick={{ fontSize: 10, fill: '#94A3B8' }} />
                <Tooltip content={customTooltip} />

                {/* Tachycardia danger band */}
                <ReferenceArea y1={120} y2={160} fill="#EF4444" fillOpacity={0.08} />
                {/* Bradycardia warning band */}
                <ReferenceArea y1={40} y2={50} fill="#F59E0B" fillOpacity={0.08} />
                
                <Line
                  type="monotone"
                  dataKey="hr"
                  name="Heart Rate"
                  stroke="#3B82F6"
                  strokeWidth={2.5}
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Chart 3: Blood Pressure (Systolic & Diastolic) */}
      {(activeTab === 'all' || activeTab === 'bp') && (
        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-600" />
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Non-Invasive Blood Pressure (Systolic / Diastolic mmHg)
              </h4>
            </div>
            <div className="text-[11px] font-mono font-bold text-slate-900">
              Current: {currentVitals.bpSys}/{currentVitals.bpDia} mmHg
            </div>
          </div>

          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                <YAxis domain={[40, 180]} tick={{ fontSize: 10, fill: '#94A3B8' }} />
                <Tooltip content={customTooltip} />

                {/* Hypotension warning band */}
                <ReferenceArea y1={40} y2={60} fill="#EF4444" fillOpacity={0.08} />
                {/* Hypertension danger band */}
                <ReferenceArea y1={140} y2={180} fill="#F59E0B" fillOpacity={0.08} />

                <Line
                  type="monotone"
                  dataKey="bpSys"
                  name="Systolic BP"
                  stroke="#8B5CF6"
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="bpDia"
                  name="Diastolic BP"
                  stroke="#C084FC"
                  strokeWidth={2}
                  strokeDasharray="4 4"
                  dot={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

export default VitalCharts;
