/**
 * Tipos del contrato HTTP del backend Aduana IA (reflejan app/schemas.py y core/context.py).
 * Solo describen datos en tránsito: nada de esto se persiste en el navegador.
 */

export type RecommendationType =
  | 'PRIORIDAD_ALTA'
  | 'REVISION_ESTANDAR'
  | 'RECAUDOS_INCOMPLETOS'
  | 'BLOQUEADO_SEGURIDAD';

export type PolicyStatus =
  | 'CLEAN'
  | 'BLOCKED_INJECTION'
  | 'BLOCKED_CANARY_LEAK'
  | 'BLOCKED_NO_CONSENT'
  | 'BLOCKED_PII_LEAK';

export type ChainFailureReason =
  | 'HASH_MISMATCH'
  | 'PREV_HASH_LINK_BROKEN'
  | 'HMAC_SIGNATURE_FORGED'
  | 'GENESIS_LINK_BROKEN'
  | 'INDEX_GAP'
  | 'TAIL_TRUNCATED';

export type TamperScenario =
  | 'flip_payload_bit'
  | 'recompute_sha_without_key'
  | 'break_prev_link'
  | 'flip_override';

export const TAMPER_SCENARIOS: readonly TamperScenario[] = [
  'flip_payload_bit',
  'recompute_sha_without_key',
  'break_prev_link',
  'flip_override',
];

/** Variables del modelo institucional EXPLICA (pipeline/stage5_explica.py). */
export const EXPLICA_FEATURE_NAMES = [
  'tiempo_espera_dias',
  'vulnerabilidad_socioeconomica',
  'completitud_recaudos',
  'urgencia_medica',
  'complejidad_caso',
] as const;

export type ExplicaFeatureName = (typeof EXPLICA_FEATURE_NAMES)[number];
export type ExplicaFeatures = Record<ExplicaFeatureName, number>;

export interface ShieldInspectResponse {
  masked_text: string;
  pii_count: number;
  detected_types: string[];
  rif_mod11_verified: boolean | null;
  latency_ms: number;
  is_offline_fallback?: boolean;
}

export interface LedgerVerifyResponse {
  is_valid: boolean;
  blocks_checked: number;
  corrupted_block_index: number | null;
  failure_reason: ChainFailureReason | string | null;
  head_hash: string | null;
  latency_ms: number;
}

export interface TamperSimResponse {
  simulated: boolean;
  scenario: TamperScenario;
  tampered_block_index: number;
  detection: LedgerVerifyResponse;
}

export interface GatewayProcessRequest {
  raw_text: string;
  citizen_cedula: string;
  consent: {
    granted: boolean;
    purpose_code: string;
  };
  features: Record<string, number>;
  human_decision?: RecommendationType | null;
  override_justification?: string | null;
}

export interface GatewayProcessResponse {
  request_id: string;
  timestamp_utc: string;
  policy_status: PolicyStatus;
  masked_text: string | null;
  sanitized_response: string;
  ai_generated_notice: boolean;
  model_recommendation: RecommendationType;
  human_decision: RecommendationType;
  human_override: boolean;
  citizen_receipt_code: string;
  block_index: number;
  chain_verified: boolean;
  latency_ms: number;
  probability_score?: number | null;
  linear_shap_values?: Record<string, number> | null;
}

export interface BenchmarkResponse {
  total: number;
  tpr: number;
  fpr: number;
  mean_latency_ms: number;
  canary_leaks_neutralized_pct: number;
}

export interface HealthResponse {
  status: string;
  ledger_mode: 'ephemeral' | 'persistent';
  implemented_stages: string[];
}
