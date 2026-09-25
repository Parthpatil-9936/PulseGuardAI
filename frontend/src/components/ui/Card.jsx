import React from 'react';
import { cn } from '../../utils/cn';

export function Card({
  variant = 'elevated',
  hoverLift = false,
  className,
  children,
  ...props
}) {
  const variantStyles = {
    elevated: 'card-elevated',
    glass: 'glass-panel rounded-2xl',
    flat: 'bg-white rounded-2xl border border-slate-200 shadow-xs',
  };

  return (
    <div
      className={cn(
        variantStyles[variant] || variantStyles.elevated,
        hoverLift && 'hover-lift cursor-pointer',
        'overflow-hidden',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ className, children, ...props }) {
  return (
    <div
      className={cn('px-6 pt-5 pb-3 flex flex-col space-y-1.5', className)}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardTitle({ className, children, ...props }) {
  return (
    <h3
      className={cn('text-lg font-semibold text-slate-900 tracking-tight leading-snug', className)}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardDescription({ className, children, ...props }) {
  return (
    <p
      className={cn('text-sm text-slate-500 font-normal leading-relaxed', className)}
      {...props}
    >
      {children}
    </p>
  );
}

export function CardContent({ className, children, ...props }) {
  return (
    <div className={cn('px-6 py-4', className)} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({ className, children, ...props }) {
  return (
    <div
      className={cn('px-6 py-4 border-t border-slate-100/80 bg-slate-50/40 flex items-center justify-between', className)}
      {...props}
    >
      {children}
    </div>
  );
}

export default Card;
