import React from 'react';
import { ShapBars } from '../../components/ui/ShapBars';
import { useBackendStatus } from '../../state/BackendStatus';
import { ExplicabilidadView } from '../ExplicabilidadView';

interface Props {
  onNavigateToPasarela: () => void;
  onNotify?: (msg: string) => void;
}

/** Explicabilidad con el último resultado real de /gateway/process integrado con los gráficos institucionales. */
export const LiveExplicabilidadView: React.FC<Props> = ({ onNotify }) => {
  const { lastResult } = useBackendStatus();
  const hasExplanation =
    lastResult && typeof lastResult.probability_score === 'number' && lastResult.linear_shap_values;

  return (
    <div className="w-full space-y-6" data-testid="explica-live">
      {hasExplanation ? (
        <div className="max-w-5xl mx-auto px-4 sm:px-6 pt-4">
          <section className="rounded-2xl border border-indigo-200 dark:border-indigo-800/80 bg-white dark:bg-slate-900 p-5 space-y-5 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-600 dark:text-indigo-400 font-bold">
                  ÚLTIMA INFERENCIA EN TIEMPO REAL
                </span>
                <h3 className="text-base font-bold text-slate-900 dark:text-white mt-0.5">
                  Resultado Procesado en Enclave Edge
                </h3>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
                Live Gateway
              </span>
            </div>
            <dl className="grid gap-4 sm:grid-cols-3 text-sm">
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Probabilidad</dt>
                <dd data-testid="explica-probability" className="text-2xl font-bold font-mono text-slate-900 dark:text-white">
                  {((lastResult.probability_score as number) * 100).toFixed(1)} %
                </dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Recomendación</dt>
                <dd data-testid="explica-recommendation" className="font-mono text-slate-900 dark:text-slate-100">
                  {lastResult.model_recommendation}
                </dd>
              </div>
              <div>
                <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Decisión humana</dt>
                <dd data-testid="explica-human-decision" className="font-mono text-slate-900 dark:text-slate-100">
                  {lastResult.human_decision}
                  {lastResult.human_override ? ' (override)' : ''}
                </dd>
              </div>
            </dl>
            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2">
                Contribuciones SHAP lineales (positivo favorece prioridad)
              </h3>
              <ShapBars values={lastResult.linear_shap_values as Record<string, number>} testIdPrefix="explica-shap" />
            </div>
            <p className="text-xs text-slate-500">
              Recibo ciudadano <span data-testid="explica-receipt" className="font-mono">{lastResult.citizen_receipt_code}</span>
            </p>
          </section>
        </div>
      ) : (
        <div data-testid="explica-empty" className="hidden" aria-hidden="true" />
      )}

      {/* Siempre renderizar el panel completo de gráficos y auditoría algorítmica */}
      <ExplicabilidadView onNotify={(msg) => onNotify?.(msg)} />
    </div>
  );
};
