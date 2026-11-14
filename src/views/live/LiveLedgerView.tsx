import React, { useEffect, useState } from 'react';
import { api, errorMessage } from '../../services/apiClient';
import { useBackendStatus } from '../../state/BackendStatus';
import {
  TAMPER_SCENARIOS,
  type LedgerVerifyResponse,
  type TamperScenario,
  type TamperSimResponse,
} from '../../types/api';

interface Props {
  onNotify: (msg: string) => void;
}

const SCENARIO_LABELS: Record<TamperScenario, string> = {
  flip_payload_bit: 'Alterar un bit del contenido',
  recompute_sha_without_key: 'Recalcular SHA-256 sin la clave HMAC',
  break_prev_link: 'Romper el enlace con el bloque previo',
  flip_override: 'Invertir la marca de override humano',
};

const FAILURE_LABELS: Record<string, string> = {
  HASH_MISMATCH: 'El hash del bloque no coincide con su contenido',
  PREV_HASH_LINK_BROKEN: 'El enlace con el bloque previo está roto',
  HMAC_SIGNATURE_FORGED: 'La firma HMAC no es válida (posible falsificación)',
  GENESIS_LINK_BROKEN: 'El bloque génesis no enlaza correctamente',
  INDEX_GAP: 'Hay un salto en los índices de la cadena',
  TAIL_TRUNCATED: 'La cola de la cadena fue truncada',
};

const Field: React.FC<{ label: string; testId: string; children: React.ReactNode }> = ({ label, testId, children }) => (
  <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-3 py-1.5 border-b border-slate-100 dark:border-slate-800 text-sm">
    <dt className="w-48 shrink-0 text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</dt>
    <dd data-testid={testId} className="font-mono break-all text-slate-900 dark:text-slate-100">{children}</dd>
  </div>
);

const VerificationDetails: React.FC<{ v: LedgerVerifyResponse; prefix: string }> = ({ v, prefix }) => (
  <dl>
    <Field label="Cadena válida" testId={`${prefix}-is-valid`}>{v.is_valid ? 'true' : 'false'}</Field>
    <Field label="Bloques revisados" testId={`${prefix}-blocks-checked`}>{String(v.blocks_checked)}</Field>
    <Field label="Hash de cabeza" testId={`${prefix}-head-hash`}>{v.head_hash ?? 'Sin bloques'}</Field>
    {!v.is_valid && (
      <>
        <Field label="Bloque corrupto" testId={`${prefix}-corrupted-index`}>{String(v.corrupted_block_index)}</Field>
        <Field label="Motivo del fallo" testId={`${prefix}-failure-reason`}>
          {v.failure_reason ? `${v.failure_reason} - ${FAILURE_LABELS[v.failure_reason] ?? 'Fallo de integridad'}` : 'Desconocido'}
        </Field>
      </>
    )}
  </dl>
);

export const LiveLedgerView: React.FC<Props> = ({ onNotify }) => {
  const { lastResult } = useBackendStatus();
  const [verification, setVerification] = useState<LedgerVerifyResponse | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState<string | null>(null);

  const [demoAvailable, setDemoAvailable] = useState(false);
  const [scenario, setScenario] = useState<TamperScenario>('flip_payload_bit');
  const [blockIndex, setBlockIndex] = useState('1');
  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState<TamperSimResponse | null>(null);
  const [simError, setSimError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api.isTamperSimAvailable().then((ok) => {
      if (!cancelled) setDemoAvailable(ok);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const verify = async () => {
    setVerifying(true);
    setVerifyError(null);
    try {
      const v = await api.verifyLedger();
      setVerification(v);
      onNotify(v.is_valid ? `Cadena íntegra: ${v.blocks_checked} bloques` : 'Integridad comprometida detectada');
    } catch (err) {
      setVerifyError(errorMessage(err));
    } finally {
      setVerifying(false);
    }
  };

  // Índices válidos del backend: 1..blocks_checked-1 (el génesis, 0, no es simulable).
  const maxIndex = verification ? verification.blocks_checked - 1 : null;
  const parsedIndex = Number(blockIndex);
  const indexValid =
    Number.isInteger(parsedIndex) && parsedIndex >= 0 && (maxIndex === null || parsedIndex <= maxIndex);

  const simulate = async () => {
    if (!indexValid) {
      setSimError('Índice de bloque inválido. Verifique el ledger primero para conocer el rango.');
      return;
    }
    setSimulating(true);
    setSimError(null);
    try {
      setSimResult(await api.simulateTamper(parsedIndex, scenario));
    } catch (err) {
      setSimError(errorMessage(err));
      if (err instanceof Error && 'status' in err && (err as { status: number }).status === 404) {
        setDemoAvailable(false);
      }
    } finally {
      setSimulating(false);
    }
  };

  const btn = 'px-4 py-2 text-sm font-semibold rounded-lg disabled:opacity-60';
  const input =
    'rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 px-3 py-2 text-sm text-slate-900 dark:text-slate-100';

  return (
    <div className="w-full max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6" data-testid="ledger-live">
      <h2 className="text-xl font-bold text-slate-900 dark:text-white">Registro de auditoría inalterable</h2>

      {lastResult && (
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Último bloque generado en esta sesión:{' '}
          <span data-testid="ledger-last-block" className="font-mono">{lastResult.block_index}</span>
        </p>
      )}

      <section className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 space-y-4">
        <button
          type="button"
          data-testid="ledger-verify-button"
          onClick={verify}
          disabled={verifying}
          className={`${btn} bg-indigo-600 text-white hover:bg-indigo-700`}
        >
          {verifying ? 'Verificando…' : 'Verificar integridad del ledger'}
        </button>
        {verifyError && (
          <p role="alert" data-testid="ledger-verify-error" className="text-sm font-medium text-rose-700 dark:text-rose-300">
            {verifyError}
          </p>
        )}
        {verification && (
          <div data-testid="ledger-verify-result" aria-live="polite">
            <VerificationDetails v={verification} prefix="ledger-verify" />
          </div>
        )}
      </section>

      {demoAvailable && (
        <section
          data-testid="tamper-section"
          className="rounded-2xl border-2 border-dashed border-amber-400 bg-amber-50 dark:bg-amber-950/30 p-5 space-y-4"
        >
          <h3 className="text-sm font-bold text-amber-900 dark:text-amber-200">
            SIMULACIÓN de manipulación (no modifica el ledger real)
          </h3>
          <div className="flex flex-wrap gap-3 items-end">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Escenario
              <select
                data-testid="tamper-scenario"
                value={scenario}
                onChange={(e) => setScenario(e.target.value as TamperScenario)}
                className={`${input} block mt-1`}
              >
                {TAMPER_SCENARIOS.map((s) => (
                  <option key={s} value={s}>{SCENARIO_LABELS[s]}</option>
                ))}
              </select>
            </label>
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Bloque {maxIndex !== null && maxIndex >= 0 ? `(0 a ${maxIndex})` : '(verifica primero)'}
              <input autoComplete="off"
                data-testid="tamper-block-index"
                type="number"
                min={0}
                max={maxIndex ?? undefined}
                value={blockIndex}
                onChange={(e) => setBlockIndex(e.target.value)}
                className={`${input} block mt-1 w-28`}
              />
            </label>
            <button
              type="button"
              data-testid="tamper-button"
              onClick={simulate}
              disabled={simulating}
              className={`${btn} bg-amber-600 text-white hover:bg-amber-700`}
            >
              {simulating ? 'Simulando…' : 'Simular manipulación'}
            </button>
          </div>
          {simError && (
            <p role="alert" data-testid="tamper-error" className="text-sm font-medium text-rose-700 dark:text-rose-300">
              {simError}
            </p>
          )}
          {simResult && (
            <div data-testid="tamper-result" aria-live="polite" className="space-y-2">
              <p className="text-xs font-bold uppercase text-amber-900 dark:text-amber-200">
                SIMULACIÓN · simulated:{' '}
                <span data-testid="tamper-simulated">{String(simResult.simulated)}</span> · escenario {simResult.scenario}{' '}
                · bloque <span data-testid="tamper-block">{simResult.tampered_block_index}</span>
              </p>
              <VerificationDetails v={simResult.detection} prefix="tamper-detection" />
            </div>
          )}
        </section>
      )}
    </div>
  );
};
