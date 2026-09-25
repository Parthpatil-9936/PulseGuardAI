import React from 'react';
import { cn } from '../../utils/cn';

export function Badge({
  variant = 'neutral',
  size = 'md',
  dot = false,
  dotPing = false,
  icon,
  children,
  className,
  ...props
}) {
  const baseStyles = 'inline-flex items-center font-medium rounded-full transition-colors whitespace-nowrap';

  const variants = {
    // Alert Tiers (Clinical specification)
    tier1: 'bg-red-50 text-[#EF4444] border border-red-200/90 font-semibold',
    'tier1-solid': 'bg-[#EF4444] text-white font-semibold shadow-xs shadow-red-500/30',
    tier2: 'bg-amber-50 text-amber-800 border border-amber-200/90 font-semibold',
    'tier2-solid': 'bg-[#F59E0B] text-white font-semibold shadow-xs shadow-amber-500/30',
    tier3: 'bg-slate-100 text-slate-600 border border-slate-200 font-medium',

    // Role Badges (Admin, Doctor, Nurse)
    admin: 'bg-purple-50 text-purple-700 border border-purple-200 font-medium',
    doctor: 'bg-teal-50 text-[#0D8A9A] border border-teal-200 font-medium',
    nurse: 'bg-blue-50 text-blue-700 border border-blue-200 font-medium',

    // Generic / Utility Badges
    primary: 'bg-teal-50 text-teal-700 border border-teal-200',
    secondary: 'bg-blue-50 text-blue-700 border border-blue-200',
    success: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
    warning: 'bg-amber-50 text-amber-800 border border-amber-200',
    danger: 'bg-red-50 text-red-700 border border-red-200',
    neutral: 'bg-slate-100 text-slate-700 border border-slate-200/80',
    glass: 'glass-panel text-slate-800 border-white/60 font-medium shadow-xs',
  };

  const sizes = {
    sm: 'text-[11px] px-2 py-0.5 gap-1 leading-tight',
    md: 'text-xs px-2.5 py-1 gap-1.5',
    lg: 'text-sm px-3.5 py-1.5 gap-2',
  };

  const dotColors = {
    tier1: 'bg-[#EF4444]',
    'tier1-solid': 'bg-white',
    tier2: 'bg-[#F59E0B]',
    'tier2-solid': 'bg-white',
    tier3: 'bg-[#94A3B8]',
    admin: 'bg-purple-600',
    doctor: 'bg-[#0EA5B7]',
    nurse: 'bg-[#3B82F6]',
    primary: 'bg-[#0EA5B7]',
    secondary: 'bg-[#3B82F6]',
    success: 'bg-emerald-500',
    warning: 'bg-amber-500',
    danger: 'bg-red-500',
    neutral: 'bg-slate-400',
    glass: 'bg-[#0EA5B7]',
  };

  const resolvedDotColor = dotColors[variant] || 'bg-current';

  return (
    <span
      className={cn(
        baseStyles,
        variants[variant] || variants.neutral,
        sizes[size] || sizes.md,
        className
      )}
      {...props}
    >
      {dot && (
        <span className="relative flex h-2 w-2 shrink-0">
          {dotPing && (
            <span
              className={cn(
                'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
                resolvedDotColor
              )}
            />
          )}
          <span
            className={cn(
              'relative inline-flex rounded-full h-2 w-2',
              resolvedDotColor
            )}
          />
        </span>
      )}
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{children}</span>
    </span>
  );
}

export default Badge;
