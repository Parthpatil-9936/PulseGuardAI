import React from 'react';

/**
 * AnomalyGauge Component
 * Radial / Arc Gauge (0.0 to 1.0)
 * Color interpolates: Teal (0.0 - 0.49) -> Amber (0.50 - 0.79) -> Red (0.80 - 1.00)
 * Label: Normal / Warning / Critical
 */
export const AnomalyGauge = ({ score = 0.12 }) => {
  // Clamp score between 0 and 1
  const clampedScore = Math.max(0, Math.min(1, score));

  // Determine label and color
  let label = 'Normal Telemetry';
  let color = '#0EA5B7'; // Teal
  let bgFill = 'bg-teal-50 text-teal-800 border-teal-200';

  if (clampedScore >= 0.8) {
    label = 'Critical Anomaly';
    color = '#EF4444'; // Red
    bgFill = 'bg-red-50 text-red-800 border-red-200 animate-pulse';
  } else if (clampedScore >= 0.5) {
    label = 'Warning Trend';
    color = '#F59E0B'; // Amber
    bgFill = 'bg-amber-50 text-amber-800 border-amber-200';
  }

  // Semi-circle arc calculations
  const radius = 70;
  const strokeWidth = 14;
  const circumference = Math.PI * radius; // Half-circle
  const strokeDashoffset = circumference - clampedScore * circumference;

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className="relative w-48 h-28 flex items-center justify-center">
        <svg className="w-48 h-28 overflow-visible" viewBox="0 0 160 90">
          <defs>
            {/* Gradient for arc track */}
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#0EA5B7" />
              <stop offset="50%" stopColor="#F59E0B" />
              <stop offset="100%" stopColor="#EF4444" />
            </linearGradient>
          </defs>

          {/* Background track arc */}
          <path
            d="M 10 80 A 70 70 0 0 1 150 80"
            fill="none"
            stroke="#E2E8F0"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Filled arc matching current score */}
          <path
            d="M 10 80 A 70 70 0 0 1 150 80"
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-700 ease-out"
          />
        </svg>

        {/* Center Score Readout */}
        <div className="absolute bottom-0 text-center flex flex-col items-center">
          <span 
            className="vital-number text-3xl leading-none font-bold"
            style={{ color }}
          >
            {clampedScore.toFixed(2)}
          </span>
          <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider mt-0.5">
            Anomaly Index
          </span>
        </div>
      </div>

      {/* Status Chip */}
      <div className={`mt-3 px-3 py-1 rounded-full text-xs font-bold border shadow-xs ${bgFill}`}>
        {label}
      </div>

      <div className="w-full flex justify-between text-[10px] font-mono text-slate-400 px-6 mt-2">
        <span>0.0 (Normal)</span>
        <span>0.5 (Trend)</span>
        <span>1.0 (Critical)</span>
      </div>
    </div>
  );
};

export default AnomalyGauge;
