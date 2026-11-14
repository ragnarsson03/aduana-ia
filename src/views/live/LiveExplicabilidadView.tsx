import React from 'react';
import { ShapBars } from '../../components/ui/ShapBars';
import { useBackendStatus } from '../../state/BackendStatus';

interface Props {
  onNavigateToPasarela: () => void;
}

/** Explicabilidad con el último resultado real de /gateway/process (sin mockData). */
export const LiveExplicabilidadView: React.FC<Props> = ({ onNavigateToPasarela }) => {
  const { lastResult } = useBackendStatus();
  const hasExplanation =
    lastResult && typeof lastResult.probability_score === 'number' && lastResult.linear_shap_values;

  return (
    <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6" data-testid="explica-live">
      <h2 className="text-xl font-bold text-slate-900 dark:text-white">Explicabilidad algorítmica</h2>

      {!hasExplanation ? (
        <div
          data-testid="explica-empty"
          className="rounded-2xl border border-dashed border-slate-300 dark:border-slate-700 p-6 text-sm text-slate-600 dark:text-slate-400 space-y-3"
        >
          <p>
            {lastResult
              ? 'La última solicitud fue bloqueada por política: no hay explicación disponible.'
              : 'Aún no hay resultados. Procese una solicitud en la Pasarela para ver su explicación.'}
          </p>
          <button
            type="button"
            onClick={onNavigateToPasarela}
            className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-300 dark:border-slate-700"
          >
            Ir a la Pasarela
          </button>
        </div>
      ) : (
        <section className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-5">
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
      )}
    </div>
  );
};
