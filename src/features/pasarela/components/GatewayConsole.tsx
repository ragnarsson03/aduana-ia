import React, { useState } from 'react';
import { api, errorMessage } from '../../../services/apiClient';
import { useBackendStatus } from '../../../state/BackendStatus';
import { EXPLICA_FEATURE_NAMES, type ExplicaFeatureName } from '../../../types/api';
import {
  DEFAULT_FEATURE_INPUTS,
  FEATURE_LABELS,
  MAX_JUSTIFICATION_CHARS,
  MAX_RAW_TEXT_CHARS,
  PURPOSE_OPTIONS,
  RECOMMENDATION_OPTIONS,
  buildFeatures,
  validateGatewayForm,
  type GatewayFormValues,
} from '../../../utils/gatewayForm';
import { GatewayResultPanel } from './GatewayResultPanel';

interface Props {
  onNavigateToLedger?: () => void;
  onNavigateToExplica?: () => void;
  onNotify?: (msg: string) => void;
}

const INITIAL_VALUES: GatewayFormValues = {
  rawText: '',
  cedula: '',
  consentGranted: false,
  purposeCode: PURPOSE_OPTIONS[0],
  features: DEFAULT_FEATURE_INPUTS,
  humanDecision: '',
  justification: '',
};

const inputCls =
  'w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-sm text-slate-900 dark:text-slate-100';
const labelCls = 'block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1';

export const GatewayConsole: React.FC<Props> = ({ onNavigateToLedger, onNavigateToExplica, onNotify }) => {
  const { lastResult, setLastResult } = useBackendStatus();
  const [values, setValues] = useState<GatewayFormValues>(INITIAL_VALUES);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const patch = (p: Partial<GatewayFormValues>) => setValues((v) => ({ ...v, ...p }));
  const setFeature = (name: ExplicaFeatureName, value: string) =>
    setValues((v) => ({ ...v, features: { ...v.features, [name]: value } }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;
    const problem = validateGatewayForm(values);
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const result = await api.processGateway({
        raw_text: values.rawText,
        citizen_cedula: values.cedula.trim(),
        consent: { granted: values.consentGranted, purpose_code: values.purposeCode },
        features: buildFeatures(values.features),
        human_decision: values.humanDecision || null,
        override_justification: values.humanDecision && values.justification.trim() ? values.justification : null,
      });
      setLastResult(result);
      // Zero-Leak: el texto crudo del ciudadano no se conserva tras procesarlo.
      patch({ rawText: '' });
      onNotify?.(`Solicitud procesada. Recibo ${result.citizen_receipt_code}`);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="gateway-console">
      <form
        onSubmit={submit}
        noValidate
        className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4"
      >
        <h2 className="text-base font-bold text-slate-900 dark:text-white">Procesar trámite ciudadano</h2>

        <div>
          <label htmlFor="gw-raw-text" className={labelCls}>Texto del trámite</label>
          <textarea
            id="gw-raw-text"
            data-testid="gateway-raw-text"
            rows={5}
            maxLength={MAX_RAW_TEXT_CHARS}
            autoComplete="off"
            value={values.rawText}
            onChange={(e) => patch({ rawText: e.target.value })}
            className={inputCls}
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="gw-cedula" className={labelCls}>Cédula del ciudadano</label>
            <input
              id="gw-cedula"
              data-testid="gateway-cedula"
              autoComplete="off"
              placeholder="V-12345678"
              value={values.cedula}
              onChange={(e) => patch({ cedula: e.target.value })}
              className={inputCls}
            />
          </div>
          <div>
            <label htmlFor="gw-purpose" className={labelCls}>Propósito del consentimiento</label>
            <select
              id="gw-purpose"
              data-testid="gateway-purpose"
              value={values.purposeCode}
              onChange={(e) => patch({ purposeCode: e.target.value })}
              className={inputCls}
            >
              {PURPOSE_OPTIONS.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
        </div>

        <label className="flex items-center gap-2 text-sm text-slate-800 dark:text-slate-200">
          <input autoComplete="off"
            type="checkbox"
            data-testid="gateway-consent"
            checked={values.consentGranted}
            onChange={(e) => patch({ consentGranted: e.target.checked })}
          />
          El ciudadano otorga su consentimiento expreso para este propósito
        </label>

        <fieldset className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <legend className={labelCls}>Variables del modelo EXPLICA</legend>
          {EXPLICA_FEATURE_NAMES.map((name) => (
            <div key={name}>
              <label htmlFor={`gw-f-${name}`} className={labelCls}>{FEATURE_LABELS[name]}</label>
              <input autoComplete="off"
                id={`gw-f-${name}`}
                data-testid={`gateway-feature-${name}`}
                type="number"
                step="any"
                value={values.features[name]}
                onChange={(e) => setFeature(name, e.target.value)}
                className={inputCls}
              />
            </div>
          ))}
        </fieldset>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="gw-human" className={labelCls}>Decisión humana (opcional)</label>
            <select
              id="gw-human"
              data-testid="gateway-human-decision"
              value={values.humanDecision}
              onChange={(e) => patch({ humanDecision: e.target.value as GatewayFormValues['humanDecision'] })}
              className={inputCls}
            >
              <option value="">Adoptar la recomendación del modelo</option>
              {RECOMMENDATION_OPTIONS.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="gw-just" className={labelCls}>Justificación del override</label>
            <textarea autoComplete="off"
              id="gw-just"
              data-testid="gateway-override-justification"
              rows={2}
              maxLength={MAX_JUSTIFICATION_CHARS}
              value={values.justification}
              onChange={(e) => patch({ justification: e.target.value })}
              className={inputCls}
            />
          </div>
        </div>

        {error && (
          <p role="alert" data-testid="gateway-error" className="text-sm font-medium text-rose-700 dark:text-rose-300">
            {error}
          </p>
        )}

        <button
          type="submit"
          data-testid="gateway-submit"
          disabled={loading}
          className="px-4 py-2 text-sm font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          {loading ? 'Procesando…' : 'Procesar solicitud'}
        </button>
        {loading && (
          <span data-testid="gateway-loading" role="status" className="ml-3 text-xs text-slate-500">
            Ejecutando pipeline SHIELD, GUARD, IA, EXPLICA y LEDGER
          </span>
        )}
      </form>

      {lastResult && (
        <GatewayResultPanel
          result={lastResult}
          onNavigateToLedger={onNavigateToLedger}
          onNavigateToExplica={onNavigateToExplica}
        />
      )}
    </div>
  );
};
