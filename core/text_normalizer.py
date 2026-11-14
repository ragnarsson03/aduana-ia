"""Normalización canónica previa a SHIELD y a GUARD (evita evasión por Unicode).

Pasos (hasta punto fijo): NFKC -> eliminación de invisibles (``Cf``, controles, rellenos,
selectores) -> canonicalización de compatibilidad:
- dígitos Unicode ``Nd`` (árabe, devanagari...) -> ASCII;
- guiones ``Pd`` y signo menos -> ``-``; U+2028/U+2029 -> salto de línea;
- homoglifos cirílicos/griegos/small-caps -> latín en palabras mixtas o prefijos de números;
  no se altera texto cirílico puro sin contexto numérico;
- escapes URL/HTML y puntos ideográficos se canonicalizan; marcas Mn entre dígitos se eliminan.
Conserva espacios, saltos de línea, tabuladores y acentos. Idempotente.

Límite de expansión: si NFKC infla el texto más de 2x (+64) se lanza ``ValueError`` (DoS por
U+FDFA y similares); el llamador debe rechazar la entrada.

Rendimiento: texto ASCII sin controles => retorno inmediato (ASCII es estable bajo NFKC).
"""

from __future__ import annotations

import re
import unicodedata
from html import unescape
from typing import Final
from urllib.parse import unquote

_INVISIBLE: Final = re.compile(
    "[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f"
    "­͏؜܏࢐࢑࣢ᅟᅠ឴឵᠋-᠎"
    "​-‏‪-‮⁠-⁤⁦-⁯⠀ㅤ︀-️﻿"
    "ﾠ￹-￻"
    "\U000110bd\U000110cd\U00013430-\U0001343f\U0001bca0-\U0001bca3\U0001d173-\U0001d17a"
    "\U000e0001\U000e0020-\U000e007f\U000e0100-\U000e01ef]"
)
_ASCII_CONTROLS: Final = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# After NFKC/invisible removal, Latin-1 characters need no further folding.
_NON_ASCII: Final = re.compile(r"[^\x00-\xff]")
_CONFUSABLE: Final[dict[str, str]] = {
    "В": "V",
    "Е": "E",
    "Ј": "J",
    "Р": "P",
    "С": "C",  # cirílico mayúsculas
    "Ε": "E",
    "Ρ": "P",  # griego
    "ο": "o",
    "ν": "V",
    "Ν": "N",
    "Ѵ": "V",
    "ѕ": "V",
    "Ϲ": "C",
    "Σ": "C",
    "υ": "u",
    "Н": "N",
    "Т": "T",
    "І": "I",
    "Ғ": "F",
    "ᴠ": "V",
    "ᴇ": "E",
    "ᴊ": "J",
    "ᴘ": "P",
    "ᴄ": "C",
    "ɢ": "G",  # small caps
    "а": "a",
    "е": "e",
    "о": "o",
    "р": "p",
    "с": "c",
    "і": "i",
    "ј": "j",  # cirílico minúsculas
}
_MAX_PASSES: Final[int] = 4
_EXPANSION_FACTOR: Final[int] = 2
_EXPANSION_SLACK: Final[int] = 64


def _fold(match: re.Match[str]) -> str:
    ch = match.group()
    category = unicodedata.category(ch)
    if category == "Nd":
        return str(unicodedata.decimal(ch))
    if category == "Pd" or ch in "−⁃":
        return "-"
    if ch in "  ":
        return "\n"
    if ch in "。｡":
        return "."

    return ch


_WORD = re.compile(r"[^\W_]+(?:\.[^\W_]+)*", re.UNICODE)
_PREFIX = re.compile(r"(?<!\w)[^\W_](?=[\s.\-_/]{0,3}[0-9])", re.UNICODE)
_RIF_KEYWORD = re.compile(r"(?<!\w)Р[ІI][ҒF](?=[\s:.\-#]{0,64}[0-9])")
_DIGIT_NOISE = re.compile(r"(?<=[0-9])[^\w]++(?=[0-9])")


def _fold_word(match: re.Match[str]) -> str:
    word = match.group()
    if any((ch.isascii() and ch.isalnum()) or "LATIN" in unicodedata.name(ch, "") for ch in word):
        return "".join(_CONFUSABLE.get(ch, ch) for ch in word)
    return word


def _fold_prefix(match: re.Match[str]) -> str:
    return _CONFUSABLE.get(match.group(), match.group())


def _strip_digit_marks(match: re.Match[str]) -> str:
    return "".join(ch for ch in match.group() if unicodedata.category(ch) != "Mn")


def normalize_text(text: str) -> str:
    """NFKC + invisibles + canonicalización; idempotente (punto fijo)."""
    for _ in range(_MAX_PASSES):
        decoded = unescape(text) if "&" in text else text
        decoded = unquote(decoded) if "%" in decoded else decoded
        if decoded == text:
            break
        text = decoded
    if text.isascii():
        return _ASCII_CONTROLS.sub("", text) if _ASCII_CONTROLS.search(text) else text
    text = text.replace("…", "...")
    limit = _EXPANSION_FACTOR * len(text) + _EXPANSION_SLACK
    current = text
    for _ in range(_MAX_PASSES):
        expanded = unicodedata.normalize("NFKC", current)
        if len(expanded) > limit:
            raise ValueError("Expansión Unicode excesiva.")
        folded = _NON_ASCII.sub(_fold, _INVISIBLE.sub("", expanded))
        if _NON_ASCII.search(folded):
            folded = _RIF_KEYWORD.sub("RIF", folded)
            folded = _WORD.sub(_fold_word, folded)
            folded = _PREFIX.sub(_fold_prefix, folded)
            # Combining marks between digits carry no identifier semantics.
            folded = _DIGIT_NOISE.sub(_strip_digit_marks, folded)
        if folded == current:
            break
        current = folded
    return current
