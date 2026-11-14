from __future__ import annotations

import copy
import pickle

import pytest

from core.config import Settings, load_keys_from_env
from core.keyring import KeyRing
from core.text_normalizer import normalize_text

MASTER = bytes(range(32))


def test_domains_are_separated() -> None:
    keys = KeyRing(MASTER)
    assert keys.hmac_hex("ledger-sign", b"x") != keys.hmac_hex("canary", b"x")


def test_verify_accepts_valid_and_rejects_forged_and_non_ascii() -> None:
    keys = KeyRing(MASTER)
    sig = keys.hmac_hex("ledger-sign", b"x")
    assert keys.verify("ledger-sign", b"x", sig)
    assert not keys.verify("ledger-sign", b"x", "0" * 64)
    assert not keys.verify("ledger-sign", b"x", "ñ" * 64)  # no lanza TypeError


def test_keyring_hides_and_refuses_serialization() -> None:
    keys = KeyRing(MASTER)
    assert MASTER.hex() not in repr(keys) + str(keys)
    for operation in (pickle.dumps, copy.copy, copy.deepcopy):
        with pytest.raises(TypeError):
            operation(keys)


@pytest.mark.parametrize("bad", [b"short", b"\x00" * 32])
def test_rejects_short_or_degenerate_keys(bad: bytes) -> None:
    with pytest.raises(ValueError):
        KeyRing(bad)


def test_keyring_is_unusable_after_wipe() -> None:
    keys = KeyRing(MASTER)
    keys.wipe()
    for operation in (
        lambda: keys.hmac_hex("canary", b"x"),
        lambda: keys.verify("canary", b"x", "0" * 64),
        lambda: keys.key_id,
    ):
        with pytest.raises(RuntimeError):
            operation()


def test_verify_returns_false_for_non_str_and_unknown_domain_raises() -> None:
    keys = KeyRing(MASTER)
    assert keys.verify("canary", b"x", None) is False  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        keys.hmac_hex("unknown", b"x")


def test_rejects_31_byte_key() -> None:
    with pytest.raises(ValueError):
        KeyRing(bytes(range(31)))


def test_key_id_differs_between_keys_and_hides_key() -> None:
    assert KeyRing(MASTER).key_id != KeyRing(bytes(range(1, 33))).key_id
    assert len(KeyRing(MASTER).key_id) == 16


def test_load_keys_pops_secret_from_environment() -> None:
    env = {"ADUANA_MASTER_KEY": MASTER.hex()}
    keys = load_keys_from_env(env)
    assert "ADUANA_MASTER_KEY" not in env
    assert keys.key_id == KeyRing(MASTER).key_id


def test_settings_ledger_ephemeral_depends_on_master_key() -> None:
    assert Settings.from_env({}).ledger_ephemeral is True
    assert Settings.from_env({"ADUANA_MASTER_KEY": MASTER.hex()}).ledger_ephemeral is False


def test_settings_rejects_remote_host_without_opt_in() -> None:
    with pytest.raises(ValueError):
        Settings.from_env({"ADUANA_HOST": "0.0.0.0"})  # noqa: S104
    assert Settings.from_env({"ADUANA_HOST": "0.0.0.0", "ADUANA_ALLOW_REMOTE": "1"})  # noqa: S104


@pytest.mark.parametrize(
    "invisible",
    ["­", "‎", "‏", "‪", "‮", "⁦", "⁩", "᠎", "؜", "͏", "⁡", "️", "ㅤ", "ᅟ",
     "\U000e0041"],
)
def test_normalize_text_strips_all_invisible_format_characters(invisible: str) -> None:
    assert normalize_text(f"V1{invisible}2345678") == "V12345678"


def test_normalize_text_keeps_whitespace_and_accents_and_is_idempotent() -> None:
    text = "Solicitud de beca\n\tniño áéí"
    assert normalize_text(text) == text
    messy = "V１­２​３"
    assert normalize_text(normalize_text(messy)) == normalize_text(messy)


def test_normalize_text_defeats_unicode_evasion() -> None:
    evaded = "V-１２​３４５６７８"  # dígitos fullwidth + zero-width
    assert normalize_text(evaded) == "V-12345678"
    assert normalize_text(normalize_text(evaded)) == normalize_text(evaded)
