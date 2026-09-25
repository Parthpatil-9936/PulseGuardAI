import React, { useEffect } from 'react';
import { X } from 'lucide-react';

/**
 * Modal Component
 * Glass backdrop with animated appearance
 * Can be locked (disableBackdropDismiss) for critical Tier 1 takeovers that require clinician action.
 */
export const Modal = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  size = 'md',
  disableBackdropDismiss = false,
  showCloseButton = true,
  className = '',
  criticalTier1 = false,
}) => {
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && !disableBackdropDismiss) {
        onClose?.();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, disableBackdropDismiss, onClose]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-[95vw] h-[90vh]',
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget && !disableBackdropDismiss) {
      onClose?.();
    }
  };

  return (
    <div
      onClick={handleBackdropClick}
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-all duration-300 ${
        criticalTier1 
          ? 'bg-red-950/80 backdrop-blur-xl' 
          : 'bg-slate-900/50 backdrop-blur-md'
      }`}
      role="dialog"
      aria-modal="true"
    >
      <div
        className={`w-full ${sizeClasses[size] || sizeClasses.md} rounded-2xl bg-white shadow-2xl border transition-all duration-300 transform scale-100 overflow-hidden ${
          criticalTier1 
            ? 'border-red-500 shadow-[0_0_50px_rgba(239,68,68,0.5)] ring-4 ring-red-500/30' 
            : 'border-slate-100/80 shadow-[0_20px_50px_rgba(0,0,0,0.15)]'
        } ${className}`}
      >
        {/* Header if title is passed */}
        {(title || showCloseButton) && (
          <div className={`px-6 py-4 flex items-center justify-between border-b ${
            criticalTier1 ? 'bg-red-600 text-white border-red-700' : 'bg-slate-50/70 border-slate-100'
          }`}>
            <div>
              {title && (
                <h3 className={`text-lg font-bold ${criticalTier1 ? 'text-white' : 'text-slate-900'}`}>
                  {title}
                </h3>
              )}
              {description && (
                <p className={`text-xs mt-0.5 ${criticalTier1 ? 'text-red-100' : 'text-slate-500'}`}>
                  {description}
                </p>
              )}
            </div>

            {showCloseButton && !disableBackdropDismiss && (
              <button
                type="button"
                onClick={onClose}
                className={`p-1.5 rounded-lg transition-colors ${
                  criticalTier1 
                    ? 'text-white/80 hover:text-white hover:bg-red-700' 
                    : 'text-slate-400 hover:text-slate-600 hover:bg-slate-100'
                }`}
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        )}

        {/* Modal body */}
        <div className="p-6 max-h-[80vh] overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
};

export const ModalHeader = ({ children, className = '' }) => (
  <div className={`mb-4 ${className}`}>{children}</div>
);

export const ModalFooter = ({ children, className = '' }) => (
  <div className={`mt-6 pt-4 border-t border-slate-100 flex items-center justify-end gap-3 ${className}`}>
    {children}
  </div>
);

export default Modal;
