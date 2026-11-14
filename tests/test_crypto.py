"""Gatillo 0 — core/crypto.py. Vectores Módulo 11 calculados a mano (ver comentarios)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from core import crypto
from core.context import LedgerEntry
from core.keyring import KeyRing

KEYS = KeyRing(bytes(range(32)))
OTHER = KeyRing(bytes(range(1, 33)))


def test_sha256_hex_matches_stdlib() -> None:
    assert crypto.sha256_hex(b"abc") == hashlib.sha256(b"abc").hexdigest()


# --- cédula / índice ciego -------------------------------------------------------------
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("V-12.345.678", "V12345678"),
        ("v12345678", "V12345678"),
        ("12345678", "V12345678"),
        ("E-81234567", "E81234567"),
        (" V - １２３４５６７８ ", "V12345678"),  # fullwidth + espacios (NFKC)
        ("V-12​345678", "V12345678"),  # zero-width
    ],
)
def test_normalize_cedula_is_stable(raw: str, expected: str) -> None:
    assert crypto.normalize_cedula(raw) == expected


@pytest.mark.parametrize("bad", ["", "V-", "abc", "V-12"])
def test_normalize_cedula_rejects_garbage(bad: str) -> None:
    with pytest.raises(ValueError):
        crypto.normalize_cedula(bad)


def test_blind_citizen_id_is_deterministic_keyed_and_format_independent() -> None:
    a = crypto.blind_citizen_id(KEYS, "V-12.345.678")
    assert a == crypto.blind_citizen_id(KEYS, "12345678")
    assert a != crypto.blind_citizen_id(OTHER, "12345678")
    assert a != crypto.blind_citizen_id(KEYS, "12345679")
    assert len(a) == 64
    assert "12345678" not in a


# --- consentimiento / canary ------------------------------------------------------------
def test_consent_hash_binds_all_fields() -> None:
    base = crypto.consent_hash("r1", "2026-11-13T10:00:00Z", "BECA", "b1")
    assert len(base) == 64
    assert base == crypto.consent_hash("r1", "2026-11-13T10:00:00Z", "BECA", "b1")
    for args in (
        ("r2", "2026-11-13T10:00:00Z", "BECA", "b1"),
        ("r1", "2026-11-13T10:00:01Z", "BECA", "b1"),
        ("r1", "2026-11-13T10:00:00Z", "SALUD", "b1"),
        ("r1", "2026-11-13T10:00:00Z", "BECA", "b2"),
    ):
        assert crypto.consent_hash(*args) != base


def test_consent_hash_has_no_separator_ambiguity() -> None:
    assert crypto.consent_hash("a|b", "c", "d", "e") != crypto.consent_hash("a", "b|c", "d", "e")


def test_canary_token_format_and_uniqueness() -> None:
    token = crypto.canary_token(KEYS, "req-1")
    assert token.startswith("[[CANARY-HMAC-") and token.endswith("]]")
    digest = token.removeprefix("[[CANARY-HMAC-").removesuffix("]]")
    assert len(digest) == 16 and digest == digest.upper()
    assert token == crypto.canary_token(KEYS, "req-1")
    assert token != crypto.canary_token(KEYS, "req-2")
    assert token != crypto.canary_token(OTHER, "req-1")


# --- RIF Módulo 11 SENIAT ----------------------------------------------------------------
# d = [letra, 8 dígitos]; pesos (4,3,2,7,6,5,4,3,2); R = 11 - (S mod 11); R >= 10 -> 0.
@pytest.mark.parametrize(
    "rif",
    [
        "J-12345678-4",  # S=150, 150%11=7, R=4
        "V-00000001-5",  # S=6,   6%11=6,   R=5
        "G-00000000-2",  # S=20,  20%11=9,  R=2
        "V-00000009-0",  # S=22,  22%11=0,  R=11 -> 0
        "V-00000004-0",  # S=12,  12%11=1,  R=10 -> 0
        "J123456784",  # sin guiones
    ],
)
def test_rif_mod11_valid(rif: str) -> None:
    assert crypto.rif_mod11_valid(rif) is True


@pytest.mark.parametrize(
    "rif",
    [
        "J-12345678-5",  # dígito verificador erróneo
        "V-00000009-1",
        "X-12345678-4",  # letra fuera del mapa
        "J-1234567-4",  # longitud errónea
        "J-12345678",  # sin dígito verificador
        "",
        "J-1234567A-4",
    ],
)
def test_rif_mod11_invalid(rif: str) -> None:
    assert crypto.rif_mod11_valid(rif) is False


# RIF públicos publicados por organismos/empresas (verificados por Codex; no prueban estado fiscal).
@pytest.mark.parametrize(
    "rif",
    [
        "J-00002961-0",  # Mercantil Banco: S=78, R=10 -> 0 (descarta la variante 10 -> 9)
        "G-20000110-0",  # BCV: S=33, R=11 -> 0
        "J-07013380-5",  # Banesco: S=83, R=5, con cero inicial
        "G-20000194-1",  # Alcaldía de Chacao: S=65, R=1
        "E-00000001-1",  # sintético E: S=10, R=1
        "P-00000001-4",  # sintético P: S=18, R=4
        "C-00000001-8",  # sintético C (valor 3 por contrato del proyecto): S=14, R=8
    ],
)
def test_rif_mod11_public_and_synthetic_vectors(rif: str) -> None:
    assert crypto.rif_mod11_valid(rif) is True


@pytest.mark.parametrize(
    "rif",
    [
        "J-00002961-9",  # regresión: con R=10 -> 9 este sería válido
        "J-7013380-5",  # forma abreviada sin relleno de ceros: se rechaza (10 caracteres exactos)
        "G-200000303-0",  # longitud incorrecta
    ],
)
def test_rif_mod11_known_invalid_vectors(rif: str) -> None:
    assert crypto.rif_mod11_valid(rif) is False


def test_rif_letter_map_and_weights_are_the_official_ones() -> None:
    assert crypto.RIF_WEIGHTS == (4, 3, 2, 7, 6, 5, 4, 3, 2)
    assert crypto.RIF_LETTER_MAP == {"V": 1, "E": 2, "J": 3, "P": 4, "G": 5, "C": 3}


# --- ledger: payload canónico, hash y firma ---------------------------------------------
ENTRY = LedgerEntry(
    request_id="r1",
    timestamp_utc="2026-11-13T10:00:00Z",
    blind_citizen_id="b" * 64,
    payload_hash="p" * 64,
    security_verdict="CLEAN",
    model_recommendation="REVISION_ESTANDAR",
    human_decision="REVISION_ESTANDAR",
    human_override=False,
    citizen_receipt_code="RC-1",
    override_justification_hash=None,
)


def _payload(
    entry: LedgerEntry = ENTRY, index: int = 1, prev: str = "0" * 64, key_id: str = "k"
) -> bytes:
    return crypto.canonical_block_payload(entry, index=index, prev_hash=prev, key_id=key_id)


def test_canonical_payload_is_compact_sorted_ascii_json_covering_all_fields() -> None:
    payload = _payload()
    data = json.loads(payload)
    assert list(data) == sorted(data)
    assert b" " not in payload
    assert set(data) == {
        "block_index",
        "request_id",
        "timestamp_utc",
        "blind_citizen_id",
        "payload_hash",
        "prev_hash",
        "security_verdict",
        "model_recommendation",
        "human_decision",
        "human_override",
        "citizen_receipt_code",
        "override_justification_hash",
        "key_id",
    }


@pytest.mark.parametrize(
    "change",
    [
        {"request_id": "r2"},
        {"timestamp_utc": "2026-11-13T10:00:01Z"},
        {"blind_citizen_id": "c" * 64},
        {"payload_hash": "q" * 64},
        {"security_verdict": "BLOCKED_INJECTION"},
        {"model_recommendation": "PRIORIDAD_ALTA"},
        {"human_decision": "PRIORIDAD_ALTA"},
        {"human_override": True},
        {"citizen_receipt_code": "RC-2"},
        {"override_justification_hash": "h" * 64},
    ],
)
def test_every_entry_field_changes_the_block_hash(change: dict) -> None:
    base = crypto.block_hash(_payload())
    assert crypto.block_hash(_payload(replace(ENTRY, **change))) != base


def test_index_prev_hash_and_key_id_change_the_block_hash() -> None:
    base = crypto.block_hash(_payload())
    assert crypto.block_hash(_payload(index=2)) != base
    assert crypto.block_hash(_payload(prev="1" * 64)) != base
    assert crypto.block_hash(_payload(key_id="k2")) != base


def test_block_signature_is_keyed_and_verifiable() -> None:
    h = crypto.block_hash(_payload())
    sig = crypto.block_signature(KEYS, h)
    assert sig == crypto.block_signature(KEYS, h)
    assert sig != crypto.block_signature(OTHER, h)
    assert KEYS.verify("ledger-sign", h.encode(), sig)
    assert sig != h  # un atacante que recalcula SHA-256 sin la clave no obtiene la firma


# --- hallazgos de revisión: evasión Unicode y robustez --------------------------------------
@pytest.mark.parametrize(
    "evaded",
    ["V١٢٣٤٥٦٧٨", "V१२३४५६७८", "V1­2345678", "V1‮2345678"],  # arabigo, devanagari, soft hyphen, bidi
)
def test_cedula_non_ascii_digits_or_invisibles_cannot_split_the_blind_index(evaded: str) -> None:
    try:
        normalized = crypto.normalize_cedula(evaded)
    except ValueError:
        return  # rechazada: tampoco genera un índice distinto
    assert normalized == "V12345678"


def test_cedula_canonical_form_ignores_leading_zeros_and_surrounding_whitespace() -> None:
    assert crypto.normalize_cedula("V012345678") == "V12345678"
    assert crypto.normalize_cedula("12345678\n") == "V12345678"


@pytest.mark.parametrize(
    ("rif", "expected"),
    [
        ("J-١٢٣٤٥٦٧٨-4", True),  # dígitos árabes: se canonizan a ASCII
        ("J-12345678-４", True),  # fullwidth: NFKC lo lleva a ASCII
        ("J-12345678-4​", True),  # zero-width: se elimina
    ],
)
def test_rif_validation_uses_same_normalization_as_cedula(rif: str, expected: bool) -> None:
    assert crypto.rif_mod11_valid(rif) is expected


def test_rif_trailing_newline_and_non_str_input() -> None:
    assert crypto.rif_mod11_valid("J-12345678-4\n") is True
    assert crypto.rif_mod11_valid(None) is False  # type: ignore[arg-type]


def test_canary_rejects_unencodable_request_id_without_echo() -> None:
    with pytest.raises(ValueError) as info:
        crypto.canary_token(KEYS, "id-\ud800")
    assert "\ud800" not in str(info.value)
