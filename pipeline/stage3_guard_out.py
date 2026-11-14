"""Etapa 3 — GUARD-OUT: fuga de Canary, PII residual, anti-XSS (RF-13, RF-14).

Normaliza (NFKC, zero-width) antes de inspeccionar; compara el Canary sobre texto normalizado;
neutraliza HTML con ``html.escape``. Reutiliza ``core.pii_patterns`` (no importa de stage1).
"""

from __future__ import annotations

import html
import re
import time
from typing import Final

from core.context import GuardOutResult, PolicyStatus
from core.pii_patterns import find_pii
from core.text_normalizer import normalize_text

_CANARY_HEX_RE: Final = re.compile(r"\[\[CANARY-HMAC-([0-9A-Fa-f]+)\]\]")
_XSS_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"<script[\s>]", re.IGNORECASE),
    re.compile(r"</script>", re.IGNORECASE),
    re.compile(r"\bjavascript:", re.IGNORECASE),
    re.compile(r"\bonerror\s*=", re.IGNORECASE),
    re.compile(r"\bonload\s*=", re.IGNORECASE),
    re.compile(r"\bonclick\s*=", re.IGNORECASE),
    re.compile(r"<iframe[\s>]", re.IGNORECASE),
    re.compile(r"<img[\s>]", re.IGNORECASE),
    re.compile(r"<object[\s>]", re.IGNORECASE),
)

_UNVERIFIED_CLAIMS_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"\bha sido (?:formalmente )?aprobado sin revisi[oó]n\b", re.IGNORECASE),
    re.compile(r"\bresoluci[oó]n ministerial inexistente\b", re.IGNORECASE),
    re.compile(r"\baprobaci[oó]n autom[aá]tica vinculante e irrevocable\b", re.IGNORECASE),
)


def guard_out(llm_response: str, *, canary_token: str) -> GuardOutResult:
    """Inspecciona la respuesta del LLM antes de entregarla al ciudadano o funcionario.

    Verifica ausencia de fuga de Canary, PII residual no enmascarada y vectores de inyección XSS.
    Gatillo 2 (specs/02_guardian.spec.md).
    """
    start_time = time.perf_counter()

    # 1. Normalización previa a la inspección
    normalized = normalize_text(llm_response)

    # 2. Detección de fuga de Canary (total o parcial)
    canary_leaked = False
    if canary_token in llm_response or canary_token in normalized:
        canary_leaked = True
    else:
        # Extraer digest hex del Canary Token
        match = _CANARY_HEX_RE.search(canary_token)
        if match:
            hex_digest = match.group(1)
            # Fuga si aparece el hash hex completo o un fragmento relevante (>= 8 caracteres)
            if hex_digest.lower() in normalized.lower() or hex_digest.upper() in normalized:
                canary_leaked = True
            elif len(hex_digest) >= 8 and (
                hex_digest[:8].lower() in normalized.lower() or hex_digest[:8].upper() in normalized
            ):
                canary_leaked = True

    # 3. Detección de PII residual o alucinada (tokens [CEDULA_1] etc. son válidos)
    pii_matches = find_pii(normalized)
    residual_pii_detected = len(pii_matches) > 0

    # 4. Detección y neutralización de XSS / código ejecutable
    xss_detected = any(p.search(llm_response) or p.search(normalized) for p in _XSS_PATTERNS)

    # 5. Detección de afirmaciones no verificadas
    unverified_claims = any(
        p.search(llm_response) or p.search(normalized) for p in _UNVERIFIED_CLAIMS_PATTERNS
    )

    # 6. Decisión de política y saneamiento de salida
    if canary_leaked:
        allowed = False
        policy_status: PolicyStatus = "BLOCKED_CANARY_LEAK"
        sanitized_response = ""
    elif residual_pii_detected:
        allowed = False
        policy_status = "BLOCKED_PII_LEAK"
        sanitized_response = ""
    else:
        allowed = True
        policy_status = "CLEAN"
        sanitized_response = html.escape(llm_response)

    latency_ms = (time.perf_counter() - start_time) * 1000.0

    return GuardOutResult(
        allowed=allowed,
        canary_leaked=canary_leaked,
        residual_pii_detected=residual_pii_detected,
        xss_or_code_injected=xss_detected,
        unverified_claims_flag=unverified_claims,
        sanitized_response=sanitized_response,
        policy_status=policy_status,
        latency_ms=latency_ms,
    )
