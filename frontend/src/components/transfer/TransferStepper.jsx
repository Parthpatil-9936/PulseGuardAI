import React from 'react';
import { CheckCircle2, Clock, AlertCircle, XCircle } from 'lucide-react';

/**
 * TransferStepper Component
 * Visual horizontal stepper for doctor patient transfer:
 * Pending -> Approved / Rejected -> Completed
 */
export const TransferStepper = ({ status = 'Pending', rejectionReason }) => {
  const isRejected = status === 'Rejected';

  const steps = [
    {
      id: 'pending',
      label: 'Request Submitted',
      sublabel: 'Pending Admin / Unit Review',
      isCurrent: status === 'Pending',
      isCompleted: status === 'Approved' || status === 'Completed' || status === 'Rejected',
    },
    {
      id: 'review',
      label: isRejected ? 'Transfer Rejected' : 'Approved',
      sublabel: isRejected ? rejectionReason || 'Capacity reached' : 'Accepted by Attending',
      isCurrent: status === 'Approved' || isRejected,
      isCompleted: status === 'Completed',
    },
    {
      id: 'completed',
      label: 'Handover Completed',
      sublabel: 'Roster & Ledger Synced',
      isCurrent: status === 'Completed',
      isCompleted: status === 'Completed',
    }
  ];

  return (
    <div className="w-full py-3">
      <div className="flex items-center justify-between relative">
        {/* Horizontal connecting background line */}
        <div className="absolute left-6 right-6 top-4 h-0.5 bg-slate-200 z-0" />

        {steps.map((step, index) => {
          let circleBg = 'bg-white border-slate-300 text-slate-400';
          let textColor = 'text-slate-500';

          if (isRejected && index === 1) {
            circleBg = 'bg-red-500 border-red-600 text-white shadow-sm';
            textColor = 'text-red-700 font-bold';
          } else if (step.isCompleted) {
            circleBg = 'bg-[#0EA5B7] border-teal-600 text-white shadow-sm';
            textColor = 'text-teal-900 font-bold';
          } else if (step.isCurrent) {
            circleBg = 'bg-amber-500 border-amber-600 text-white shadow-sm ring-4 ring-amber-100';
            textColor = 'text-amber-900 font-bold';
          }

          return (
            <div key={step.id} className="relative z-10 flex flex-col items-center text-center max-w-[140px]">
              {/* Step indicator circle */}
              <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center font-bold text-xs transition-all ${circleBg}`}>
                {isRejected && index === 1 ? (
                  <XCircle className="w-4 h-4" />
                ) : step.isCompleted ? (
                  <CheckCircle2 className="w-4 h-4" />
                ) : step.isCurrent ? (
                  <Clock className="w-4 h-4 animate-spin" style={{ animationDuration: '4s' }} />
                ) : (
                  <span>{index + 1}</span>
                )}
              </div>

              {/* Step Title & Subtitle */}
              <span className={`text-xs mt-2 leading-tight ${textColor}`}>
                {step.label}
              </span>
              <span className="text-[10px] text-slate-400 mt-0.5 leading-tight">
                {step.sublabel}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TransferStepper;
