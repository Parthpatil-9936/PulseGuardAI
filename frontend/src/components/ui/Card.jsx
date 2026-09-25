import React from 'react';

/**
 * Card Component
 * Variants:
 * - 'elevated': solid white background, rounded-2xl, dual-layer shadow
 * - 'glass': backdrop-blur-lg, bg-white/60, border border-white/40, layered shadow
 * - 'flat': subtle border, flat background
 */
export const Card = ({
  children,
  variant = 'elevated',
  hoverLift = false,
  className = '',
  onClick,
  ...props
}) => {
  const variantClasses = {
    elevated: 'card-elevated',
    glass: 'glass-panel rounded-2xl',
    flat: 'bg-white rounded-2xl border border-slate-200/80 shadow-sm',
    dark: 'glass-panel-dark rounded-2xl text-white',
  };

  const liftClass = hoverLift ? 'hover-lift cursor-pointer' : '';

  return (
    <div
      onClick={onClick}
      className={`${variantClasses[variant] || variantClasses.elevated} ${liftClass} transition-all duration-200 overflow-hidden ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader = ({ children, className = '' }) => (
  <div className={`p-5 pb-3 flex flex-col gap-1 ${className}`}>
    {children}
  </div>
);

export const CardTitle = ({ children, className = '' }) => (
  <h3 className={`text-base font-semibold text-slate-900 leading-tight tracking-tight ${className}`}>
    {children}
  </h3>
);

export const CardDescription = ({ children, className = '' }) => (
  <p className={`text-xs text-slate-500 font-normal leading-relaxed ${className}`}>
    {children}
  </p>
);

export const CardContent = ({ children, className = '' }) => (
  <div className={`p-5 pt-0 ${className}`}>
    {children}
  </div>
);

export const CardFooter = ({ children, className = '' }) => (
  <div className={`p-4 pt-3 bg-slate-50/60 border-t border-slate-100 flex items-center justify-between gap-3 ${className}`}>
    {children}
  </div>
);

export default Card;
