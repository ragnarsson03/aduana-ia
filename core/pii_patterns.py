"""Detectores de PII compartidos por SHIELD (etapa 1) y GUARD-OUT (etapa 3).

Viven en ``core/`` para que ``stage3`` no dependa de ``stage1``. Reciben texto YA normalizado
(``core.text_normalizer.normalize_text``). Regex lineales: anclas con lookbehind, cuantificadores
acotados y sin anidamiento ambiguo (sin ReDoS).

Decisiones:
- Se enmascara de forma preventiva todo patrón RIF aunque su dígito sea inválido.
- RIF: J/P/G/C con separadores opcionales; V/E exigen separador antes del dígito verificador. Así
  ``V-123456789`` (9 dígitos juntos) es CÉDULA, no RIF. RIF abreviado (cuerpo de 7) no se detecta.
- Cédula: letra V/E (con ``-``, ``.`` o espacio opcional) + 5-9 dígitos; sin letra solo tras una
  palabra clave ("cédula", "C.I.", "documento de identidad", con "nro/Nº"), para no enmascarar
  montos ni años.
- Cuenta: run completo con >= 20 dígitos y separadores espacio, ``-``, ``.``, ``/``;
  una lista cubierta íntegramente por teléfonos conserva sus tokens PHONE.
- Teléfono: 04xx y 02xx, separadores ``espacio - . /``; un número de 10 dígitos que empiece por 2
  (p. ej. un monto) se enmascara por la regla preventiva (falso positivo conocido).
- Nombres: solo contextuales (marcador + 1 a 4 palabras capitalizadas o en mayúsculas, con guion
  y apóstrofo). Sin marcador o en minúsculas no se detectan (límite conocido).
- ``ENCODED``: bloque Base64 (estándar o url-safe, >= 12 caracteres) o hex (>= 16) que decodificado
  a UTF-8 contiene PII. También admite fragmentos Base64 con padding y hex por pares.
- Prioridad ante solapes: ENCODED > EMAIL > BANK > RIF > PHONE > CEDULA > NAME > CLINICAL.
"""

from __future__ import annotations

import base64
import binascii
import re
from dataclasses import dataclass
from typing import Final

from core.text_normalizer import normalize_text

KINDS: Final[tuple[str, ...]] = (
    "ENCODED",
    "EMAIL",
    "BANK",
    "RIF",
    "PHONE",
    "CEDULA",
    "NAME",
    "CLINICAL",
)
_MAX_DECODE_DEPTH: Final[int] = 2

_SEP = r"[\s.\-/_,:#]"
_DOTTED = r"[0-9]{1,2}[.,  ][0-9]{3}[.,  ][0-9]{3}"
_RIF_BODY = r"(?:[0-9]{8}|[0-9]{2}\.[0-9]{3}\.[0-9]{3})"
_NAME_WORD = r"[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ'’\-]+"
# Every component is bounded; at most three intervening short words.
_FILLER = r"[\s:.\-#°ºª]{0,64}(?:(?i:[a-záéíóúñ]{1,16})[\s:.\-#°ºª]{1,64}){0,3}"


def _number(minimum: int, maximum: int) -> str:
    return rf"[0-9](?:{_SEP}{{0,3}}[0-9]){{{minimum - 1},{maximum - 1}}}"


_EMAIL = re.compile(
    r"(?<![A-Za-z0-9._%+\-])[A-Za-z0-9._%+\-]++"
    r"\s{0,64}(?:@|(?i:\(at\)|\[at\]| arroba ))\s{0,64}"
    r"[\w\-]{1,63}(?:(?:\.|\s{0,3}(?i:\(dot\))\s{0,3})[\w\-]{1,63}){1,4}"
)
# Consume a whole run once, then count digits. Never restart inside a failed run.
_BANK = re.compile(r"(?<![A-Za-z0-9])[0-9](?:[\s.\-/]*+[0-9])*+")
_RIF = re.compile(
    rf"(?<![A-Za-z0-9])(?:[JPGCjpgc]{_SEP}{{0,3}}{_number(9, 10)}"
    rf"|[VEve]{_SEP}{{0,3}}{_RIF_BODY}{_SEP}{{1,3}}[0-9])(?![0-9])"
)
_RIF_CONTEXT = re.compile(rf"(?<![A-Za-z])(?i:rif){_FILLER}(?P<v>{_number(9, 10)})(?![0-9])")
_PHONE = re.compile(
    r"(?<![0-9A-Za-z])(?:(?:\+|00)?58[\s.\-/]{0,3}\(?0?|\(?0)(?:4(?:12|14|16|22|24|26)|2[0-9]{2})\)?"
    r"(?:[\s.\-/_,]{0,3}[0-9]){7}(?![0-9])"
)
_CEDULA_LETTER = re.compile(rf"(?<![A-Za-z0-9])[VEve]{_SEP}{{0,4}}{_number(5, 9)}(?![0-9])")
_CEDULA_CONTEXT = re.compile(
    r"(?<![A-Za-z])(?i:c[ée]dula(?: de identidad)?|documento[o]? de identidad|identificaci[oó]n|"
    r"c\.?i\.?|ced\.?|dni|pasaporte)"
    rf"{_FILLER}(?P<v>(?:[VEve]{_SEP}{{0,3}})?{_number(5, 10)})(?![0-9])"
)
_NAME = re.compile(
    r"(?<![A-Za-z])(?i:solicitante|ciudadan[oa]|beneficiari[oa]|paciente|titular|nombre|"
    r"se[ñn]or[a]?|sr\.?|sra\.?)\s{0,20}:?\s{0,20}"
    rf"(?P<v>{_NAME_WORD}(?:\s{{1,20}}(?:(?:de|del|la|las|los)\s{{1,20}}){{0,3}}{_NAME_WORD}){{0,3}})"
)
# Cargos y términos comerciales que siguen a un marcador sin ser nombres de persona.
_NAME_STOPWORDS = frozenset(
    {
        "comercial",
        "final",
        "presidente",
        "presidenta",
        "director",
        "directora",
        "general",
        "aduana",
        "del",
        "de",
        "producto",
        "legal",
        "fiscal",
        "jurídico",
        "juridico",
    }
)
_B64 = re.compile(r"(?<![A-Za-z0-9+/\-_=])[A-Za-z0-9+/\-_]{12,4096}+={0,3}(?![A-Za-z0-9+/=\-_])")
# Runs bound both encoded searches without changing their original boundaries.
_ENCODED_RUN = re.compile(r"[A-Za-z0-9+/=_\-]{12,}")
_NAME_MARKERS = (
    "solicitante",
    "ciudadan",
    "beneficiari",
    "paciente",
    "titular",
    "nombre",
    "se\u00f1or",
    "senor",
    "sr",
)

_HEX = re.compile(r"(?<![0-9A-Fa-f])(?:[0-9A-Fa-f]{2}){8,}(?![0-9A-Fa-f])")
_HEX_SEPARATED = re.compile(
    r"(?<![0-9A-Fa-f:\-])[0-9A-Fa-f]{2}(?:[:\-][0-9A-Fa-f]{2}){7,4095}+(?![0-9A-Fa-f:\-])"
)
_B64_SPLIT = re.compile(
    r"(?<![A-Za-z0-9+/=_\-])[A-Za-z0-9+/_\-]{4,4096}+"
    r"(?:[ .\t\r\n]{1,3}[A-Za-z0-9+/_\-]{2,4096}+){0,32}={1,3}(?![A-Za-z0-9+/=_\-])"
)

CLINICAL_TERMS: Final[tuple[str, ...]] = (
    "diabetes",
    "diabético",
    "diabética",
    "diabetico",
    "diabetica",
    "hipertensión",
    "hipertension",
    "hipertenso",
    "hipertensa",
    "cáncer",
    "cancer",
    "vih",
    "hiv",
    "sida",
    "tuberculosis",
    "epilepsia",
    "epiléptico",
    "asma",
    "depresión",
    "depresion",
    "esquizofrenia",
    "trastorno bipolar",
    "ansiedad",
    "hepatitis",
    "leucemia",
    "insuficiencia renal",
    "insuficiencia cardíaca",
    "insuficiencia cardiaca",
    "cardiopatía",
    "cardiopatia",
    "cardiópata",
    "cardiopata",
    "discapacidad",
    "embarazo",
    "covid",
    "dengue",
    "malaria",
    "paludismo",
    "parkinson",
    "alzheimer",
    "lupus",
    "esclerosis múltiple",
    "esclerosis multiple",
    "trasplante",
    "quimioterapia",
    "diálisis",
    "dialisis",
    "anemia falciforme",
)
_CLINICAL_BODY = "|".join(re.escape(t) for t in sorted(CLINICAL_TERMS, key=len, reverse=True))
_LETTERS = "A-Za-zÁÉÍÓÚÑáéíóúñ"
_CLINICAL = re.compile(rf"(?<![{_LETTERS}])(?i:{_CLINICAL_BODY})(?![{_LETTERS}])")


@dataclass(frozen=True, slots=True)
class PiiMatch:
    kind: str  # uno de ``KINDS``
    start: int
    end: int


def _decode_candidate(token: str, *, is_hex: bool) -> str | None:
    try:
        if is_hex:
            raw = bytes.fromhex(token)
        else:
            standard = token.rstrip("=").replace("-", "+").replace("_", "/")
            raw = base64.b64decode(standard + "=" * (-len(standard) % 4), validate=True)
        return raw.decode("utf-8")
    except (binascii.Error, ValueError):
        return None


def _looks_like_plain_word(token: str) -> bool:
    return token.isalpha() and (token.islower() or token.istitle() or token.isupper())


Region = tuple[int, int]


def _extend_digit_bounds(text: str, lo: int, hi: int) -> Region:
    """No convertir el borde de una ventana en el final artificial de un identificador."""
    lo, hi = max(0, lo), min(len(text), max(0, hi))
    while hi < len(text) and (text[hi] in "0123456789.-/_," or text[hi].isspace()):
        hi += 1
    while lo > 0 and (text[lo - 1] in "0123456789.-/_," or text[lo - 1].isspace()):
        lo -= 1
    return lo, hi


_DIGIT_CLUSTER = re.compile(r"[0-9](?:[^0-9]{0,40}[0-9])*")
_DIGIT_PATTERNS: Final = (  # (prioridad, regex, grupo)
    (2, _BANK, 0),
    (3, _RIF, 0),
    (3, _RIF_CONTEXT, "v"),
    (4, _PHONE, 0),
    (5, _CEDULA_LETTER, 0),
    (5, _CEDULA_CONTEXT, "v"),
)
_LEFT_PAD: Final[int] = 160
_RIGHT_PAD: Final[int] = 16


def _merge(regions: list[Region]) -> list[Region]:
    merged: list[Region] = []
    for lo, hi in sorted(regions):
        if merged and lo <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
        else:
            merged.append((lo, hi))
    return merged


def _digit_regions(text: str, lo: int, hi: int) -> list[Region]:
    """Vecindarios de dígitos: los patrones numéricos solo se evalúan donde hay dígitos."""
    return _merge(
        [
            _extend_digit_bounds(
                text, max(lo, m.start() - _LEFT_PAD), min(hi, m.end() + _RIGHT_PAD)
            )
            for m in _DIGIT_CLUSTER.finditer(text, lo, hi)
        ]
    )


def _encoded_spans(text: str, depth: int, lo: int, hi: int) -> list[Region]:
    spans: list[Region] = []
    candidates: list[tuple[re.Match[str], bool]] = []
    for run in _ENCODED_RUN.finditer(text, lo, hi):
        for pattern, is_hex in ((_B64, False), (_HEX, True)):
            candidates.extend((m, is_hex) for m in pattern.finditer(text, run.start(), run.end()))
    if text.find("=", lo, hi) != -1:
        candidates.extend((m, False) for m in _B64_SPLIT.finditer(text, lo, hi))
    if text.find(":", lo, hi) != -1 or text.find("-", lo, hi) != -1:
        candidates.extend((m, True) for m in _HEX_SEPARATED.finditer(text, lo, hi))
    for match, is_hex in candidates:
        token = match.group()
        if is_hex:
            token = token.replace(":", "").replace("-", "")
        else:
            token = re.sub(r"[ .\t\r\n]", "", token)
            if _looks_like_plain_word(token):
                continue
        # Bounded prefix probing also catches a label glued to a padded blob.
        offsets = range(min(17, len(token) - 11)) if not is_hex and token.endswith("=") else (0,)
        for offset in offsets:
            decoded = _decode_candidate(token[offset:], is_hex=is_hex)
            if not decoded:
                continue
            try:
                sensitive = bool(_scan(normalize_text(decoded), depth + 1))
            except ValueError:
                sensitive = True  # excessive decoded expansion is unsafe too
            if sensitive:
                spans.append(match.span())
                break
    return spans


def _is_bank_run(value: str) -> bool:
    if sum(ch.isdigit() for ch in value) < 20:
        return False
    # Preserve an existing list of complete phones (e.g. two phones joined by /).
    phones = list(_PHONE.finditer(value))
    if len(phones) < 2:
        return True
    cursor = 0
    for phone in phones:
        if any(ch.isdigit() for ch in value[cursor : phone.start()]):
            return True
        cursor = phone.end()
    return any(ch.isdigit() for ch in value[cursor:])


def _scan(text: str, depth: int, regions: list[Region] | None = None) -> list[tuple[str, int, int]]:
    """Candidatos (tipo, inicio, fin) filtrados por prioridad y sin solapes.

    ``regions=None`` escanea todo el texto; con regiones solo esos tramos (p. ej. el entorno de
    los tokens ya insertados, para la comprobación de residual).
    """
    # Lowercase is only a presence filter: original text retains offsets, case and boundaries.
    # Python IGNORECASE also accepts dotted/dotless I and long S.
    lowered = text.replace("\u0131", "i").replace("\u017f", "s").replace("\u0130", "I").lower()
    candidates: list[tuple[int, int, int]] = []  # (prioridad, inicio, fin)
    for lo, hi in regions if regions is not None else [(0, len(text))]:
        lo, hi = _extend_digit_bounds(text, lo, hi)
        if depth < _MAX_DECODE_DEPTH:
            candidates += [(0, s, e) for s, e in _encoded_spans(text, depth, lo, hi)]
        if any(lowered.find(marker, lo, hi) != -1 for marker in ("@", "(at)", "[at]", " arroba ")):
            candidates += [(1, *m.span()) for m in _EMAIL.finditer(text, lo, hi)]
        for d_lo, d_hi in _digit_regions(text, lo, hi):
            for priority, pattern, group in _DIGIT_PATTERNS:
                candidates += [
                    (priority, *m.span(group))
                    for m in pattern.finditer(text, d_lo, d_hi)
                    if pattern is not _BANK or _is_bank_run(m.group())
                ]
        # Match regex handling of negative region bounds.
        filter_lo, filter_hi = max(0, lo), max(0, hi)
        if any(lowered.find(marker, filter_lo, filter_hi) != -1 for marker in _NAME_MARKERS):
            candidates += [
                (6, *m.span("v"))
                for m in _NAME.finditer(text, lo, hi)
                if m.group("v").split()[0].casefold() not in _NAME_STOPWORDS
            ]
        if any(lowered.find(term, filter_lo, filter_hi) != -1 for term in CLINICAL_TERMS):
            candidates += [(7, *m.span()) for m in _CLINICAL.finditer(text, lo, hi)]

    taken = bytearray(len(text))
    accepted: list[tuple[str, int, int]] = []
    for priority, start, end in sorted(candidates, key=lambda c: (c[0], c[1])):
        if any(taken[start:end]):
            continue
        taken[start:end] = b"" * (end - start)
        accepted.append((KINDS[priority], start, end))
    return sorted(accepted, key=lambda item: item[1])


def find_pii(normalized_text: str, *, regions: list[Region] | None = None) -> tuple[PiiMatch, ...]:
    """Coincidencias ordenadas por posición y sin solapes. Recibe texto ya normalizado.

    ``regions`` limita el escaneo a tramos ``(inicio, fin)``; el llamador debe dejar margen
    suficiente alrededor de lo que le interesa (los lookbehind ven el texto previo al tramo).
    Los bordes numéricos se extienden al run completo para evitar enmascarados parciales.
    """
    return tuple(
        PiiMatch(kind, start, end) for kind, start, end in _scan(normalized_text, 0, regions)
    )
