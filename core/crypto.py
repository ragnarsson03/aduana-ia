"""Criptografía pura (hashlib, hmac, secrets, unicodedata). Gatillo 0.

Funciones puras. Las operaciones con llave se hacen vía ``KeyRing`` (subllaves por dominio).

Contrato del ledger: ``canonical_block_payload`` serializa en JSON canónico (claves ordenadas,
separadores compactos, ``ensure_ascii=True``) TODOS los campos del bloque excepto ``block_hash``
y ``hmac_signature``. ``block_hash`` = SHA-256 del payload; ``hmac_signature`` = HMAC (dominio
``ledger-sign``) de ``block_hash``. El JSON elimina cualquier ambigüedad por separadores.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Final

from core.context import LedgerBlock, LedgerEntry
from core.keyring import KeyRing
from core.text_normalizer import normalize_text

RIF_LETTER_MAP: Final[dict[str, int]] = {"V": 1, "E": 2, "J": 3, "P": 4, "G": 5, "C": 3}
RIF_WEIGHTS: Final[tuple[int, ...]] = (4, 3, 2, 7, 6, 5, 4, 3, 2)

# ASCII estricto: ``\d`` de str acepta dígitos Unicode (árabe, devanagari) y evadiría el índice.
_CEDULA_RE: Final = re.compile(r"([VE])?([0-9]{5,9})", re.ASCII)
_RIF_RE: Final = re.compile(r"([A-Z])([0-9]{8})([0-9])", re.ASCII)
_RIF_MODULUS: Final[int] = 11


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_cedula(cedula: str) -> str:
    """``V-12.345.678`` / ``V12345678`` / ``12345678`` -> ``V12345678`` (V por defecto).

    Forma canónica: letra V|E + dígitos ASCII sin ceros a la izquierda (5 a 9 dígitos).
    """
    if not isinstance(cedula, str):
        raise ValueError("Cédula con formato inválido.")
    compact = "".join(
        ch for ch in normalize_text(cedula).upper() if ch not in "-." and not ch.isspace()
    )
    match = _CEDULA_RE.fullmatch(compact)
    digits = match.group(2).lstrip("0") if match else ""
    if match is None or not 5 <= len(digits) <= 9:
        raise ValueError("Cédula con formato inválido.")  # sin eco del valor (Zero-Leak)
    return f"{match.group(1) or 'V'}{digits}"


def blind_citizen_id(keys: KeyRing, cedula: str) -> str:
    """HMAC irreversible (dominio ``blind-index``) de la cédula normalizada."""
    return keys.hmac_hex("blind-index", normalize_cedula(cedula).encode())


def consent_hash(request_id: str, timestamp_utc: str, purpose_code: str, blind_id: str) -> str:
    """Vincula consentimiento a request, momento, propósito y ciudadano (RF-02)."""
    return sha256_hex(_canonical_json([request_id, timestamp_utc, purpose_code, blind_id]))


def canary_token(keys: KeyRing, request_id: str) -> str:
    """``[[CANARY-HMAC-XXXXXXXXXXXXXXXX]]`` (16 hex) dinámico por transacción (RF-10)."""
    try:
        encoded = request_id.encode()
    except (AttributeError, UnicodeError):
        raise ValueError("request_id inválido.") from None  # sin eco del valor
    digest = keys.hmac_hex("canary", encoded)[:16].upper()
    return f"[[CANARY-HMAC-{digest}]]"


def rif_mod11_valid(rif: str) -> bool:
    """Módulo 11 SENIAT: S = sum(d_k * W_k), R = 11 - (S mod 11); R >= 10 -> dígito 0."""
    if not isinstance(rif, str):
        return False
    compact = "".join(ch for ch in normalize_text(rif).upper() if ch != "-" and not ch.isspace())
    match = _RIF_RE.fullmatch(compact)
    if match is None or match.group(1) not in RIF_LETTER_MAP:
        return False
    digits = (RIF_LETTER_MAP[match.group(1)], *map(int, match.group(2)))
    total = sum(d * w for d, w in zip(digits, RIF_WEIGHTS, strict=True))
    remainder = _RIF_MODULUS - (total % _RIF_MODULUS)
    expected = 0 if remainder >= 10 else remainder
    return int(match.group(3)) == expected


def canonical_block_payload(
    source: LedgerBlock | LedgerEntry, *, index: int, prev_hash: str, key_id: str
) -> bytes:
    """Payload determinista que cubre TODOS los campos (salvo hash y firma)."""
    return _canonical_json(
        {
            "block_index": index,
            "request_id": source.request_id,
            "timestamp_utc": source.timestamp_utc,
            "blind_citizen_id": source.blind_citizen_id,
            "payload_hash": source.payload_hash,
            "prev_hash": prev_hash,
            "security_verdict": source.security_verdict,
            "model_recommendation": source.model_recommendation,
            "human_decision": source.human_decision,
            "human_override": source.human_override,
            "citizen_receipt_code": source.citizen_receipt_code,
            "override_justification_hash": source.override_justification_hash,
            "key_id": key_id,
        }
    )


def block_hash(payload: bytes) -> str:
    return sha256_hex(payload)


def block_signature(keys: KeyRing, block_hash_hex: str) -> str:
    return keys.hmac_hex("ledger-sign", block_hash_hex.encode())
