import React from 'react';

/**
 * Badge Component: Status pills for clinical alert tiers and roles
 * Alert Tiers:
 * - tier1: #EF4444 (Critical)
 * - tier2: #F59E0B (Warning)
 * - tier3: #94A3B8 (Muted/Notice)
 * - normal: #0EA5B7 (Normal telemetry)
 * Roles: admin, doctor
 */
export const Badge = ({
  children,
  variant = 'normal',
  size = 'md',
  dot = false,
  pulseDot = false,
  className = '',
  ...props
}) => {
  const sizeClasses = {
    sm: 'text-[11px] px-2 py-0.5 font-medium gap-1',
    md: 'text-xs px-2.5 py-1 font-semibold gap-1.5',
    lg: 'text-sm px-3 py-1.5 font-semibold gap-2',
  };

  const variantClasses = {
    // Clinical Tiers
    tier1: 'bg-red-50 text-red-700 border border-red-200/80 shadow-sm',
    'tier1-solid': 'bg-[#EF4444] text-white shadow-sm shadow-red-500/20',
    tier2: 'bg-amber-50 text-amber-800 border border-amber-200/80 shadow-sm',
    'tier2-solid': 'bg-[#F59E0B] text-white shadow-sm shadow-amber-500/20',
    tier3: 'bg-slate-100 text-slate-600 border border-slate-200 shadow-sm',
    normal: 'bg-teal-50 text-teal-800 border border-teal-200/80 shadow-sm',
    'normal-solid': 'bg-[#0EA5B7] text-white shadow-sm',
    
    // Roles
    admin: 'bg-purple-50 text-purple-700 border border-purple-200 font-semibold',
    doctor: 'bg-teal-50 text-[#0D8A9A] border border-teal-200 font-semibold',

    // System States
    online: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
    offline: 'bg-rose-100 text-rose-800 border border-rose-300 font-bold animate-pulse',
    edge: 'bg-cyan-50 text-cyan-800 border border-cyan-200',
  };

  const dotColorClasses = {
    tier1: 'bg-[#EF4444]',
    'tier1-solid': 'bg-white',
    tier2: 'bg-[#F59E0B]',
    'tier2-solid': 'bg-white',
    tier3: 'bg-[#94A3B8]',
    normal: 'bg-[#0EA5B7]',
    'normal-solid': 'bg-white',
    admin: 'bg-purple-600',
    doctor: 'bg-[#0EA5B7]',
    online: 'bg-emerald-500',
    offline: 'bg-rose-600',
    edge: 'bg-cyan-500',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full tracking-wide transition-colors ${sizeClasses[size] || sizeClasses.md} ${variantClasses[variant] || variantClasses.normal} ${className}`}
      {...props}
    >
      {dot && (
        <span className="relative flex h-2 w-2 shrink-0">
          {pulseDot && (
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${dotColorClasses[variant] || 'bg-current'}`} />
          )}
          <span className={`relative inline-flex rounded-full h-2 w-2 ${dotColorClasses[variant] || 'bg-current'}`} />
        </span>
      )}
      <span>{children}</span>
    </span>
  );
};

export default Badge;
