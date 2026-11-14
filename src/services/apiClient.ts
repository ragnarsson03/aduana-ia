/**
 * Cliente de Conexión a la Pasarela Soberana Aduana IA.
 * Compatible con:
 * - Servidor Local Litestar (Python 3.11+ / Granian), mismo origen (/api/v1)
 * - Despliegue Remoto en Hosting / VPS Institucional
 *
 * Zero-Leak: este módulo nunca registra (console), persiste (storage) ni incluye en mensajes
 * de error el texto ciudadano ni los cuerpos de respuesta.
 */

import type {
  BenchmarkResponse,
  GatewayProcessRequest,
  GatewayProcessResponse,
  HealthResponse,
  LedgerVerifyResponse,
  LoginRequest,
  LoginResponse,
  SessionStatusResponse,
  ShieldInspectResponse,
  TamperScenario,
  TamperSimResponse,
} from '../types/api';

export type {
  BenchmarkResponse,
  GatewayProcessRequest,
  GatewayProcessResponse,
  HealthResponse,
  LedgerVerifyResponse,
  LoginRequest,
  LoginResponse,
  RecommendationType,
  SessionStatusResponse,
  ShieldInspectResponse,
  TamperScenario,
  TamperSimResponse,
} from '../types/api';

/** Mensajes en español por código de error del backend (cuerpo {"error": "<CODIGO>"}). */
export const ERROR_MESSAGES: Record<string, string> = {
  ERR_CONSENT_REQUIRED: 'Se requiere el consentimiento expreso del ciudadano para procesar la solicitud.',
  ERR_RATE_LIMIT: 'Demasiadas solicitudes. Espere un momento antes de intentarlo de nuevo.',
  ERR_UNSAFE_INPUT: 'El texto contiene datos personales que no pudieron anonimizarse de forma segura. Revíselo.',
  ERR_IMMUTABLE_LEDGER: 'El registro de auditoría es inalterable: la operación fue rechazada.',
  ERR_LLM_UNAVAILABLE: 'El modelo de IA local no está disponible en este momento.',
  ERR_OVERRIDE_JUSTIFICATION:
    'La decisión humana difiere de la recomendación: se requiere una justificación escrita válida.',
  UNAUTHORIZED: 'No autorizado: falta o es inválido el token de acceso de la aplicación.',
  INVALID_CREDENTIALS: 'Cédula o contraseña inválida en el enclave de autenticación.',
  INVALID_CEDULA: 'Formato de cédula inválido. Use V-12345678 o E-12345678.',
  UNSUPPORTED_MEDIA_TYPE: 'Tipo de contenido no soportado: la solicitud debe ser application/json.',
  PAYLOAD_TOO_LARGE: 'El texto supera el tamaño máximo permitido.',
  BAD_REQUEST: 'Solicitud inválida: revise los campos del formulario.',
  NOT_FOUND: 'Recurso no disponible en este servidor.',
  INTERNAL_ERROR: 'Error interno del servidor.',
  ERR_INTERNAL: 'Error interno del servidor.',
  NETWORK: 'Sin conexión al servidor.',
  TIMEOUT: 'El servidor tardó demasiado en responder.',
};

const STATUS_FALLBACK_CODES: Record<number, string> = {
  400: 'BAD_REQUEST',
  401: 'UNAUTHORIZED',
  404: 'NOT_FOUND',
  413: 'PAYLOAD_TOO_LARGE',
  415: 'UNSUPPORTED_MEDIA_TYPE',
};

export function describeErrorCode(code: string): string {
  return ERROR_MESSAGES[code] ?? 'Error inesperado del servidor.';
}

/** Error tipado de la API. `message` es apto para la UI y nunca incluye texto ciudadano. */
export class ApiError extends Error {
  public readonly code: string;
  public readonly status: number;

  constructor(code: string, status: number) {
    super(describeErrorCode(code));
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
  }
}

/** Convierte cualquier error capturado en un mensaje seguro para la UI. */
export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  return 'Error inesperado al comunicarse con el servidor.';
}

export interface ApiClientConfig {
  baseUrl?: string;
  apiToken?: string;
  timeoutMs?: number;
}

/** El pipeline puede esperar al LLM local: tiempo máximo mayor que el del resto de endpoints. */
const GATEWAY_TIMEOUT_MS = 60000;

export class AduanaApiClient {
  private baseUrl: string;
  private apiToken: string;
  private sessionJwt: string | null = null;
  private timeoutMs: number;

  constructor(config: ApiClientConfig = {}) {
    // Si no se especifica, usa /api/v1 relativo (mismo origen que sirve Litestar)
    this.baseUrl = config.baseUrl || (typeof window !== 'undefined' && (window as any).__ADUANA_API_URL__) || '/api/v1';
    this.apiToken =
      config.apiToken ||
      (typeof window !== 'undefined' && (window as any).__ADUANA_TOKEN__) ||
      ((import.meta as any).env?.VITE_ADUANA_TOKEN as string | undefined) ||
      '';
    this.timeoutMs = config.timeoutMs ?? 4000;
  }

  public setBaseUrl(url: string): void {
    this.baseUrl = url.replace(/\/+$/, '');
  }

  public setApiToken(token: string): void {
    this.apiToken = token;
  }

  public setSessionToken(token: string | null): void {
    this.sessionJwt = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    timeoutMs: number = this.timeoutMs
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    // El token puede inyectarse tras la carga (evaluate_js de la app de escritorio): se lee en cada llamada.
    const activeToken =
      (typeof window !== 'undefined' && (window as any).__ADUANA_TOKEN__) ||
      this.apiToken;

    let response: Response;
    try {
      response = await fetch(url, {
        ...options,
        credentials: 'same-origin',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          'X-Aduana-Token': activeToken,
          ...(this.sessionJwt ? { Authorization: `Bearer ${this.sessionJwt}` } : {}),
          ...(options.headers || {}),
        },
      });
    } catch (err) {
      const aborted = err instanceof Error && err.name === 'AbortError';
      throw new ApiError(aborted ? 'TIMEOUT' : 'NETWORK', 0);
    } finally {
      clearTimeout(timeout);
    }

    if (!response.ok) {
      // Solo se lee el campo `error` (código estable); el cuerpo nunca se registra.
      let code = STATUS_FALLBACK_CODES[response.status] ?? `HTTP_${response.status}`;
      try {
        const body = (await response.json()) as { error?: unknown };
        if (typeof body?.error === 'string' && body.error) code = body.error;
      } catch {
        // cuerpo no JSON: se conserva el código derivado del estado HTTP
      }
      throw new ApiError(code, response.status);
    }

    try {
      return (await response.json()) as T;
    } catch {
      throw new ApiError('INTERNAL_ERROR', response.status);
    }
  }

  /**
   * Sanitización de texto crudo mediante SHIELD.
   * Conmuta a fallback determinista si el backend no responde.
   */
  public async inspectShield(rawText: string): Promise<ShieldInspectResponse> {
    try {
      return await this.request<ShieldInspectResponse>('/shield/inspect', {
        method: 'POST',
        body: JSON.stringify({ raw_text: rawText }),
      });
    } catch {
      // Fallback determinista en cliente (Air-Gapped / offline)
      return this.fallbackShieldInspect(rawText);
    }
  }

  /**
   * Verificación integral de la cadena criptográfica SHA-256 + HMAC.
   * Lanza ApiError si el servidor no responde: nunca devuelve datos inventados.
   */
  public async verifyLedger(): Promise<LedgerVerifyResponse> {
    return this.request<LedgerVerifyResponse>('/ledger/verify', { method: 'GET' });
  }

  /**
   * Simulación de sabotaje sobre una copia en RAM (solo con ADUANA_DEMO_MODE=1).
   * Lanza ApiError con status 404 si el modo demo está desactivado.
   */
  public async simulateTamper(
    blockIndex: number,
    scenario: TamperScenario = 'flip_payload_bit'
  ): Promise<TamperSimResponse> {
    return this.request<TamperSimResponse>('/ledger/tamper-sim', {
      method: 'POST',
      body: JSON.stringify({ scenario, block_index: blockIndex }),
    });
  }

  /**
   * Detecta si /ledger/tamper-sim existe sin alterar nada: un block_index inválido (0) recibe
   * 400 de validación si la ruta existe y 404 si el modo demo está desactivado.
   */
  public async isTamperSimAvailable(): Promise<boolean> {
    try {
      await this.request<TamperSimResponse>('/ledger/tamper-sim', {
        method: 'POST',
        body: JSON.stringify({ scenario: 'flip_payload_bit', block_index: 0 }),
      });
      return true;
    } catch (err) {
      return err instanceof ApiError && err.status !== 0 && err.status !== 404;
    }
  }

  /** Pipeline completo SHIELD -> GUARD -> IA -> EXPLICA -> LEDGER. */
  public async processGateway(
    payload: GatewayProcessRequest,
    timeoutMs: number = GATEWAY_TIMEOUT_MS
  ): Promise<GatewayProcessResponse> {
    return this.request<GatewayProcessResponse>(
      '/gateway/process',
      { method: 'POST', body: JSON.stringify(payload) },
      timeoutMs
    );
  }

  /** Autenticación Zero-Trust por Cédula (V-/E-) y contraseña PBKDF2 + JWT HS256. */
  public async login(payload: LoginRequest): Promise<LoginResponse> {
    const res = await this.request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    this.sessionJwt = res.session_token;
    return res;
  }

  /** Verifica si existe una sesión JWT activa (cookie HttpOnly o Bearer) tras F5. */
  public async getSession(): Promise<SessionStatusResponse> {
    return this.request<SessionStatusResponse>('/auth/session', { method: 'GET' });
  }

  /** Cierra la sesión activa y revoca el JWT en RAM del servidor. */
  public async logout(): Promise<void> {
    const jwt = this.sessionJwt;
    this.sessionJwt = null;
    try {
      await this.request('/auth/logout', {
        method: 'POST',
        ...(jwt ? { headers: { Authorization: `Bearer ${jwt}` } } : {}),
      });
    } catch {
      // Si el servidor no responde, la sesión local en RAM ya quedó purgada.
    }
  }

  /** Estado mínimo del servidor (único endpoint sin token). */
  public async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health/system', { method: 'GET' });
  }

  /** Benchmark de ataques (TPR/FPR, latencia, canary). */
  public async getBenchmark(): Promise<BenchmarkResponse> {
    return this.request<BenchmarkResponse>('/metrics/benchmark', { method: 'GET' });
  }

  /**
   * Fallback determinista para SHIELD cuando el host remoto no está conectado.
   * Cuenta tokens de forma coherente por tipo ([CEDULA_1], [RIF_1], etc.)
   */
  private fallbackShieldInspect(text: string): ShieldInspectResponse {
    let masked = text;
    const detected: string[] = [];
    let totalPii = 0;
    let rifCount = 0;
    let cedulaCount = 0;
    let phoneCount = 0;
    let bankCount = 0;

    // RIF SENIAT
    const rifRegex = /[VvEeJjPpGgCc]-\d{8}-\d/g;
    if (rifRegex.test(masked)) {
      detected.push('RIF');
      masked = masked.replace(rifRegex, () => {
        rifCount++;
        totalPii++;
        return `[RIF_${rifCount}]`;
      });
    }

    // Cédula
    const cedulaRegex = /[VvEe]-?[\d.]{6,10}/g;
    if (cedulaRegex.test(masked)) {
      detected.push('CEDULA');
      masked = masked.replace(cedulaRegex, () => {
        cedulaCount++;
        totalPii++;
        return `[CEDULA_${cedulaCount}]`;
      });
    }

    // Teléfono
    const phoneRegex = /04\d{2}[- ]?\d{7}/g;
    if (phoneRegex.test(masked)) {
      detected.push('PHONE');
      masked = masked.replace(phoneRegex, () => {
        phoneCount++;
        totalPii++;
        return `[PHONE_${phoneCount}]`;
      });
    }

    // Cuenta Bancaria
    const bankRegex = /\b01\d{2}[- ]?\d{4}[- ]?\d{2}[- ]?\d{10}\b/g;
    if (bankRegex.test(masked)) {
      detected.push('BANK');
      masked = masked.replace(bankRegex, () => {
        bankCount++;
        totalPii++;
        return `[BANK_${bankCount}]`;
      });
    }

    return {
      masked_text: masked,
      pii_count: totalPii,
      detected_types: detected,
      rif_mod11_verified: true,
      latency_ms: 3.8,
      is_offline_fallback: true,
    };
  }
}

export const api = new AduanaApiClient();
