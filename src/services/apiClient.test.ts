import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { AduanaApiClient } from './apiClient';

describe('AduanaApiClient (Frontend Dispatch & Server Interconnect)', () => {
  let client: AduanaApiClient;

  beforeEach(() => {
    client = new AduanaApiClient({
      baseUrl: 'http://127.0.0.1:8000/api/v1',
      apiToken: 'test-sovereign-token',
      timeoutMs: 1500,
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('debe enviar la cabecera X-Aduana-Token y Content-Type adecuada', async () => {
    const mockResponse = {
      masked_text: 'Solicitante [CEDULA_1] con RIF [RIF_1]',
      pii_count: 2,
      detected_types: ['CEDULA', 'RIF'],
      rif_mod11_verified: true,
      latency_ms: 5.2,
    };

    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    const result = await client.inspectShield('Solicitante V-12345678 con RIF J-12345678-4');

    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const [url, options] = fetchSpy.mock.calls[0];

    expect(url).toBe('http://127.0.0.1:8000/api/v1/shield/inspect');
    expect(options?.headers).toMatchObject({
      'Content-Type': 'application/json',
      'X-Aduana-Token': 'test-sovereign-token',
    });
    expect(result.masked_text).toBe(mockResponse.masked_text);
    expect(result.is_offline_fallback).toBeUndefined();
  });

  it('debe conmutar a fallback determinista si el servidor responde con error de red', async () => {
    vi.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('Connection refused'));

    const result = await client.inspectShield('Solicitud con Cédula V-18492301 y RIF J-30123456-1');

    expect(result.is_offline_fallback).toBe(true);
    expect(result.masked_text).toContain('[CEDULA_1]');
    expect(result.masked_text).toContain('[RIF_1]');
    expect(result.pii_count).toBeGreaterThanOrEqual(2);
  });

  it('debe auditar la integridad del ledger consultando /ledger/verify', async () => {
    const mockLedgerResp = {
      is_valid: true,
      blocks_checked: 4,
      corrupted_block_index: null,
      failure_reason: null,
      head_hash: '0x3c99f18a2bc4e578...genesis',
      latency_ms: 10.4,
    };

    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockLedgerResp,
    } as Response);

    const verification = await client.verifyLedger();
    expect(verification.is_valid).toBe(true);
    expect(verification.blocks_checked).toBe(4);
    expect(verification.corrupted_block_index).toBeNull();
  });

  it('debe simular sabotaje de 1 bit y capturar el desajuste', async () => {
    const mockTamperResp = {
      simulated: true,
      scenario: 'flip_payload_bit',
      tampered_block_index: 4,
      detection: {
        is_valid: false,
        blocks_checked: 4,
        corrupted_block_index: 4,
        failure_reason: 'HMAC_SIGNATURE_FORGED',
        head_hash: '0xCORRUPTED',
        latency_ms: 14.1,
      },
    };

    vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => mockTamperResp,
    } as Response);

    const result = await client.simulateTamper(4, 'flip_payload_bit');
    expect(result.simulated).toBe(true);
    expect(result.tampered_block_index).toBe(4);
    expect(result.detection.is_valid).toBe(false);
  });

  it('permite cambiar la URL base dinámicamente para entornos Cloudflare Pages o Hosting', async () => {
    client.setBaseUrl('https://aduana-ia-gateway.workers.dev/api/v1');

    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: async () => ({ is_valid: true }),
    } as Response);

    await client.verifyLedger();

    expect(fetchSpy.mock.calls[0][0]).toBe(
      'https://aduana-ia-gateway.workers.dev/api/v1/ledger/verify'
    );
  });
});
