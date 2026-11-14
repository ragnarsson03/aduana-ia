"""CA-01 — SHIELD. Datos sintéticos; RIF con verificador calculado (J-12345678-4, V-00000001-5)."""

from __future__ import annotations

import time

import pytest

from core.ephemeral_vault import EphemeralVault
from pipeline.stage1_shield import shield

TEXT = (
    "Solicitante V-00000001 y E-00000002, empresa J-12345678-4. "
    "Tel 0412-0000001 / 0212-0000002. Cuenta 00000000000000000001. "
    "Correo fixture@example.invalid. Paciente con diabetes."
)
ORIGINALS = [
    "V-00000001", "E-00000002", "J-12345678-4", "0412-0000001", "0212-0000002",
    "00000000000000000001", "fixture@example.invalid", "diabetes",
]


@pytest.fixture
def vault() -> EphemeralVault:
    return EphemeralVault()


def run(vault: EphemeralVault, text: str = TEXT, rid: str = "r1"):
    return shield(rid, text, vault=vault, blind_citizen_id="b" * 64)


def test_masks_every_structured_identifier(vault: EphemeralVault) -> None:
    masked, meta = run(vault)
    for original in ORIGINALS:
        assert original not in masked
    for token in ("[CEDULA_1]", "[CEDULA_2]", "[RIF_1]", "[PHONE_1]", "[PHONE_2]", "[BANK_1]",
                  "[EMAIL_1]", "[CLINICAL_1]"):
        assert token in masked
    assert set(meta.detected_types) == {"CEDULA", "RIF", "PHONE", "BANK", "EMAIL", "CLINICAL"}
    assert meta.detected_types == tuple(sorted(meta.detected_types))


def test_reversal_map_lives_only_in_vault(vault: EphemeralVault) -> None:
    masked, meta = run(vault)
    mapping = vault.get_map("r1")
    assert mapping["[CEDULA_1]"] == "V-00000001"
    assert mapping["[RIF_1]"] == "J-12345678-4"
    assert all(o not in repr(meta) for o in ORIGINALS)
    assert meta.blind_citizen_id == "b" * 64


def test_repeated_identifier_reuses_token_and_counts_occurrences(vault: EphemeralVault) -> None:
    masked, meta = run(vault, "V-00000001 y de nuevo v00000001 y V-00.000.001")
    assert masked.count("[CEDULA_1]") == 3
    assert "[CEDULA_2]" not in masked
    assert meta.pii_count == 3
    assert len(vault.get_map("r1")) == 1


def test_rif_mod11_aggregation(vault: EphemeralVault) -> None:
    _, none_meta = run(vault, "sin rif V-00000001", "a")
    _, ok_meta = run(vault, "J-12345678-4 y V-00000001-5", "b")
    _, bad_meta = run(vault, "J-12345678-4 y J-12345678-5", "c")
    assert none_meta.rif_mod11_verified is None and none_meta.validation_passed is True
    assert ok_meta.rif_mod11_verified is True and ok_meta.validation_passed is True
    assert bad_meta.rif_mod11_verified is False and bad_meta.validation_passed is False


def test_invalid_rif_is_still_masked(vault: EphemeralVault) -> None:
    masked, _ = run(vault, "J-12345678-5")
    assert "12345678" not in masked and "[RIF_1]" in masked


def test_unicode_evasion_is_masked(vault: EphemeralVault) -> None:
    masked, _ = run(vault, "V-１２３­４５６７８ y V​-00000001")
    assert "12345678" not in masked and "00000001" not in masked


def test_clean_text_passes_through_and_vault_session_exists(vault: EphemeralVault) -> None:
    masked, meta = run(vault, "Solicito una beca")
    assert masked == "Solicito una beca"
    assert meta.pii_count == 0 and meta.detected_types == ()
    assert dict(vault.get_map("r1")) == {}


def test_latency_under_20ms_every_run(vault: EphemeralVault) -> None:
    run(vault, rid="warm")  # calentamiento
    worst = 0.0
    for i in range(200):
        start = time.perf_counter()
        _, meta = run(vault, rid=f"r{i}")
        worst = max(worst, (time.perf_counter() - start) * 1000)
        assert meta.latency_ms < 20
        vault.zeroize(f"r{i}")
    assert worst < 20, f"peor caso {worst:.2f} ms"


def test_adjacent_identifiers_are_fully_masked_by_fixed_point(vault: EphemeralVault) -> None:
    masked, meta = run(vault, "V-00000001V-00000002")
    assert "0000000" not in masked
    assert meta.pii_count == 2 and len(vault.get_map("r1")) == 2


def test_residual_pii_fails_closed_and_keeps_vault_clean(
    vault: EphemeralVault, monkeypatch: pytest.MonkeyPatch
) -> None:
    from core.errors import ShieldResidualPiiError
    from core.pii_patterns import PiiMatch
    from pipeline import stage1_shield

    monkeypatch.setattr(
        stage1_shield, "find_pii", lambda text, **kwargs: (PiiMatch("CEDULA", 0, 1),)
    )
    with pytest.raises(ShieldResidualPiiError) as info:
        run(vault, "x" * 10)
    assert "xxx" not in str(info.value)
    assert vault.active_sessions == 0


def test_preexisting_token_literals_do_not_collide(vault: EphemeralVault) -> None:
    masked, _ = run(vault, "[CEDULA_1] y V-00000001")
    assert masked.count("[CEDULA_1]") == 1  # solo el generado
    assert vault.get_map("r1")["[CEDULA_1]"] == "V-00000001"


@pytest.mark.parametrize("size", [2_000, 5_000, 10_000])  # alcance acordado de CA-01: <= 10 000
def test_latency_scales_within_ca01_scope(vault: EphemeralVault, size: int) -> None:
    filler = "Solicito la revisión de mi expediente de beca universitaria. "
    text = (filler * (size // len(filler) + 1))[:size] + " V-00000001 0412-0000001"
    run(vault, text, "warm")
    worst = 0.0
    for i in range(20):
        start = time.perf_counter()
        run(vault, text, f"s{i}")
        worst = max(worst, (time.perf_counter() - start) * 1000)
    assert worst < 20, f"{size} chars: {worst:.1f} ms"


def test_every_rif_letter_is_masked_even_when_check_digit_is_wrong(vault: EphemeralVault) -> None:
    for letter in "VEJPGC":
        masked, meta = run(vault, f"{letter}-00000001-9 fin", f"l{letter}")
        assert "00000001" not in masked and meta.detected_types == ("RIF",)


def test_meta_and_masked_text_hold_no_original_values(vault: EphemeralVault) -> None:
    masked, meta = run(vault)
    blob = masked + repr(meta)
    assert not any(o.lower() in blob.lower() for o in ORIGINALS)
