import React from 'react';
import { ShieldCheck } from 'lucide-react';
import { CircularGauge } from '../../../components/ui/CircularGauge';
import { ShieldRuleMapping } from '../../../types';

interface ShieldFilterCardProps {
  rules: ShieldRuleMapping[];
  promptRiskPercentage?: number;
  riskLevelLabel?: string;
}

export const ShieldFilterCard: React.FC<ShieldFilterCardProps> = ({
  rules,
  promptRiskPercentage = 8,
  riskLevelLabel = '8% (Nivel Seguro)',
}) => {
  return (
    <div className="flex flex-col justify-between p-4 bg-white/95 dark:bg-slate-800/90 backdrop-blur-xs border border-slate-200 dark:border-slate-700/80 rounded-2xl shadow-xs transition-colors">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-100 dark:border-slate-700/50">
          <span className="font-bold text-xs text-slate-800 dark:text-slate-100 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-[#4f46e5]" />
            Shield Filtro
          </span>
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
        </div>

        {/* Sanitized Entity Rules Matching */}
        <div className="space-y-1.5 text-xs font-mono">
          {rules.map((rule, idx) => (
            <div 
              key={idx}
              className="flex items-center justify-between p-1.5 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-100 dark:border-slate-800/60"
            >
              <span className="text-[11px] px-2 py-0.5 rounded bg-indigo-50 text-[#4f46e5] dark:bg-indigo-950/60 dark:text-indigo-300 font-semibold">
                {rule.original}
              </span>
              <span className="text-slate-400">→</span>
              <span className="text-slate-600 dark:text-slate-300 font-medium">
                {rule.masked}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Risk Gauge Meter */}
      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-700/50 flex items-center space-x-3">
        <CircularGauge
          value={promptRiskPercentage}
          size={44}
          strokeWidth={3.5}
          color="text-emerald-500"
          trackColor="text-slate-200 dark:text-slate-700"
          label={`${promptRiskPercentage}%`}
        />
        <div className="text-left">
          <p className="text-xs font-bold text-slate-800 dark:text-slate-100 leading-tight">
            Riesgo Prompt Injection
          </p>
          <p className="text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold mt-0.5 font-mono">
            {riskLevelLabel}
          </p>
        </div>
      </div>
    </div>
  );
};
