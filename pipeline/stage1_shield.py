"""Etapa 1 — SHIELD: anonimización soberana (RF-04..RF-07, CA-01). Gatillo 1.

Flujo: ``normalize_text`` -> neutraliza literales ``[KIND_n]`` preexistentes -> ``find_pii`` ->
tokens coherentes por identidad dentro del trámite (``[CEDULA_1]``...) -> repite hasta punto fijo
(máx. 6 pasadas con progreso: p. ej. cédulas pegadas) -> mapa token->original SOLO a la bóveda.

Decisiones:
- Fail-closed: si tras 6 pasadas queda PII detectable se lanza ``ShieldResidualPiiError`` y no se
  guarda nada en la bóveda; ningún llamador puede recibir texto con PII residual.
- ``pii_count``: ocurrencias enmascaradas (no valores únicos).
- ``rif_mod11_verified``: ``None`` sin RIF; ``True`` si todos validan; ``False`` si alguno falla.
- ``validation_passed``: ningún RIF falló el Módulo 11 (el residual ya no es posible: lanza).
- El mapa guarda el texto NORMALIZADO (NFKC), no el crudo, y una sola forma por identidad.
"""

from __future__ import annotations

import re
import time
from collections import Counter
from dataclasses import dataclass, field

from core.context import ShieldMeta
from core.crypto import rif_mod11_valid
from core.ephemeral_vault import EphemeralVault
from core.errors import ShieldResidualPiiError
from core.pii_patterns import KINDS, _extend_digit_bounds, find_pii
from core.text_normalizer import normalize_text

MAX_PASSES = 6
_CEDULA_PARTS = re.compile(r"([VEve])?[ .\-]?([0-9.]+)")
_TOKEN_LITERAL = re.compile(r"\[(?:" + "|".join(KINDS) + r")_[0-9]+\]")


@dataclass(slots=True)
class _State:
    counters: Counter[str] = field(default_factory=Counter)
    tokens: dict[tuple[str, str], str] = field(default_factory=dict)
    token_map: dict[str, str] = field(default_factory=dict)
    rif_results: list[bool] = field(default_factory=list)
    kinds: set[str] = field(default_factory=set)
    occurrences: int = 0


def _identity_key(kind: str, original: str) -> str:
    """Clave de coherencia: el mismo identificador en formatos distintos comparte token."""
    if kind == "CEDULA":
        match = _CEDULA_PARTS.fullmatch(original)
        if match:
            digits = match.group(2).replace(".", "").lstrip("0") or "0"
            return f"{(match.group(1) or 'V').upper()}{digits}"
    if kind == "RIF":
        return "".join(ch for ch in original.upper() if ch.isalnum())
    if kind in {"PHONE", "BANK"}:
        digits = "".join(ch for ch in original if ch.isdigit())
        return digits[-10:] if kind == "PHONE" else digits
    return " ".join(original.casefold().split())


_ANY_TOKEN = re.compile(r"\[(?:" + "|".join(KINDS) + r")_[0-9]+\]")
_WINDOW = 80


def _token_windows(text: str) -> list[tuple[int, int]]:
    """Ventanas alrededor de cada token de salida, fusionadas, para el chequeo de residual."""
    windows: list[tuple[int, int]] = []
    for token in _ANY_TOKEN.finditer(text):
        lo, hi = max(0, token.start() - _WINDOW), min(len(text), token.end() + _WINDOW)
        lo, hi = _extend_digit_bounds(text, lo, hi)
        if windows and lo <= windows[-1][1]:
            windows[-1] = (windows[-1][0], max(windows[-1][1], hi))
        else:
            windows.append((lo, hi))
    return windows


def _mask_pass(text: str, matches: tuple, state: _State) -> str:
    parts: list[str] = []
    cursor = 0
    for match in matches:
        original = text[match.start : match.end]
        identity = (match.kind, _identity_key(match.kind, original))
        token = state.tokens.get(identity)
        if token is None:
            state.counters[match.kind] += 1
            token = f"[{match.kind}_{state.counters[match.kind]}]"
            state.tokens[identity] = token
            state.token_map[token] = original
        if match.kind == "RIF":
            state.rif_results.append(rif_mod11_valid(original))
        state.kinds.add(match.kind)
        state.occurrences += 1
        parts.append(text[cursor : match.start])
        parts.append(token)
        cursor = match.end
    parts.append(text[cursor:])
    return "".join(parts)


def shield(
    request_id: str,
    raw_text: str,
    *,
    vault: EphemeralVault,
    blind_citizen_id: str,
) -> tuple[str, ShieldMeta]:
    """Devuelve ``(masked_text, meta)``. El mapa token->PII va solo a ``vault``."""
    started = time.perf_counter()
    try:
        normalized = normalize_text(raw_text)
    except ValueError:
        raise ShieldResidualPiiError("Texto no anonimizable de forma segura.") from None
    text = _TOKEN_LITERAL.sub(lambda m: "［" + m.group(0)[1:], normalized)
    state = _State()

    matches = find_pii(text)  # único escaneo completo
    remaining = len(text)
    for _ in range(MAX_PASSES):
        if not matches:
            break
        text = _mask_pass(text, matches, state)
        # Newly exposed glued identifiers may keep the match count constant.
        # Progress means fewer characters outside the generated tokens.
        next_remaining = len(_ANY_TOKEN.sub("", text))
        if next_remaining >= remaining:
            raise ShieldResidualPiiError("Texto no anonimizable de forma segura.")
        remaining = next_remaining
        # Residual: solo puede aparecer junto a los tokens recién insertados.
        matches = find_pii(text, regions=_token_windows(text))
    if matches:
        raise ShieldResidualPiiError("Texto no anonimizable de forma segura.")

    vault.put(request_id, state.token_map)
    rif_verified = all(state.rif_results) if state.rif_results else None
    meta = ShieldMeta(
        blind_citizen_id=blind_citizen_id,
        pii_count=state.occurrences,
        detected_types=tuple(sorted(state.kinds)),
        rif_mod11_verified=rif_verified,
        validation_passed=rif_verified is not False,
        latency_ms=(time.perf_counter() - started) * 1000,
    )
    return text, meta
