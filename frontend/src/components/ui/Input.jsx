import React, { forwardRef } from 'react';
import { cn } from '../../utils/cn';

export const Input = forwardRef(function Input(
  {
    label,
    error,
    helperText,
    required = false,
    leftIcon,
    rightIcon,
    size = 'md',
    id,
    disabled = false,
    className,
    wrapperClassName,
    ...props
  },
  ref
) {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  const sizes = {
    sm: 'text-xs py-1.5 px-3 rounded-lg',
    md: 'text-sm py-2.5 px-3.5 rounded-xl',
    lg: 'text-base py-3 px-4 rounded-xl',
  };

  return (
    <div className={cn('w-full flex flex-col space-y-1.5', wrapperClassName)}>
      {label && (
        <label
          htmlFor={inputId}
          className="text-xs font-semibold text-slate-700 select-none flex items-center justify-between"
        >
          <span>
            {label}
            {required && <span className="text-[#EF4444] ml-1">*</span>}
          </span>
        </label>
      )}

      <div className="relative flex items-center">
        {leftIcon && (
          <div className="absolute left-3.5 pointer-events-none text-slate-400 flex items-center justify-center">
            {leftIcon}
          </div>
        )}

        <input
          ref={ref}
          id={inputId}
          disabled={disabled}
          className={cn(
            'w-full bg-white border text-slate-900 placeholder:text-slate-400 transition-all duration-150',
            'border-slate-200 hover:border-slate-300',
            'focus:outline-none focus:border-[#0EA5B7] focus:ring-4 focus:ring-[#0EA5B7]/15 focus:bg-white',
            'disabled:bg-slate-50 disabled:text-slate-400 disabled:border-slate-200 disabled:cursor-not-allowed',
            error && 'border-[#EF4444] focus:border-[#EF4444] focus:ring-red-400/20 text-red-900',
            leftIcon && 'pl-10',
            rightIcon && 'pr-10',
            sizes[size] || sizes.md,
            className
          )}
          {...props}
        />

        {rightIcon && (
          <div className="absolute right-3.5 pointer-events-none text-slate-400 flex items-center justify-center">
            {rightIcon}
          </div>
        )}
      </div>

      {error ? (
        <p className="text-xs text-[#EF4444] font-medium flex items-center gap-1 mt-0.5">
          <span>{error}</span>
        </p>
      ) : helperText ? (
        <p className="text-xs text-slate-500 font-normal mt-0.5">
          {helperText}
        </p>
      ) : null}
    </div>
  );
});

export default Input;
