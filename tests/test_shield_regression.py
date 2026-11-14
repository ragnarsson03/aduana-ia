"""Regresión del red team de SHIELD (rondas 1-2). Datos 100% sintéticos.

``MUST_MASK``: la cadena ``needle`` no puede aparecer en la salida enmascarada.
``REDOS``: entradas patológicas; deben resolverse en < 1 s (con 20 000 caracteres).
``KNOWN_LIMITS``: límites conocidos de baja prioridad; ``xfail`` no estricto.
"""

from __future__ import annotations

import time

import pytest

from core.ephemeral_vault import EphemeralVault
from core.errors import ShieldResidualPiiError
from pipeline.stage1_shield import shield

ACCOUNT_TAIL = "0123456789"

MUST_MASK: list[tuple[str, str, str]] = [
    # --- cuenta bancaria pegada a otro número (A-2) y cuentas de 21-24 dígitos
    ("bank-adj-1", "+58 414 7654321 0102-0123-45-0123456789", ACCOUNT_TAIL),
    ("bank-adj-2", "1234567890 0102-0123-45-0123456789", ACCOUNT_TAIL),
    ("bank-adj-3", "cédula 1234567890 0102-0123-45-0123456789", ACCOUNT_TAIL),
    ("bank-adj-4", "584147654321\n0102-0123-45-0123456789", ACCOUNT_TAIL),
    ("bank-adj-5", "123456789012 0102 0123 450123456789", "450123456789"),
    ("bank-adj-6", "V-12345678 0102012345012345678", "2345678"),
    ("bank-21", "010201234501234567890", ACCOUNT_TAIL),
    ("bank-24", "010201234501234567890123", ACCOUNT_TAIL),
    # --- contexto de cédula/RIF lejos de la palabra clave (M-1) y con palabras intermedias (M-5)
    ("ctx-gap-1", "cédula" + " " * 43 + "12345678", "12345678"),
    ("ctx-gap-2", "cédula" + "\n" * 43 + "12345678", "12345678"),
    ("ctx-gap-3", "cédula de identidad" + " " * 30 + "12345678", "12345678"),
    ("ctx-gap-4", "documento de identidad" + " " * 27 + "12345678", "12345678"),
    ("ctx-gap-5", "C.I." + " " * 45 + "12345678", "12345678"),
    ("ctx-gap-6", "cédula es" + " " * 40 + "12345678", "12345678"),
    ("ctx-gap-7", "cédula" + " " * 45 + "12.345.678", "12345678"),
    ("ctx-gap-8", "rif" + " " * 50 + "123456784", "12345678"),
    ("ctx-w-1", "cédula del solicitante 12345678", "12345678"),
    ("ctx-w-2", "la cédula del ciudadano es 12345678", "12345678"),
    ("ctx-w-3", "cédula de identidad personal 12345678", "12345678"),
    ("ctx-w-4", "pasaporte 12345678", "12345678"),
    # --- homoglifos con espacio/punto/tab/salto o en palabras clave (M-2)
    ("hg-1", "В 12345678", "12345678"),
    ("hg-2", "В.12345678", "12345678"),
    ("hg-3", "Е\n12345678", "12345678"),
    ("hg-4", "В\t12345678", "12345678"),
    ("hg-5", "Ј 12345678 4", "12345678"),
    ("hg-6", "Ε 12345678", "12345678"),
    ("hg-7", "Р 12345678 4", "12345678"),
    ("hg-8", "Ѵ-12345678", "12345678"),
    ("hg-9", "ѕ-12345678", "12345678"),
    ("hg-10", "ν-12345678", "12345678"),
    ("hg-11", "Ϲ-12345678-4", "12345678"),
    ("hg-12", "сédula 12345678", "12345678"),
    ("hg-13", "Сédula 12345678", "12345678"),
    ("hg-14", "documentoο de identidad 12345678", "12345678"),
    ("hg-15", "identificaciοn 12345678", "12345678"),
    ("hg-16", "cédυla 12345678", "12345678"),
    ("hg-17", "с.і. 12345678", "12345678"),
    ("hg-18", "РІҒ 123456784", "12345678"),
    ("hg-19", "Нombre: Juan Perez", "Juan"),
    # --- dígitos separados, ruido y separadores (M-3)
    ("dig-1", "V-1 2 3 4 5 6 7 8", "12345678"),
    ("dig-2", "cédula 1 2 3 4 5 6 7 8", "12345678"),
    ("dig-3", "J 1 2 3 4 5 6 7 8 4", "12345678"),
    ("dig-4", "cédula 12-345-678", "12345678"),
    ("dig-5", "cédula 12/345/678", "12345678"),
    ("dig-6", "cédula 123 45 678", "12345678"),
    ("dig-7", "cédula 1234 5678", "12345678"),
    ("dig-8", "cédula 12345-678", "12345678"),
    ("dig-9", "V-12\t345\t678", "12345678"),
    ("dig-10", "V-1234́45678", "12345678"),
    ("dig-11", "V -  12345678", "12345678"),
    ("dig-12", "V:12345678", "12345678"),
    ("dig-13", "V#12345678", "12345678"),
    ("rif-1", "RIF: 1234567890", "12345678"),
    ("rif-2", "RIF: 12.345.678-4", "12345678"),
    ("rif-3", "J_12345678_4", "12345678"),
    ("rif-4", "J:12345678-4", "12345678"),
    ("rif-5", "J-12345678-45", "12345678"),
    # --- teléfonos (M-4)
    ("ph-1", "+58/412/123/4567", "1234567"),
    ("ph-2", "+58.412.123.4567", "1234567"),
    ("ph-3", "+58 - 412 - 123 4567", "1234567"),
    ("ph-4", "0414  123  4567", "1234567"),
    ("ph-5", "0414 - 123 - 4567", "1234567"),
    ("ph-6", "0414,123,4567", "1234567"),
    # --- correos (B-1)
    ("mail-1", "juan.perez(at)gmail.com", "juan.perez"),
    ("mail-2", "juan.perez [at] gmail.com", "juan.perez"),
    ("mail-3", "juan.perez@\ngmail.com", "juan.perez"),
    ("mail-4", "juan.perez\n@gmail.com", "juan.perez"),
    ("mail-5", "juan.perez @ gmail.com", "juan.perez"),
    ("mail-6", "juan@my_domain.com", "juan@"),
    ("mail-8", "juan.perez@gmail。com", "juan.perez"),
    ("mail-9", "a" * 70 + "@gmail.com", "a" * 65),
    # --- codificaciones (B-2): base64 partido/con prefijo, hex con separadores, URL/HTML
    ("enc-1", "Vi0x MjM0 NTY3 OA==", "Vi0x"),
    ("enc-2", "Vi0xMjM0.NTY3OA==", "Vi0x"),
    ("enc-3", "cedVi0xMjM0NTY3OA==", "Vi0x"),
    ("enc-4", "Vi0xMjM0NTY3OA===", "Vi0x"),
    ("enc-5", "56:2d:31:32:33:34:35:36:37:38", "56:2d"),
    ("enc-6", "56-2d-31-32-33-34-35-36-37-38", "56-2d"),
    ("enc-7", "V%2D12345678", "12345678"),
    ("enc-8", "&#86;-12345678", "12345678"),
    # --- controles: lo corregido en rondas previas debe seguir enmascarado
    ("ctl-1", "cédula es 12345678", "12345678"),
    ("ctl-2", "cédula Nº V-12345678", "12345678"),
    ("ctl-3", "cédula:\n12345678", "12345678"),
    ("ctl-4", "C.I. nro. 12345678", "12345678"),
    ("ctl-5", "V 00000001", "00000001"),
    ("ctl-6", "V-12,345,678", "12345678"),
    ("ctl-7", "J 12345678 4", "12345678"),
    ("ctl-8", "J-12.345.678-4", "12345678"),
    ("ctl-9", "0412.123.4567", "1234567"),
    ("ctl-10", "+58 412 123 4567", "1234567"),
    ("ctl-11", "0102 0123 45 0123456789", ACCOUNT_TAIL),
    ("ctl-12", "В-12345678", "12345678"),
    ("ctl-13", "V-١٢٣٤٥٦٧٨", "12345678"),
    ("ctl-14", "Ｖ－１２３４５６７８", "12345678"),
    ("ctl-15", "Y2VkdWxhIDEyMzQ1Njc4", "Y2Vk"),
]

# Se deben resolver en tiempo acotado (ReDoS, hallazgo A-1).
REDOS: list[tuple[str, str]] = [
    ("nm-1", "titular" + " " * 20000 + "x"),
    ("nm-2", "sr" + "\t" * 20000 + "x"),
    ("nm-3", "titular" + "\n" * 20000),
    ("b64-1", "-" * 20000 + "==="),
    ("b64-2", "/" * 20000 + "==="),
    ("b64-3", "+" * 20000 + "=A"),
    ("digits", "1" * 20000),
    ("sep-digits", "1-" * 10000),
    ("all-pii", "Solicitante: Juan Perez, cédula V-12345678, RIF J-12345678-4. " * 300),
]

KNOWN_LIMITS: list[tuple[str, str, str]] = [
    ("mail-7", "juan@пример.рф", "juan@"),
    ("ph-7", "0414_1234567", "1234567"),
    ("glue-2", "0412-12345670412-1234568", "1234567"),
    ("rif-6", "J-12345678", "12345678"),
]


def _mask(text: str) -> str:
    vault = EphemeralVault()
    masked, _ = shield("regr", text, vault=vault, blind_citizen_id="b" * 64)
    vault.zeroize("regr")
    return masked


@pytest.mark.parametrize(("case_id", "text", "needle"), MUST_MASK, ids=[c[0] for c in MUST_MASK])
def test_sensitive_value_is_masked(case_id: str, text: str, needle: str) -> None:
    try:
        masked = _mask(text)
    except ShieldResidualPiiError:
        return  # fail-closed también es aceptable
    assert needle not in masked, f"{case_id}: {masked!r}"


@pytest.mark.parametrize(("case_id", "text"), REDOS, ids=[c[0] for c in REDOS])
def test_pathological_input_resolves_in_bounded_time(case_id: str, text: str) -> None:
    start = time.perf_counter()
    try:
        _mask(text)
    except ShieldResidualPiiError:
        pass
    elapsed = time.perf_counter() - start
    assert elapsed < 1.0, f"{case_id}: {elapsed:.2f}s"


@pytest.mark.xfail(strict=False, reason="límite conocido de baja prioridad")
@pytest.mark.parametrize(
    ("case_id", "text", "needle"), KNOWN_LIMITS, ids=[c[0] for c in KNOWN_LIMITS]
)
def test_known_limits(case_id: str, text: str, needle: str) -> None:
    try:
        masked = _mask(text)
    except ShieldResidualPiiError:
        return
    assert needle not in masked


def test_partial_digit_run_at_window_edge_is_not_half_masked() -> None:
    """B-3: un run de dígitos cortado por la ventana no debe producir un [BANK_n] parcial."""
    masked = _mask("V-12345678" + "x" * 60 + "1" * 30 + " fin")
    assert "[BANK_" not in masked


def test_four_glued_cedulas_are_masked_or_fail_closed() -> None:
    try:
        masked = _mask("V-12345671V-12345672V-12345673V-12345674")
    except ShieldResidualPiiError:
        return
    assert "1234567" not in masked


def test_nfkc_expansion_returns_422_not_500(client) -> None:
    from tests.conftest import TOKEN_HEADERS

    response = client.post(
        "/api/v1/shield/inspect", json={"raw_text": "ﷺ" * 200}, headers=TOKEN_HEADERS
    )
    assert response.status_code == 422
    assert response.json()["error"] == "ERR_UNSAFE_INPUT"
