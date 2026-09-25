import React from 'react';

/**
 * Avatar Component
 * Displays initials or image with role accents and status indicators
 */
export const Avatar = ({
  name = 'Clinician',
  src,
  size = 'md',
  role = 'doctor',
  status, // 'online' | 'busy' | 'offline'
  className = '',
}) => {
  const getInitials = (name) => {
    if (!name) return 'PG';
    const parts = name.trim().split(' ');
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  const sizeClasses = {
    xs: 'w-7 h-7 text-[10px]',
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm font-semibold',
    lg: 'w-12 h-12 text-base font-bold',
    xl: 'w-16 h-16 text-xl font-bold',
  };

  const roleColors = {
    admin: 'bg-purple-100 text-purple-700 border-purple-200',
    doctor: 'bg-teal-50 text-[#0D8A9A] border-teal-200',
    nurse: 'bg-blue-50 text-[#2563EB] border-blue-200',
    patient: 'bg-slate-100 text-slate-700 border-slate-200',
  };

  const statusColors = {
    online: 'bg-emerald-500',
    busy: 'bg-amber-500',
    offline: 'bg-slate-400',
  };

  return (
    <div className="relative inline-block shrink-0">
      <div
        className={`
          flex items-center justify-center rounded-full border shadow-sm select-none
          ${sizeClasses[size] || sizeClasses.md}
          ${roleColors[role] || roleColors.doctor}
          ${className}
        `}
      >
        {src ? (
          <img
            src={src}
            alt={name}
            className="w-full h-full object-cover rounded-full"
          />
        ) : (
          <span>{getInitials(name)}</span>
        )}
      </div>

      {status && (
        <span
          className={`
            absolute bottom-0 right-0 block rounded-full ring-2 ring-white
            ${size === 'xs' || size === 'sm' ? 'w-2 h-2' : 'w-2.5 h-2.5'}
            ${statusColors[status] || statusColors.online}
          `}
          title={`Status: ${status}`}
        />
      )}
    </div>
  );
};

export default Avatar;
