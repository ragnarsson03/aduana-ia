"""Núcleo criptográfico de identidad (specs/06 §5, §7): contraseñas, índice ciego y token."""

from __future__ import annotations

import base64
import json

import pytest

from core import auth
from core.auth import (
    PBKDF2_ITERATIONS,
    PasswordRecord,
    TokenClaims,
    blind_identifier,
    derive_key,
    hash_password,
    issue_token,
    normalize_identifier,
    validate_password_policy,
    verify_password,
    verify_token,
)
from core.context import UsuarioAduana
from core.crypto import blind_citizen_id, rif_mod11_valid
from core.errors import InvalidTokenError, WeakPasswordError
from core.keyring import KeyRing

ITER = 1000
GOOD_PW = "Clave-De-Prueba-42"  # noqa: S105 - valor de test


def _rif_with_check(letter: str, body: str) -> str:
    """RIF sintético con dígito verificador válido (busca el único dígito que valida)."""
    for check in range(10):
        candidate = f"{letter}{body}{check}"
        if rif_mod11_valid(candidate):
            return candidate
    raise AssertionError("sin verificador")


def _user(rol: str = "AGENTE_ADUANAL_CERTIFICADO") -> UsuarioAduana:
    return UsuarioAduana(
        user_id="u" * 32,
        codigo_usuario="agente.01",
        blind_identifier="b" * 64,
        rol=rol,  # type: ignore[arg-type]
        estado="ACTIVO",
        created_utc="2026-01-01T00:00:00Z",
    )


# --- contraseñas ------------------------------------------------------------------------------


def test_default_iterations_constant() -> None:
    assert PBKDF2_ITERATIONS == 600_000


def test_hash_password_unique_salt_of_32_bytes() -> None:
    a = hash_password(GOOD_PW, iterations=ITER)
    b = hash_password(GOOD_PW, iterations=ITER)
    assert len(a.salt) == 32 and len(a.hash) == 32
    assert a.salt != b.salt and a.hash != b.hash
    assert a.iterations == ITER


def test_verify_password_ok_and_wrong() -> None:
    rec = hash_password(GOOD_PW, iterations=ITER)
    assert verify_password(GOOD_PW, rec) is True
    assert verify_password(GOOD_PW + "x", rec) is False
    assert verify_password("", rec) is False


def test_derive_key_is_deterministic_and_salted() -> None:
    salt = bytes(range(32))
    assert derive_key(GOOD_PW, salt, ITER) == derive_key(GOOD_PW, salt, ITER)
    assert derive_key(GOOD_PW, salt, ITER) != derive_key(GOOD_PW, bytes(32), ITER)
    assert len(derive_key(GOOD_PW, salt, ITER)) == 32


def test_password_record_repr_hides_hash() -> None:
    rec = hash_password(GOOD_PW, iterations=ITER)
    assert rec.hash.hex() not in repr(rec)
    assert rec.hash.hex() not in str(rec)
    assert "hash=" not in repr(rec)


def test_password_record_is_immutable() -> None:
    rec = hash_password(GOOD_PW, iterations=ITER)
    with pytest.raises(AttributeError):
        rec.iterations = 1  # type: ignore[misc]


def test_hash_password_rejects_invalid_iterations() -> None:
    with pytest.raises(ValueError):
        hash_password(GOOD_PW, iterations=0)


@pytest.mark.slow
def test_default_iterations_full_derivation_works() -> None:
    rec = hash_password(GOOD_PW)
    assert rec.iterations == 600_000
    assert verify_password(GOOD_PW, rec)


@pytest.mark.parametrize(
    "password",
    ["corta1A", "sinnumerosaquiabc", "123456789012", "aaaaaaaaaaaa", "1111111111111", ""],
)
def test_weak_passwords_rejected_without_echo(password: str) -> None:
    with pytest.raises(WeakPasswordError) as exc:
        validate_password_policy(password)
    if password:
        assert password not in str(exc.value)


def test_non_string_password_is_weak() -> None:
    with pytest.raises(WeakPasswordError):
        validate_password_policy(None)  # type: ignore[arg-type]


def test_strong_password_accepted() -> None:
    validate_password_policy(GOOD_PW)
    validate_password_policy("abcdefghijk1")  # justo el mínimo


# --- identificadores --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    ["V-12.345.678", "V12345678", "12345678", " v 12 345 678 ", "V-12345678", "٢"],
)
def test_cedula_formats_normalize_equal(raw: str) -> None:
    if raw == "٢":
        with pytest.raises(ValueError):
            normalize_identifier(raw)
        return
    assert normalize_identifier(raw) == "V12345678"


def test_cedula_extranjero_and_unicode_digits() -> None:
    assert normalize_identifier("E-81.234.567") == "E81234567"
    assert normalize_identifier("V-١٢٣٤٥٦٧٨") == "V12345678"  # dígitos árabe-índicos


def test_cedula_blind_index_matches_ledger(keys: KeyRing) -> None:
    for raw in ("V-12.345.678", "12345678", "E81234567"):
        assert blind_identifier(keys, raw) == blind_citizen_id(keys, raw)


def test_rif_canonical_and_blind_index(keys: KeyRing) -> None:
    rif = _rif_with_check("J", "30123456")
    dashed = f"{rif[0]}-{rif[1:9]}-{rif[9]}"
    assert normalize_identifier(dashed) == rif
    assert normalize_identifier(rif.lower()) == rif
    expected = keys.hmac_hex("blind-index", b"RIF:" + rif.encode())
    assert blind_identifier(keys, dashed) == expected


@pytest.mark.parametrize("letter", ["J", "P", "G", "C"])
def test_rif_letters_jpgc_always_rif(letter: str) -> None:
    body = "12345678"
    rif = f"{letter}{body}0"  # verificador arbitrario: la letra basta para decidir RIF
    assert normalize_identifier(rif) == rif


def test_v_with_nine_digits_disambiguation(keys: KeyRing) -> None:
    valid_rif = _rif_with_check("V", "12345678")
    assert normalize_identifier(valid_rif) == valid_rif  # RIF (mod 11 ok)
    assert blind_identifier(keys, valid_rif) != blind_citizen_id(keys, valid_rif)
    # Sin verificador válido: es cédula de 9 dígitos
    bad = next("V12345678" + str(d) for d in range(10) if not rif_mod11_valid(f"V12345678{d}"))
    assert normalize_identifier(bad) == bad
    assert blind_identifier(keys, bad) == blind_citizen_id(keys, bad)


def test_rif_and_cedula_never_collide(keys: KeyRing) -> None:
    rif = _rif_with_check("V", "12345678")
    digits = rif[1:]
    assert blind_identifier(keys, rif) != blind_identifier(keys, "E" + digits)


@pytest.mark.parametrize(
    "raw", ["", "abc", "V-1234", "X12345678", "J1234567", "V12345678901", "12-34", "V\x00123"]
)
def test_invalid_identifier_rejected_without_echo(raw: str) -> None:
    with pytest.raises(ValueError) as exc:
        normalize_identifier(raw)
    if raw:
        assert raw not in str(exc.value)


def test_non_string_identifier_rejected() -> None:
    with pytest.raises(ValueError):
        normalize_identifier(12345678)  # type: ignore[arg-type]


def test_blind_index_differs_across_keys() -> None:
    k1, k2 = KeyRing(bytes(range(32))), KeyRing(bytes(range(1, 33)))
    assert blind_identifier(k1, "V12345678") != blind_identifier(k2, "V12345678")


# --- token ------------------------------------------------------------------------------------


def _split(token: str) -> tuple[str, str, str]:
    version, payload, sig = token.split(".")
    return version, payload, sig


def _forge(keys: KeyRing, claims: dict[str, object]) -> str:
    payload = (
        base64.urlsafe_b64encode(json.dumps(claims, separators=(",", ":")).encode())
        .rstrip(b"=")
        .decode()
    )
    return f"v1.{payload}.{keys.hmac_hex('auth-token', payload.encode())}"


def test_issue_and_verify_roundtrip(keys: KeyRing) -> None:
    user = _user()
    tok = issue_token(keys, user, now=1000, ttl_seconds=60)
    assert tok.issued_at == 1000 and tok.expires_at == 1060
    assert tok.user_id == user.user_id and tok.codigo_usuario == user.codigo_usuario
    assert tok.rol == user.rol and len(tok.token_id) == 32
    claims = verify_token(keys, tok.token, now=1059)
    assert claims == TokenClaims(
        user_id=user.user_id, rol=user.rol, issued_at=1000, expires_at=1060, token_id=tok.token_id
    )


def test_token_format_and_compact_json(keys: KeyRing) -> None:
    tok = issue_token(keys, _user(), now=5, ttl_seconds=10)
    version, payload, sig = _split(tok.token)
    assert version == "v1" and len(sig) == 64
    raw = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)).decode()
    assert " " not in raw
    assert set(json.loads(raw)) == {"sub", "rol", "iat", "exp", "jti"}
    assert "=" not in payload


def test_tokens_have_unique_jti(keys: KeyRing) -> None:
    a = issue_token(keys, _user(), now=1, ttl_seconds=10)
    b = issue_token(keys, _user(), now=1, ttl_seconds=10)
    assert a.token_id != b.token_id and a.token != b.token


def test_token_expiry_boundary(keys: KeyRing) -> None:
    tok = issue_token(keys, _user(), now=1000, ttl_seconds=60)
    verify_token(keys, tok.token, now=1059)
    with pytest.raises(InvalidTokenError):
        verify_token(keys, tok.token, now=1060)  # exp <= now
    with pytest.raises(InvalidTokenError):
        verify_token(keys, tok.token, now=9999)


def test_issue_token_rejects_non_positive_ttl(keys: KeyRing) -> None:
    with pytest.raises(ValueError):
        issue_token(keys, _user(), now=1, ttl_seconds=0)


def test_tampered_payload_rejected(keys: KeyRing) -> None:
    tok = issue_token(keys, _user("AGENTE_ADUANAL_CERTIFICADO"), now=1000, ttl_seconds=60)
    version, payload, sig = _split(tok.token)
    data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    data["rol"] = "INSPECTOR_TRIBUTARIO_SENIAT"
    forged = (
        base64.urlsafe_b64encode(json.dumps(data, separators=(",", ":")).encode())
        .rstrip(b"=")
        .decode()
    )
    with pytest.raises(InvalidTokenError):
        verify_token(keys, f"{version}.{forged}.{sig}", now=1001)


def test_tampered_signature_and_other_key_rejected(keys: KeyRing) -> None:
    tok = issue_token(keys, _user(), now=1000, ttl_seconds=60)
    version, payload, sig = _split(tok.token)
    flipped = ("0" if sig[0] != "0" else "1") + sig[1:]
    with pytest.raises(InvalidTokenError):
        verify_token(keys, f"{version}.{payload}.{flipped}", now=1001)
    with pytest.raises(InvalidTokenError):
        verify_token(KeyRing(bytes(range(1, 33))), tok.token, now=1001)


@pytest.mark.parametrize(
    "token",
    ["", "v1", "v1.a", "v1.a.b.c", "v2.a.b", "garbage", "v1..", "..", "v1.%%%.zz", "é.é.é"],
)
def test_malformed_tokens_rejected_uniformly(keys: KeyRing, token: str) -> None:
    with pytest.raises(InvalidTokenError) as exc:
        verify_token(keys, token, now=1)
    assert token not in str(exc.value) or token == ""


def test_non_string_token_rejected(keys: KeyRing) -> None:
    with pytest.raises(InvalidTokenError):
        verify_token(keys, None, now=1)  # type: ignore[arg-type]


def test_wrong_version_with_valid_signature_rejected(keys: KeyRing) -> None:
    good = _forge(
        keys, {"sub": "u", "rol": "AGENTE_ADUANAL_CERTIFICADO", "iat": 1, "exp": 99, "jti": "j"}
    )
    _, payload, sig = _split(good)
    with pytest.raises(InvalidTokenError):
        verify_token(keys, f"v2.{payload}.{sig}", now=2)


def test_unknown_role_in_signed_payload_rejected(keys: KeyRing) -> None:
    tok = _forge(keys, {"sub": "u", "rol": "ROOT", "iat": 1, "exp": 99, "jti": "j"})
    with pytest.raises(InvalidTokenError):
        verify_token(keys, tok, now=2)


@pytest.mark.parametrize(
    "claims",
    [
        {"sub": "u", "rol": "AGENTE_ADUANAL_CERTIFICADO", "iat": 1, "exp": "99", "jti": "j"},
        {"sub": "u", "rol": "AGENTE_ADUANAL_CERTIFICADO", "iat": True, "exp": 99, "jti": "j"},
        {"sub": 5, "rol": "AGENTE_ADUANAL_CERTIFICADO", "iat": 1, "exp": 99, "jti": "j"},
        {"sub": "u", "rol": "AGENTE_ADUANAL_CERTIFICADO", "iat": 1, "exp": 99},
        {"sub": "u", "rol": "AGENTE_ADUANAL_CERTIFICADO", "iat": 1, "exp": 99, "jti": ""},
    ],
)
def test_signed_but_invalid_claims_rejected(keys: KeyRing, claims: dict[str, object]) -> None:
    with pytest.raises(InvalidTokenError):
        verify_token(keys, _forge(keys, claims), now=2)


def test_signed_non_json_and_non_object_payload_rejected(keys: KeyRing) -> None:
    for body in (b"not json", b"[1,2,3]", b"\xff\xfe"):
        payload = base64.urlsafe_b64encode(body).rstrip(b"=").decode()
        tok = f"v1.{payload}.{keys.hmac_hex('auth-token', payload.encode())}"
        with pytest.raises(InvalidTokenError):
            verify_token(keys, tok, now=1)


def test_error_message_is_uniform(keys: KeyRing) -> None:
    messages = set()
    for tok in ("garbage", "v1.a.b", "v2.a.b"):
        with pytest.raises(InvalidTokenError) as exc:
            verify_token(keys, tok, now=1)
        messages.add(str(exc.value))
    expired = issue_token(keys, _user(), now=1, ttl_seconds=1)
    with pytest.raises(InvalidTokenError) as exc2:
        verify_token(keys, expired.token, now=100)
    messages.add(str(exc2.value))
    assert len(messages) == 1


def test_auth_token_and_user_repr_do_not_leak(keys: KeyRing) -> None:
    tok = issue_token(keys, _user(), now=1, ttl_seconds=10)
    assert tok.token not in repr(tok) and tok.token not in str(tok)
    assert _split(tok.token)[2] not in repr(tok)


def test_module_uses_only_stdlib_crypto() -> None:
    src = open(auth.__file__, encoding="utf-8").read()  # noqa: SIM115
    for banned in (
        "import bcrypt",
        "import jwt",
        "import argon2",
        "import passlib",
        "cryptography",
    ):
        assert banned not in src


def test_password_record_fields() -> None:
    rec = PasswordRecord(salt=b"s" * 32, hash=b"h" * 32, iterations=5)
    assert rec.iterations == 5
