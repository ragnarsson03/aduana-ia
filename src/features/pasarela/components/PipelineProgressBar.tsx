import React from 'react';
import { Check } from 'lucide-react';

interface PipelineProgressBarProps {
  completedStepCount?: number; // 0 to 5
  totalSteps?: number;
  label?: string;
  sublabel?: string;
}

export const PipelineProgressBar: React.FC<PipelineProgressBarProps> = ({
  completedStepCount = 4,
  totalSteps = 5,
  label = 'Estado del Pipeline',
  sublabel = '80% completado (Fase Guard-Out)',
}) => {
  return (
    <div className="mt-4 p-3.5 bg-white/90 dark:bg-slate-800/90 rounded-2xl border border-slate-200 dark:border-slate-700/80 shadow-2xs">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold text-slate-700 dark:text-slate-200">
          {label}
        </span>
        <span className="text-[11px] font-medium text-[#4f46e5] dark:text-indigo-400 font-mono">
          {sublabel}
        </span>
      </div>

      <div className="relative flex items-center justify-between">
        {/* Connected Track Line Background */}
        <div className="absolute inset-x-3 top-1/2 -translate-y-1/2 h-1 bg-slate-200 dark:bg-slate-700 z-0" />
        
        {/* Active Progress Line */}
        <div 
          className="absolute left-3 top-1/2 -translate-y-1/2 h-1 bg-[#4f46e5] z-0 transition-all duration-500"
          style={{ width: `${((completedStepCount - 1) / (totalSteps - 1)) * 100}%` }}
        />

        {/* 5 Steps */}
        {Array.from({ length: totalSteps }).map((_, idx) => {
          const isDone = idx < completedStepCount;
          const isCurrent = idx === completedStepCount;

          return (
            <div
              key={idx}
              className={`relative z-10 w-6 h-6 rounded-full flex items-center justify-center ring-4 ring-white dark:ring-slate-800 text-xs transition-all ${
                isDone
                  ? 'bg-[#4f46e5] text-white'
                  : isCurrent
                  ? 'bg-white dark:bg-slate-800 border-2 border-[#4f46e5] text-[#4f46e5]'
                  : 'bg-slate-200 dark:bg-slate-700 text-slate-400'
              }`}
            >
              {isDone ? (
                <Check className="w-3.5 h-3.5 stroke-[2.5]" />
              ) : isCurrent ? (
                <span className="w-1.5 h-1.5 rounded-full bg-[#4f46e5] animate-pulse" />
              ) : (
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
