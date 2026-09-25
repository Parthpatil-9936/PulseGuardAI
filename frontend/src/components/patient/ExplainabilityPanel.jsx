import React from 'react';
import { BrainCircuit, Info, AlertCircle, ArrowUpRight, ArrowDownRight, Activity } from 'lucide-react';

/**
 * ExplainabilityPanel (XAI)
 * Explains machine learning triage contributing factors with clear human-readable clinical rationale.
 * Displays mandatory disclaimer: "Model output — not a diagnosis"
 */
export const ExplainabilityPanel = ({
  factors = [],
  anomalyScore = 0.12,
  tier = 'normal',
}) => {
  const isCritical = tier === 'tier1' || anomalyScore >= 0.8;
  const isWarning = tier === 'tier2' || (anomalyScore >= 0.5 && anomalyScore < 0.8);

  return (
    <div className="bg-slate-50/70 rounded-2xl p-4 border border-slate-200/80 space-y-3">
      {/* Header & Disclaimer Chip */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <BrainCircuit className="w-4 h-4 text-[#0EA5B7]" />
          <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Model Explainability Factors (XAI)
          </h4>
        </div>

        {/* Mandatory Clinical Disclaimer Chip */}
        <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-slate-200/80 text-slate-700 text-[10px] font-semibold border border-slate-300">
          <Info className="w-3 h-3 text-slate-500" />
          <span>Model output — not a diagnosis</span>
        </div>
      </div>

      {/* Human-readable Contributing Factors */}
      <div className="space-y-2">
        {factors.length > 0 ? (
          factors.map((factor, index) => {
            const isNegative = factor.toLowerCase().includes('declining') || 
                              factor.toLowerCase().includes('breach') || 
                              factor.toLowerCase().includes('diverging') || 
                              factor.toLowerCase().includes('desaturation');

            return (
              <div
                key={index}
                className={`p-2.5 rounded-xl border text-xs flex items-start gap-2.5 ${
                  isCritical
                    ? 'bg-red-50/80 border-red-200 text-red-900 font-medium'
                    : isWarning
                    ? 'bg-amber-50/80 border-amber-200 text-amber-900 font-medium'
                    : 'bg-white border-slate-200 text-slate-700'
                }`}
              >
                {isNegative ? (
                  <ArrowDownRight className={`w-4 h-4 shrink-0 mt-0.5 ${isCritical ? 'text-red-600' : 'text-amber-600'}`} />
                ) : (
                  <Activity className="w-4 h-4 shrink-0 mt-0.5 text-teal-600" />
                )}
                <span className="leading-relaxed flex-1">{factor}</span>
              </div>
            );
          })
        ) : (
          <div className="p-3 bg-white rounded-xl border border-slate-200 text-xs text-slate-500">
            No anomalous multi-vital deviations detected. Deterministic parameters within normal range.
          </div>
        )}
      </div>

      {/* Inference Footnote */}
      <div className="pt-1 flex items-center justify-between text-[10px] font-mono text-slate-400">
        <span>Engine: 1D-CNN + IsoForest</span>
        <span>Local Edge Execution: &lt;5ms</span>
      </div>
    </div>
  );
};

export default ExplainabilityPanel;
