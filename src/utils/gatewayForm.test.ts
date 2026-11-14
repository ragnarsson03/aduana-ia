import { describe, it, expect } from 'vitest';
import { DEFAULT_FEATURE_INPUTS, buildFeatures, validateGatewayForm, type GatewayFormValues } from './gatewayForm';

const valid: GatewayFormValues = {
  rawText: 'solicitud',
  cedula: 'V-12345678',
  consentGranted: true,
  purposeCode: 'BECA',
  features: DEFAULT_FEATURE_INPUTS,
  humanDecision: '',
  justification: '',
};

describe('validateGatewayForm', () => {
  it('acepta un formulario válido', () => expect(validateGatewayForm(valid)).toBeNull());
  it('rechaza texto vacío', () => expect(validateGatewayForm({ ...valid, rawText: '  ' })).toMatch(/texto/));
  it('rechaza cédula inválida', () => expect(validateGatewayForm({ ...valid, cedula: 'abc' })).toMatch(/Cédula/));
  it('rechaza propósito inválido', () => expect(validateGatewayForm({ ...valid, purposeCode: 'beca' })).toMatch(/Propósito/));
  it('rechaza variables no numéricas', () =>
    expect(validateGatewayForm({ ...valid, features: { ...valid.features, urgencia_medica: '' } })).toMatch(/numérico/));
  it('buildFeatures convierte a números', () => expect(buildFeatures(DEFAULT_FEATURE_INPUTS).tiempo_espera_dias).toBe(60));
});
