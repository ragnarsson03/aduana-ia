import React from 'react';
import { ShapBars } from '../../../components/ui/ShapBars';
import type { GatewayProcessResponse } from '../../../types/api';

const RECOMMENDATION_LABELS: Record<string, string> = {
  PRIORIDAD_ALTA: 'Prioridad alta',
  REVISION_ESTANDAR: 'Revisión estándar',
  RECAUDOS_INCOMPLETOS: 'Recaudos incompletos',
  BLOQUEADO_SEGURIDAD: 'Bloqueado por seguridad',
};

interface Props {
  result: GatewayProcessResponse;
  onNavigateToLedger?: () => void;
  onNavigateToExplica?: () => void;
}

const Row: React.FC<{ label: string; testId: string; children: React.ReactNode }> = ({ label, testId, children }) => (
  <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-3 py-1.5 border-b border-slate-100 dark:border-slate-800 text-sm">
    <dt className="w-52 shrink-0 text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</dt>
    <dd data-testid={testId} className="font-mono break-all text-slate-900 dark:text-slate-100">
      {children}
    </dd>
  </div>
);

/** Todo el contenido se renderiza como texto de React (nunca como HTML). */
export const GatewayResultPanel: React.FC<Props> = ({ result, onNavigateToLedger, onNavigateToExplica }) => {
  const blocked = result.policy_status !== 'CLEAN';
  const btn =
    'px-3 py-1.5 text-xs font-semibold rounded-lg border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800';
  return (
    <section
      data-testid="gateway-result"
      aria-live="polite"
      className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4"
    >
      <h3 className="text-sm font-bold text-slate-900 dark:text-white">Resultado del pipeline</h3>
      <dl>
        <Row label="Estado de política" testId="gateway-policy-status">{result.policy_status}</Row>
        <Row label="Recomendación del modelo" testId="gateway-recommendation">
          {RECOMMENDATION_LABELS[result.model_recommendation] ?? result.model_recommendation}
        </Row>
        <Row label="Decisión humana" testId="gateway-human-decision-result">
          {RECOMMENDATION_LABELS[result.human_decision] ?? result.human_decision}
          {result.human_override ? ' (override)' : ''}
        </Row>
        <Row label="Probabilidad" testId="gateway-probability">
          {typeof result.probability_score === 'number'
            ? `${(result.probability_score * 100).toFixed(1)} %`
            : 'No disponible'}
        </Row>
        <Row label="Recibo ciudadano" testId="gateway-receipt">{result.citizen_receipt_code}</Row>
        <Row label="Bloque del ledger" testId="gateway-block-index">{String(result.block_index)}</Row>
        <Row label="Cadena verificada" testId="gateway-chain-verified">{result.chain_verified ? 'Sí' : 'No'}</Row>
        <Row label="Latencia" testId="gateway-latency">{result.latency_ms.toFixed(1)} ms</Row>
      </dl>

      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">Texto enmascarado (SHIELD)</h4>
        <pre
          data-testid="gateway-masked-text"
          className="whitespace-pre-wrap break-words text-xs font-mono p-3 rounded-lg bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-200"
        >
          {result.masked_text ?? 'Solicitud bloqueada: no se generó texto enmascarado.'}
        </pre>
      </div>

      {!blocked && (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-1">
            Respuesta de la IA {result.ai_generated_notice ? '(generada por IA)' : ''}
          </h4>
          <pre
            data-testid="gateway-sanitized-response"
            className="whitespace-pre-wrap break-words text-xs font-mono p-3 rounded-lg bg-slate-50 dark:bg-slate-950 text-slate-800 dark:text-slate-200"
          >
            {result.sanitized_response}
          </pre>
        </div>
      )}

      {result.linear_shap_values && (
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-500 mb-2">
            Contribuciones SHAP lineales
          </h4>
          <ShapBars values={result.linear_shap_values} testIdPrefix="gateway-shap" />
        </div>
      )}

      <div className="flex flex-wrap gap-2 pt-1">
        {onNavigateToLedger && (
          <button type="button" onClick={onNavigateToLedger} className={btn}>
            Ver en el ledger
          </button>
        )}
        {onNavigateToExplica && (
          <button type="button" onClick={onNavigateToExplica} className={btn}>
            Ver explicabilidad
          </button>
        )}
      </div>
    </section>
  );
};
