"""Gatillo 1 — detectores PII compartidos (core/pii_patterns.py). Datos 100% sintéticos."""

from __future__ import annotations

import base64

import pytest

from core.pii_patterns import find_pii
from core.text_normalizer import normalize_text


def kinds(text: str) -> list[tuple[str, str]]:
    return [(m.kind, text[m.start : m.end]) for m in find_pii(normalize_text(text))]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("V-00000001", [("CEDULA", "V-00000001")]),
        ("cédula V-12.345.678 fin", [("CEDULA", "V-12.345.678")]),
        ("e12345678", [("CEDULA", "e12345678")]),
        ("cédula: 12345678", [("CEDULA", "12345678")]),
        ("C.I. 12.345.678", [("CEDULA", "12.345.678")]),
        ("J-12345678-4", [("RIF", "J-12345678-4")]),
        ("RIF G200001100", [("RIF", "G200001100")]),  # compacto: letra + 8 + verificador
        ("solicitante: Persona Ficticia Alfa", [("NAME", "Persona Ficticia Alfa")]),
        ("Sr. Juan de la Cruz Perez trae", [("NAME", "Juan de la Cruz Perez")]),
        ("0412-0000001", [("PHONE", "0412-0000001")]),
        ("0212-0000002", [("PHONE", "0212-0000002")]),
        ("+58 414 1234567", [("PHONE", "+58 414 1234567")]),
        ("cuenta 00000000000000000001", [("BANK", "00000000000000000001")]),
        ("mail fixture@example.invalid ok", [("EMAIL", "fixture@example.invalid")]),
        ("paciente con Diabetes y VIH", [("CLINICAL", "Diabetes"), ("CLINICAL", "VIH")]),
    ],
)
def test_detects_structured_pii(text: str, expected: list[tuple[str, str]]) -> None:
    assert kinds(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # cuenta venezolana 4-4-2-10, agrupaciones libres y puntos
        ("cuenta 0102-0000-00-0000000001", [("BANK", "0102-0000-00-0000000001")]),
        ("cuenta 0102 0000 00 0000000001", [("BANK", "0102 0000 00 0000000001")]),
        ("cuenta 0102.0000.00.0000000001", [("BANK", "0102.0000.00.0000000001")]),
        ("cuenta 0102-0000-0000-0000-0001", [("BANK", "0102-0000-0000-0000-0001")]),
        # RIF con espacios y puntos
        ("J-12345678 4", [("RIF", "J-12345678 4")]),
        ("J-12.345.678-4", [("RIF", "J-12.345.678-4")]),
        ("J 12345678-4", [("RIF", "J 12345678-4")]),
        # cédula con separadores y palabras clave extendidas
        ("V 12345678", [("CEDULA", "V 12345678")]),
        ("V.12345678", [("CEDULA", "V.12345678")]),
        ("cédula nro 12345678", [("CEDULA", "12345678")]),
        ("C.I. Nº 12345678", [("CEDULA", "12345678")]),
        ("documento de identidad: 12345678", [("CEDULA", "12345678")]),
        # cédula de 9 dígitos V/E sin separador previo al último dígito: cédula, no RIF
        ("V-123456789", [("CEDULA", "V-123456789")]),
        # teléfono con punto y barra
        ("0412.000.0001", [("PHONE", "0412.000.0001")]),
        ("0412/0000001", [("PHONE", "0412/0000001")]),
        # nombres: mayúsculas, guion, apóstrofo, sin tragarse el marcador siguiente
        ("Solicitante: JUAN PEREZ", [("NAME", "JUAN PEREZ")]),
        ("Titular: María-José Pérez", [("NAME", "María-José Pérez")]),
        ("paciente: O'Brien Smith", [("NAME", "O'Brien Smith")]),
        ("ciudadano Pedro Gomez y Sr. Luis Mora", [("NAME", "Pedro Gomez"), ("NAME", "Luis Mora")]),
        # base64 corto y url-safe
        ("Vi0xMjM0NTY3OA==", [("ENCODED", "Vi0xMjM0NTY3OA==")]),
        # clínico: derivados
        ("es diabético", [("CLINICAL", "diabético")]),
        ("tiene HIV", [("CLINICAL", "HIV")]),
    ],
)
def test_detects_extended_formats(text: str, expected: list[tuple[str, str]]) -> None:
    assert kinds(text) == expected


@pytest.mark.parametrize("text", ["monto 1500", "año 2026", "fecha 13/11/2026", "pág. 12 de 20"])
def test_common_numbers_are_not_pii(text: str) -> None:
    assert kinds(text) == []


def test_rif_is_not_split_into_cedula_or_phone() -> None:
    assert [k for k, _ in kinds("J-00000000-0 y V-00000001-5")] == ["RIF", "RIF"]


def test_bank_account_is_not_reported_as_phone_or_cedula() -> None:
    assert [k for k, _ in kinds("04121234567890123456")] == ["BANK"]


def test_matches_are_sorted_and_non_overlapping() -> None:
    text = normalize_text("V-00000001 0412-0000001 fixture@example.invalid 00000000000000000001")
    matches = find_pii(text)
    assert [m.start for m in matches] == sorted(m.start for m in matches)
    assert all(a.end <= b.start for a, b in zip(matches, matches[1:], strict=False))


@pytest.mark.parametrize(
    "text", ["", "Solicito una beca para mi hijo", "monto 1500 bolívares", "12345"]
)
def test_clean_text_has_no_matches(text: str) -> None:
    assert find_pii(normalize_text(text)) == ()


def test_encoded_pii_is_detected_base64_and_hex() -> None:
    payload = "cedula V-12345678 y telefono 0412-0000001"
    b64 = base64.b64encode(payload.encode()).decode()
    hexed = payload.encode().hex()
    assert [k for k, _ in kinds(f"datos: {b64}")] == ["ENCODED"]
    assert [k for k, _ in kinds(f"datos: {hexed}")] == ["ENCODED"]


def test_harmless_encoded_blob_is_not_flagged() -> None:
    blob = base64.b64encode(b"hola mundo sin datos personales").decode()
    assert kinds(blob) == []


def test_pathological_input_is_linear_time() -> None:
    import time

    text = ("a" * 50_000) + "@" + ("1-" * 10_000)
    start = time.perf_counter()
    find_pii(text)
    assert time.perf_counter() - start < 1.0
