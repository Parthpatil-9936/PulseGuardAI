import React from 'react';
import { cn } from '../../utils/cn';

export function Button({
  variant = 'primary',
  size = 'md',
  liftOnHover = true,
  loading = false,
  disabled = false,
  leftIcon,
  rightIcon,
  children,
  className,
  ...props
}) {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 select-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 disabled:pointer-events-none active:scale-[0.99]';

  const variants = {
    primary: 'bg-[#0EA5B7] hover:bg-[#0D8A9A] text-white focus:ring-[#0EA5B7]/40 shadow-sm shadow-teal-500/20',
    secondary: 'bg-[#3B82F6] hover:bg-blue-600 text-white focus:ring-blue-500/40 shadow-sm shadow-blue-500/20',
    danger: 'bg-[#EF4444] hover:bg-red-600 text-white focus:ring-red-500/40 shadow-sm shadow-red-500/20',
    outline: 'border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 hover:border-slate-300 focus:ring-slate-400/40 shadow-xs',
    ghost: 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 focus:ring-slate-300',
    glass: 'glass-panel hover:bg-white/80 text-slate-800 focus:ring-[#0EA5B7]/30',
  };

  const sizes = {
    sm: 'text-xs px-3 py-1.5 rounded-lg gap-1.5 h-8',
    md: 'text-sm px-4 py-2 rounded-xl gap-2 h-10',
    lg: 'text-base px-5 py-2.5 rounded-xl gap-2.5 h-12',
  };

  const liftStyles = (liftOnHover && !disabled && !loading) ? 'hover-lift' : '';

  return (
    <button
      className={cn(
        baseStyles,
        variants[variant] || variants.primary,
        sizes[size] || sizes.md,
        liftStyles,
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <svg
          className="animate-spin -ml-0.5 h-4 w-4 text-current"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="3"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      ) : leftIcon ? (
        <span className="shrink-0">{leftIcon}</span>
      ) : null}

      <span>{children}</span>

      {!loading && rightIcon && (
        <span className="shrink-0">{rightIcon}</span>
      )}
    </button>
  );
}

export default Button;
