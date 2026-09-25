import React, { useState } from 'react';
import { cn } from '../../utils/cn';

export function Avatar({
  name = '',
  src,
  role,
  status,
  size = 'md',
  className,
  ...props
}) {
  const [imageError, setImageError] = useState(false);

  // Compute clean initials (ignore titles like Dr., Nurse, etc.)
  const getInitials = (str) => {
    if (!str) return 'PG';
    const cleanStr = str.replace(/^(dr\.|dr|nurse|adm\.|admin)\s+/i, '').trim();
    const parts = cleanStr.split(/\s+/).filter(Boolean);
    if (parts.length === 0) return 'PG';
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  const sizes = {
    xs: 'h-6 w-6 text-[10px]',
    sm: 'h-8 w-8 text-xs',
    md: 'h-10 w-10 text-sm font-semibold',
    lg: 'h-12 w-12 text-base font-semibold',
    xl: 'h-14 w-14 text-lg font-semibold',
  };

  const roleColors = {
    doctor: 'bg-teal-50 text-[#0D8A9A] border-teal-200/80',
    nurse: 'bg-blue-50 text-[#3B82F6] border-blue-200/80',
    admin: 'bg-purple-50 text-purple-700 border-purple-200/80',
    default: 'bg-slate-100 text-slate-700 border-slate-200',
  };

  const statusColors = {
    'on-duty': 'bg-emerald-500',
    online: 'bg-emerald-500',
    busy: 'bg-amber-500',
    emergency: 'bg-[#EF4444] animate-pulse',
    offline: 'bg-slate-300',
  };

  const statusDotSizes = {
    xs: 'h-1.5 w-1.5 ring-1',
    sm: 'h-2 w-2 ring-1.5',
    md: 'h-2.5 w-2.5 ring-2',
    lg: 'h-3 w-3 ring-2',
    xl: 'h-3.5 w-3.5 ring-2',
  };

  const resolvedRole = role ? role.toLowerCase() : 'default';
  const roleColor = roleColors[resolvedRole] || roleColors.default;

  return (
    <div className={cn('relative inline-flex shrink-0 select-none', className)} {...props}>
      <div
        className={cn(
          'relative flex items-center justify-center rounded-full overflow-hidden border shadow-xs transition-transform',
          sizes[size] || sizes.md,
          roleColor
        )}
      >
        {src && !imageError ? (
          <img
            src={src}
            alt={name || 'Avatar'}
            onError={() => setImageError(true)}
            className="h-full w-full object-cover"
          />
        ) : (
          <span className="tracking-tight">{getInitials(name)}</span>
        )}
      </div>

      {status && (
        <span
          className={cn(
            'absolute bottom-0 right-0 rounded-full ring-white',
            statusColors[status] || statusColors.online,
            statusDotSizes[size] || statusDotSizes.md
          )}
          title={`Status: ${status}`}
        />
      )}
    </div>
  );
}

export default Avatar;
