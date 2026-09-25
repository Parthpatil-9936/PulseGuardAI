import React, { forwardRef } from 'react';
import { cn } from '../../utils/cn';
import { ChevronDown } from 'lucide-react';

export const Select = forwardRef(function Select(
  {
    label,
    error,
    helperText,
    required = false,
    leftIcon,
    options = [],
    size = 'md',
    id,
    disabled = false,
    className,
    wrapperClassName,
    children,
    ...props
  },
  ref
) {
  const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  const sizes = {
    sm: 'text-xs py-1.5 pl-3 pr-8 rounded-lg',
    md: 'text-sm py-2.5 pl-3.5 pr-10 rounded-xl',
    lg: 'text-base py-3 pl-4 pr-12 rounded-xl',
  };

  return (
    <div className={cn('w-full flex flex-col space-y-1.5', wrapperClassName)}>
      {label && (
        <label
          htmlFor={selectId}
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

        <select
          ref={ref}
          id={selectId}
          disabled={disabled}
          className={cn(
            'w-full bg-white border text-slate-900 transition-all duration-150 appearance-none cursor-pointer',
            'border-slate-200 hover:border-slate-300',
            'focus:outline-none focus:border-[#0EA5B7] focus:ring-4 focus:ring-[#0EA5B7]/15 focus:bg-white',
            'disabled:bg-slate-50 disabled:text-slate-400 disabled:border-slate-200 disabled:cursor-not-allowed',
            error && 'border-[#EF4444] focus:border-[#EF4444] focus:ring-red-400/20 text-red-900',
            leftIcon && 'pl-10',
            sizes[size] || sizes.md,
            className
          )}
          {...props}
        >
          {children ? (
            children
          ) : (
            options.map((opt) => (
              <option key={opt.value} value={opt.value} disabled={opt.disabled}>
                {opt.label}
              </option>
            ))
          )}
        </select>

        <div className="absolute right-3.5 pointer-events-none text-slate-400 flex items-center justify-center">
          <ChevronDown className="h-4 w-4" />
        </div>
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

export default Select;
