import { EXPLICA_FEATURE_NAMES, type ExplicaFeatureName, type RecommendationType } from '../types/api';

export const CEDULA_PATTERN = /^[A-Za-z]?-?[0-9.]{5,12}$/;
export const PURPOSE_PATTERN = /^[A-Z0-9_]{3,32}$/;
export const MAX_RAW_TEXT_CHARS = 20000;
export const MAX_JUSTIFICATION_CHARS = 500;

export const PURPOSE_OPTIONS: readonly string[] = [
  'BECA',
  'BECA_UNIVERSITARIA',
  'SUBSIDIO_SOCIAL',
  'TRAMITE_GENERAL',
];

export const RECOMMENDATION_OPTIONS: readonly RecommendationType[] = [
  'PRIORIDAD_ALTA',
  'REVISION_ESTANDAR',
  'RECAUDOS_INCOMPLETOS',
  'BLOQUEADO_SEGURIDAD',
];

export const FEATURE_LABELS: Record<ExplicaFeatureName, string> = {
  tiempo_espera_dias: 'Tiempo de espera (días)',
  vulnerabilidad_socioeconomica: 'Vulnerabilidad socioeconómica (0-1)',
  completitud_recaudos: 'Completitud de recaudos (0-1)',
  urgencia_medica: 'Urgencia médica (0-1)',
  complejidad_caso: 'Complejidad del caso (0-1)',
};

export const DEFAULT_FEATURE_INPUTS: Record<ExplicaFeatureName, string> = {
  tiempo_espera_dias: '60',
  vulnerabilidad_socioeconomica: '0.5',
  completitud_recaudos: '0.7',
  urgencia_medica: '0.25',
  complejidad_caso: '0.5',
};

export interface GatewayFormValues {
  rawText: string;
  cedula: string;
  consentGranted: boolean;
  purposeCode: string;
  features: Record<ExplicaFeatureName, string>;
  humanDecision: RecommendationType | '';
  justification: string;
}

/** Devuelve un mensaje de error en español o null si el formulario es válido. */
export function validateGatewayForm(v: GatewayFormValues): string | null {
  if (!v.rawText.trim()) return 'Escriba el texto del trámite.';
  if (v.rawText.length > MAX_RAW_TEXT_CHARS) return `El texto supera ${MAX_RAW_TEXT_CHARS} caracteres.`;
  if (!CEDULA_PATTERN.test(v.cedula.trim())) return 'Cédula inválida (ejemplo: V-12345678).';
  if (!PURPOSE_PATTERN.test(v.purposeCode)) return 'Propósito inválido (3-32 caracteres A-Z, 0-9, _).';
  for (const name of EXPLICA_FEATURE_NAMES) {
    const raw = v.features[name].trim();
    if (raw === '' || !Number.isFinite(Number(raw))) return `Valor numérico inválido: ${FEATURE_LABELS[name]}.`;
  }
  if (v.justification.length > MAX_JUSTIFICATION_CHARS) return 'La justificación es demasiado larga.';
  return null;
}

export function buildFeatures(inputs: Record<ExplicaFeatureName, string>): Record<ExplicaFeatureName, number> {
  return {
    tiempo_espera_dias: Number(inputs.tiempo_espera_dias),
    vulnerabilidad_socioeconomica: Number(inputs.vulnerabilidad_socioeconomica),
    completitud_recaudos: Number(inputs.completitud_recaudos),
    urgencia_medica: Number(inputs.urgencia_medica),
    complejidad_caso: Number(inputs.complejidad_caso),
  };
}
