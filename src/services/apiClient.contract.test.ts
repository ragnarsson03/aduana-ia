import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { AduanaApiClient, ApiError } from './apiClient';

const ok = (body: unknown) => ({ ok: true, status: 200, json: async () => body }) as Response;
const fail = (status: number, body?: unknown) =>
  ({
    ok: false,
    status,
    json: async () => {
      if (body === undefined) throw new Error('no json');
      return body;
    },
  }) as Response;

const gatewayPayload = {
  raw_text: 'texto',
  citizen_cedula: 'V-12345678',
  consent: { granted: true, purpose_code: 'BECA' },
  features: { tiempo_espera_dias: 10 },
};

describe('AduanaApiClient: métodos del contrato real y mapeo de errores', () => {
  let client: AduanaApiClient;

  beforeEach(() => {
    client = new AduanaApiClient({ baseUrl: '/api/v1', apiToken: 'tok', timeoutMs: 500 });
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('processGateway hace POST JSON a /gateway/process con token y devuelve la respuesta', async () => {
    const body = { policy_status: 'CLEAN', citizen_receipt_code: 'R-1', block_index: 3, chain_verified: true };
    const spy = vi.spyOn(global, 'fetch').mockResolvedValueOnce(ok(body));
    const res = await client.processGateway(gatewayPayload);
    const [url, opts] = spy.mock.calls[0];
    expect(url).toBe('/api/v1/gateway/process');
    expect(opts?.method).toBe('POST');
    expect(opts?.headers).toMatchObject({ 'Content-Type': 'application/json', 'X-Aduana-Token': 'tok' });
    expect(JSON.parse(opts?.body as string)).toEqual(gatewayPayload);
    expect(res.block_index).toBe(3);
  });

  it('getHealth y getBenchmark usan GET sobre sus rutas', async () => {
    const spy = vi
      .spyOn(global, 'fetch')
      .mockResolvedValueOnce(ok({ status: 'ok', ledger_mode: 'ephemeral', implemented_stages: [] }))
      .mockResolvedValueOnce(ok({ total: 100, tpr: 1, fpr: 0, mean_latency_ms: 2, canary_leaks_neutralized_pct: 100 }));
    expect((await client.getHealth()).status).toBe('ok');
    expect((await client.getBenchmark()).total).toBe(100);
    expect(spy.mock.calls[0][0]).toBe('/api/v1/health/system');
    expect(spy.mock.calls[1][0]).toBe('/api/v1/metrics/benchmark');
    expect(spy.mock.calls[1][1]?.method).toBe('GET');
  });

  it.each([
    [403, 'ERR_CONSENT_REQUIRED', /consentimiento/i],
    [429, 'ERR_RATE_LIMIT', /Demasiadas solicitudes/],
    [422, 'ERR_UNSAFE_INPUT', /datos personales/],
    [409, 'ERR_IMMUTABLE_LEDGER', /inalterable/],
    [503, 'ERR_LLM_UNAVAILABLE', /IA local/],
    [422, 'ERR_OVERRIDE_JUSTIFICATION', /justificación/],
    [401, 'UNAUTHORIZED', /No autorizado/],
  ])('mapea %i %s a un mensaje en español', async (status, code, pattern) => {
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(fail(status, { error: code }));
    const err = await client.processGateway(gatewayPayload).catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe(code);
    expect(err.status).toBe(status);
    expect(err.message).toMatch(pattern);
  });

  it('deriva el código del estado HTTP si el cuerpo no es JSON (415, 413, 401)', async () => {
    const spy = vi.spyOn(global, 'fetch');
    spy.mockResolvedValueOnce(fail(415));
    expect((await client.getBenchmark().catch((e) => e)).code).toBe('UNSUPPORTED_MEDIA_TYPE');
    spy.mockResolvedValueOnce(fail(413));
    expect((await client.getBenchmark().catch((e) => e)).message).toMatch(/tamaño máximo/);
    spy.mockResolvedValueOnce(fail(401));
    expect((await client.getBenchmark().catch((e) => e)).code).toBe('UNAUTHORIZED');
  });

  it('un fallo de red produce ApiError NETWORK y no incluye el texto ciudadano', async () => {
    vi.spyOn(global, 'fetch').mockRejectedValueOnce(new TypeError('secreto V-99999999'));
    const err = await client.processGateway(gatewayPayload).catch((e) => e);
    expect(err.code).toBe('NETWORK');
    expect(err.message).not.toContain('99999999');
  });

  it('un abort por tiempo se reporta como TIMEOUT', async () => {
    const abort = Object.assign(new Error('aborted'), { name: 'AbortError' });
    vi.spyOn(global, 'fetch').mockRejectedValueOnce(abort);
    expect((await client.getHealth().catch((e) => e)).code).toBe('TIMEOUT');
  });

  it('verifyLedger ya no inventa datos cuando el servidor falla', async () => {
    vi.spyOn(global, 'fetch').mockRejectedValueOnce(new Error('down'));
    await expect(client.verifyLedger()).rejects.toBeInstanceOf(ApiError);
  });

  it('isTamperSimAvailable: 404 es false, 400 es true, red caída es false', async () => {
    const spy = vi.spyOn(global, 'fetch');
    spy.mockResolvedValueOnce(fail(404, { error: 'NOT_FOUND' }));
    expect(await client.isTamperSimAvailable()).toBe(false);
    spy.mockResolvedValueOnce(fail(400, { error: 'validation' }));
    expect(await client.isTamperSimAvailable()).toBe(true);
    spy.mockRejectedValueOnce(new Error('down'));
    expect(await client.isTamperSimAvailable()).toBe(false);
  });

  it('no usa console al procesar un error', async () => {
    const log = vi.spyOn(console, 'log');
    const err = vi.spyOn(console, 'error');
    vi.spyOn(global, 'fetch').mockResolvedValueOnce(fail(500, { error: 'INTERNAL_ERROR' }));
    await client.processGateway(gatewayPayload).catch(() => undefined);
    expect(log).not.toHaveBeenCalled();
    expect(err).not.toHaveBeenCalled();
  });
});
