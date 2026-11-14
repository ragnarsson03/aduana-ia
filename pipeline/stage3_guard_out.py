"""Etapa 3 — GUARD-OUT: fuga de Canary, PII residual, anti-XSS (RF-13, RF-14).

Normaliza (NFKC, zero-width) antes de inspeccionar; compara el Canary sobre texto normalizado;
neutraliza HTML con ``html.escape``. Reutiliza ``core.pii_patterns`` (no importa de stage1).
"""

from __future__ import annotations

import base64
import html
import re
import time
from collections.abc import Mapping
from typing import Final

from core.context import GuardOutResult, PolicyStatus
from core.pii_patterns import find_pii
from core.text_normalizer import normalize_text

_CANARY_HEX_RE: Final = re.compile(r"\[\[CANARY-HMAC-([0-9A-Fa-f]+)\]\]")
_XSS_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"<script[\s>]", re.IGNORECASE),
    re.compile(r"</script>", re.IGNORECASE),
    re.compile(r"\bjavascript\s*:", re.IGNORECASE),
    re.compile(r"\bvbscript\s*:", re.IGNORECASE),
    re.compile(r"\bdata:(?:image/svg|text/html|application/)", re.IGNORECASE),
    re.compile(r"\]\(\s*//", re.IGNORECASE),
    re.compile(r"<input[\s>]", re.IGNORECASE),
    re.compile(r"<details[\s>]", re.IGNORECASE),
    re.compile(r"<iframe[\s>]", re.IGNORECASE),
    re.compile(r"<img[\s>]", re.IGNORECASE),
    re.compile(r"<object[\s>]", re.IGNORECASE),
    re.compile(r"\bon[a-z]{3,15}\s*=", re.IGNORECASE),
)

_UNVERIFIED_CLAIMS_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"\bha sido (?:formalmente )?aprobado sin revisi[oó]n\b", re.IGNORECASE),
    re.compile(r"\bresoluci[oó]n ministerial inexistente\b", re.IGNORECASE),
    re.compile(r"\baprobaci[oó]n autom[aá]tica vinculante e irrevocable\b", re.IGNORECASE),
)


def restore_pii_tokens(sanitized_response: str, token_map: Mapping[str, str] | None) -> str:
    """Restaura en RAM los tokens [KIND_n] desde EphemeralVault tras superar GUARD-OUT."""
    if not sanitized_response or not token_map:
        return sanitized_response
    restored = sanitized_response
    for token, original in token_map.items():
        if token in restored:
            restored = restored.replace(token, html.escape(original))
    return restored


def guard_out(
    llm_response: str,
    *,
    canary_token: str,
    token_map: Mapping[str, str] | None = None,
) -> GuardOutResult:
    """Inspecciona la respuesta del LLM antes de entregarla al ciudadano o funcionario.

    Verifica ausencia de fuga de Canary, PII residual no enmascarada y vectores de inyección XSS.
    Si ``token_map`` (procedente de ``EphemeralVault``) está presente y la respuesta es segura,
    rehidrata los tokens ``[CEDULA_1]`` etc. en ``restored_response`` sin alterar
    ``sanitized_response`` (que permanece anonimizada para el sellado en el Ledger).
    Gatillo 2 (specs/02_guardian.spec.md).
    """
    start_time = time.perf_counter()

    # 1. Normalización previa a la inspección (fail-closed ante bombas NFKC)
    try:
        normalized = normalize_text(llm_response)
    except ValueError:
        return GuardOutResult(
            allowed=False,
            canary_leaked=False,
            residual_pii_detected=False,
            xss_or_code_injected=False,
            unverified_claims_flag=False,
            sanitized_response="",
            policy_status="BLOCKED_INJECTION",
            latency_ms=(time.perf_counter() - start_time) * 1000.0,
        )

    # 2. Detección de fuga de Canary (total, parcial, fragmentada o codificada)
    canary_leaked = False
    if canary_token in llm_response or canary_token in normalized:
        canary_leaked = True
    else:
        # Base64 del canary token
        b64_token = base64.b64encode(canary_token.encode("utf-8")).decode("utf-8")
        if b64_token in llm_response or b64_token in normalized:
            canary_leaked = True

        match = _CANARY_HEX_RE.search(canary_token)
        if not canary_leaked and match:
            hex_digest = match.group(1).upper()
            compact = re.sub(r"[\s\.\-_/]+", "", normalized).upper()
            raw_compact = re.sub(r"[\s\.\-_/]+", "", llm_response).upper()

            # Base64 del hex digest
            b64_hex = base64.b64encode(hex_digest.encode("utf-8")).decode("utf-8")
            if b64_hex in llm_response or b64_hex in normalized:
                canary_leaked = True
            elif hex_digest in compact or hex_digest in raw_compact:
                canary_leaked = True
            elif hex_digest[::-1] in compact or hex_digest[::-1] in raw_compact:
                canary_leaked = True
            elif any(
                hex_digest[i : i + 6] in compact or hex_digest[i : i + 6] in raw_compact
                for i in range(len(hex_digest) - 5)
            ):
                canary_leaked = True
            elif (hex_digest[: len(hex_digest) // 2] in compact) and (
                hex_digest[len(hex_digest) // 2 :] in compact
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
        restored_response = ""
    elif xss_detected:
        allowed = False
        policy_status = "BLOCKED_INJECTION"
        sanitized_response = ""
        restored_response = ""
    elif residual_pii_detected:
        allowed = False
        policy_status = "BLOCKED_PII_LEAK"
        sanitized_response = ""
        restored_response = ""
    else:
        allowed = True
        policy_status = "CLEAN"
        sanitized_response = html.escape(llm_response)
        restored_response = restore_pii_tokens(sanitized_response, token_map)

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
        restored_response=restored_response,
    )
