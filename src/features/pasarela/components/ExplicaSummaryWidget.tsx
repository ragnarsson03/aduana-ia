import React from 'react';
import { ArrowRight } from 'lucide-react';
import { ScholarshipEvaluationDossier } from '../../../types';

interface ExplicaSummaryWidgetProps {
  dossier: ScholarshipEvaluationDossier;
  onViewFullExplica?: () => void;
}

export const ExplicaSummaryWidget: React.FC<ExplicaSummaryWidgetProps> = ({
  dossier,
  onViewFullExplica,
}) => {
  return (
    <section 
      className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/90 dark:border-slate-800 p-6 shadow-xs transition-colors"
      data-purpose="explainability-dashboard"
      id="sec-explicabilidad"
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-6">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-white">
            Explicabilidad — Beca Estudiantil
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Transparencia algorítmica y desglose de ponderaciones
          </p>
        </div>

        <span className="px-3 py-1 font-mono text-xs font-bold rounded-lg bg-slate-100 dark:bg-slate-800 text-[#4f46e5] dark:text-indigo-300 border border-slate-200 dark:border-slate-700">
          {dossier.expedienteId}
        </span>
      </div>

      {/* Top Row: Decision Meter & Fairness Monitor (2 Cards) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        
        {/* Decision Circular Gauge (78/100 Aprobado) */}
        <div className="p-4 bg-slate-50/80 dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-slate-700/60 flex items-center space-x-4">
          <div className="relative w-20 h-20 shrink-0 flex items-center justify-center">
            <svg className="w-20 h-20 transform -rotate-90" viewBox="0 0 36 36">
              <path 
                className="text-slate-200 dark:text-slate-700" 
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="3.5"
              />
              <path 
                className="text-[#4f46e5] dark:text-indigo-400" 
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" 
                fill="none" 
                stroke="currentColor" 
                strokeDasharray="78, 100" 
                strokeLinecap="round" 
                strokeWidth="3.5"
              />
            </svg>
            <div className="absolute text-center leading-none">
              <span className="block text-sm font-black font-mono text-slate-800 dark:text-white">
                {dossier.score}/100
              </span>
            </div>
          </div>

          <div>
            <p className="text-xs uppercase tracking-wider font-bold text-slate-400 font-mono">
              Decisión del Modelo
            </p>
            <p className="text-base font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">
              {dossier.verdictLabel}
            </p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 font-mono">
              Umbral mínimo: {dossier.minimumThreshold} pts
            </p>
          </div>
        </div>

        {/* Fairness Monitor (Donut Chart) */}
        <div className="p-4 bg-slate-50/80 dark:bg-slate-800/60 rounded-2xl border border-slate-100 dark:border-slate-700/60 flex items-center space-x-4">
          <div className="relative w-20 h-20 shrink-0 flex items-center justify-center">
            <svg className="w-20 h-20 transform -rotate-90" viewBox="0 0 36 36">
              {/* Donut Segments */}
              <circle cx="18" cy="18" fill="none" r="14" stroke="#6366f1" strokeDasharray="45 100" strokeWidth="4" />
              <circle cx="18" cy="18" fill="none" r="14" stroke="#3b82f6" strokeDasharray="30 100" strokeDashoffset="-45" strokeWidth="4" />
              <circle cx="18" cy="18" fill="none" r="14" stroke="#10b981" strokeDasharray="25 100" strokeDashoffset="-75" strokeWidth="4" />
            </svg>
            <span className="absolute text-[10px] font-bold text-slate-600 dark:text-slate-300 text-center leading-tight">
              Regiones<br />Equidad
            </span>
          </div>

          <div>
            <p className="text-xs uppercase tracking-wider font-bold text-slate-400 font-mono">
              Monitor de Equidad
            </p>
            <p className="text-xs font-bold text-slate-800 dark:text-slate-100 mt-0.5">
              Sin sesgo territorial
            </p>
            <span className="inline-block mt-1 text-[11px] font-mono text-[#4f46e5] dark:text-indigo-400 font-semibold bg-indigo-50 dark:bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-200 dark:border-indigo-800/50">
              {dossier.parityBadgeText}
            </span>
          </div>
        </div>

      </div>

      {/* Bottom: Variables (Regresión Logística / Feature Weights) */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono">
            Variables (Regresión Logística)
          </h4>
          <span className="text-[11px] text-slate-400 font-mono">Contribución Marginal</span>
        </div>

        <div className="space-y-3">
          {dossier.variables.map((v) => (
            <div key={v.id}>
              <div className="flex justify-between text-xs font-medium text-slate-700 dark:text-slate-200 mb-1">
                <span>{v.name}</span>
                <span className={`font-mono font-bold ${v.isPositive ? 'text-[#4f46e5] dark:text-indigo-400' : 'text-slate-500 dark:text-slate-400'}`}>
                  {v.displayValue}
                </span>
              </div>
              <div className={`w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden ${!v.isPositive ? 'flex justify-end' : ''}`}>
                <div 
                  className={`h-2.5 rounded-full transition-all duration-500 ${
                    v.isPositive ? 'bg-[#4f46e5] dark:bg-indigo-500' : 'bg-slate-400 dark:bg-slate-600'
                  }`}
                  style={{ width: `${v.barWidthPercentage}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer Navigation Link */}
      {onViewFullExplica && (
        <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800 flex justify-end">
          <button
            onClick={onViewFullExplica}
            className="text-xs font-semibold text-[#4f46e5] dark:text-indigo-400 hover:underline inline-flex items-center gap-1"
          >
            <span>Ver Desglose Completo y Paridad Regional</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </section>
  );
};
