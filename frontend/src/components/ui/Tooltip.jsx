import React, { useState } from 'react';

/**
 * Tooltip Component
 * Accessible tooltip with hover delay, arrow, and smooth appearance
 */
export const Tooltip = ({
  content,
  children,
  position = 'top',
  delay = 150,
  className = '',
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [timeoutId, setTimeoutId] = useState(null);

  const showTooltip = () => {
    const id = setTimeout(() => setIsVisible(true), delay);
    setTimeoutId(id);
  };

  const hideTooltip = () => {
    if (timeoutId) clearTimeout(timeoutId);
    setIsVisible(false);
  };

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  const arrowClasses = {
    top: 'top-full left-1/2 -translate-x-1/2 border-t-slate-800 border-l-transparent border-r-transparent border-b-transparent',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-slate-800 border-l-transparent border-r-transparent border-t-transparent',
    left: 'left-full top-1/2 -translate-y-1/2 border-l-slate-800 border-t-transparent border-b-transparent border-r-transparent',
    right: 'right-full top-1/2 -translate-y-1/2 border-r-slate-800 border-t-transparent border-b-transparent border-l-transparent',
  };

  if (!content) return children;

  return (
    <div 
      className="relative inline-flex items-center" 
      onMouseEnter={showTooltip} 
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
    >
      {children}
      {isVisible && (
        <div
          role="tooltip"
          className={`
            absolute z-50 px-2.5 py-1 text-xs font-medium text-white bg-slate-800/95
            rounded-lg shadow-lg backdrop-blur-sm pointer-events-none whitespace-nowrap
            transition-opacity duration-150 animate-in fade-in zoom-in-95
            ${positionClasses[position] || positionClasses.top}
            ${className}
          `}
        >
          {content}
          <div 
            className={`absolute border-4 w-0 h-0 ${arrowClasses[position] || arrowClasses.top}`} 
          />
        </div>
      )}
    </div>
  );
};

export default Tooltip;
