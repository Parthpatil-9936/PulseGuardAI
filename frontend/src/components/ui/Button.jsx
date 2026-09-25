import React from 'react';

/**
 * Button component
 * Variants: primary, secondary, danger, ghost, outline
 * Features lift-on-hover, loading state with spinner, disabled state, size scaling
 */
export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  liftOnHover = true,
  loading = false,
  disabled = false,
  icon: Icon,
  iconPosition = 'left',
  className = '',
  onClick,
  type = 'button',
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none select-none';

  const sizeClasses = {
    sm: 'text-xs px-3 py-1.5 gap-1.5',
    md: 'text-sm px-4 py-2 gap-2',
    lg: 'text-base px-5 py-2.5 gap-2.5',
    icon: 'p-2 rounded-lg'
  };

  const variantClasses = {
    // Primary: teal-500: #0EA5B7, teal-600: #0D8A9A
    primary: 'bg-[#0EA5B7] hover:bg-[#0D8A9A] text-white shadow-sm hover:shadow focus:ring-[#0EA5B7]/50',
    // Secondary: blue-500: #3B82F6
    secondary: 'bg-[#3B82F6] hover:bg-[#2563EB] text-white shadow-sm hover:shadow focus:ring-[#3B82F6]/50',
    // Danger: tier1-red: #EF4444
    danger: 'bg-[#EF4444] hover:bg-[#DC2626] text-white shadow-sm hover:shadow-red-500/20 focus:ring-[#EF4444]/50',
    outline: 'border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 shadow-sm focus:ring-slate-300',
    ghost: 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/80 focus:ring-slate-300',
    glass: 'glass-panel text-slate-800 hover:bg-white/80 border border-white/60 focus:ring-teal-400/50',
  };

  const liftClass = liftOnHover && !disabled && !loading ? 'hover:-translate-y-0.5 hover:shadow-md' : '';

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={`${baseClasses} ${sizeClasses[size] || sizeClasses.md} ${variantClasses[variant] || variantClasses.primary} ${liftClass} ${className}`}
      {...props}
    >
      {loading ? (
        <svg className="animate-spin -ml-0.5 h-4 w-4 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      ) : Icon && iconPosition === 'left' ? (
        <Icon className="w-4 h-4 shrink-0" />
      ) : null}

      <span>{children}</span>

      {!loading && Icon && iconPosition === 'right' && (
        <Icon className="w-4 h-4 shrink-0" />
      )}
    </button>
  );
};

export default Button;
