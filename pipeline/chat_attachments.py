"""Streaming efímero en RAM (hasta 100 MB), extracción limpia PDF/CSV/TXT y Map-Reduce.

Reglas SDD:
- Límite de hasta 100 MB (``MAX_CHAT_ATTACHMENT_BYTES = 100 * 1024 * 1024``).
- Cero escritura en disco (ni SQLite, ni D1, ni R2): el archivo se procesa por fragmentos
  (``AsyncIterable[bytes]``) en memoria y cada buffer ``bytearray`` se sobrescribe con ``0x00``.
- Extracción limpia en RAM: prohibido volcar cabeceras ``%PDF-1.4`` o diccionarios ``obj``.
  Los PDFs descomprimen ``FlateDecode`` / ``ASCII85Decode``, traducen mapas ``/ToUnicode``
  (``beginbfchar`` / ``beginbfrange``) y extraen bloques ``BT...ET``.
- Ventana de contexto multi-turno en RAM: soporta Caso A (solo texto + historial), Caso B
  (texto + archivo) y Caso C (solo archivo con prompt por defecto).
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import re
import time
import unicodedata
import zlib
from collections import Counter
from collections.abc import AsyncIterable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import PurePath
from typing import Final

from core import crypto
from core.config import MAX_RAW_TEXT_CHARS
from core.context import ShieldMeta
from core.crypto import rif_mod11_valid
from core.ephemeral_vault import EphemeralVault
from core.errors import AttachmentValidationError, ShieldResidualPiiError
from core.pii_patterns import KINDS, find_pii
from core.text_normalizer import normalize_text
from pipeline.stage1_shield import MAX_PASSES, _identity_key, _token_windows

MAX_CHAT_ATTACHMENT_BYTES: Final[int] = 100 * 1024 * 1024  # 100 MB
STREAM_CHUNK_SIZE: Final[int] = 64 * 1024  # 64 KB por fragmento
MAX_PDF_RAM_BUFFER: Final[int] = 32 * 1024 * 1024  # 32 MB buffer RAM para descompresión PDF
MAX_FILENAME_CHARS: Final[int] = 80
MAX_MAP_FRAGMENT_CHARS: Final[int] = 480
MAX_REDUCED_DOC_CHARS: Final[int] = 4_800
MAX_UI_PREVIEW_CHARS: Final[int] = 280
MAX_DOC_CONTEXT_CHARS: Final[int] = 1_800
ROLLING_REDUCE_BATCH: Final[int] = 32

DEFAULT_ATTACHMENT_PROMPT: Final[str] = (
    "Analiza exhaustivamente el documento adjunto, resume sus hallazgos clave, "
    "verifica su cumplimiento normativo y emite un dictamen técnico."
)

ALLOWED_EXTENSIONS: Final[dict[str, frozenset[str]]] = {
    ".txt": frozenset({"text/plain", "application/octet-stream"}),
    ".md": frozenset({"text/plain", "text/markdown", "application/octet-stream"}),
    ".csv": frozenset(
        {
            "text/csv",
            "application/csv",
            "text/plain",
            "application/vnd.ms-excel",
            "application/octet-stream",
        }
    ),
    ".json": frozenset({"application/json", "text/plain", "application/octet-stream"}),
    ".pdf": frozenset({"application/pdf", "application/x-pdf", "application/octet-stream"}),
}

_SAFE_FILENAME_RE: Final = re.compile(r"[^A-Za-z0-9._-]+")
_PDF_OBJ_RE: Final = re.compile(rb"(\d+)\s+0\s+obj(.*?)endobj", re.DOTALL)
_PDF_STREAM_RE: Final = re.compile(rb"stream\r?\n(.*?)\s*endstream", re.DOTALL)
_PDF_SKIP_DICT_RE: Final = re.compile(
    rb"/Subtype\s*/(?:Image|Type1C|CIDFontType0C|XML)|/Length1\s+\d+|/Type\s*/(?:Metadata|XRef)"
)
_PDF_BFCHAR_BLOCK_RE: Final = re.compile(rb"beginbfchar(.*?)endbfchar", re.DOTALL)
_PDF_BFRANGE_BLOCK_RE: Final = re.compile(rb"beginbfrange(.*?)endbfrange", re.DOTALL)
_PDF_BFCHAR_PAIR_RE: Final = re.compile(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>")
_PDF_BFRANGE_SIMPLE_RE: Final = re.compile(
    rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>"
)
_PDF_BFRANGE_ARRAY_RE: Final = re.compile(
    rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]", re.DOTALL
)
_PDF_TOUNICODE_REF_RE: Final = re.compile(rb"/ToUnicode\s+(\d+)\s+0\s+R")
_PDF_FONT_RES_RE: Final = re.compile(rb"/([A-Za-z0-9_+.-]+)\s+(\d+)\s+0\s+R")
_PDF_BT_TOKEN_RE: Final = re.compile(
    rb"/([A-Za-z0-9_+.-]+)\s+[-0-9.]+\s+Tf"
    rb"|\(([^()\\]*(?:\\.[^()\\]*)*)\)"
    rb"|<([0-9A-Fa-f\s]{2,})>"
    rb"|(T\*|TD|Td|Tm|ET)"
)
_PDF_NOISE_LINE_RE: Final = re.compile(
    r"(?:^%PDF-|^\d+\s+0\s+obj\b|^endobj\b|^stream\b|^endstream\b|^xref\b|^trailer\b"
    r"|/Creator\b|/Producer\b|/CreationDate\b|/ModDate\b|/BaseFont\b|/FontDescriptor\b"
    r"|Mozilla/5\.0|HeadlessChrome|Skia/PDF|AppleWebKit)",
    re.IGNORECASE,
)
_TOKEN_LITERAL_RE: Final = re.compile(r"\[(?:" + "|".join(KINDS) + r")_[0-9]+\]")
_DOMAIN_KEYWORDS: Final[tuple[str, ...]] = (
    "salud",
    "clínic",
    "clinic",
    "médic",
    "medic",
    "patolog",
    "arancel",
    "exoneraci",
    "aduana",
    "seniat",
    "factura",
    "monto",
    "contenedor",
    "manifiesto",
    "urgente",
    "prioridad",
    "recaudo",
    "auditor",
    "vulnerab",
    "riesgo",
    "hallazgo",
    "normativ",
    "ignora",
    "instrucciones",
    "exfiltra",
    "clave",
)


@dataclass(slots=True)
class _StreamShieldState:
    counters: Counter[str] = field(default_factory=Counter)
    tokens: dict[tuple[str, str], str] = field(default_factory=dict)
    token_map: dict[str, str] = field(default_factory=dict)
    rif_results: list[bool] = field(default_factory=list)
    kinds: set[str] = field(default_factory=set)
    occurrences: int = 0


@dataclass(frozen=True, slots=True)
class ExtractedAttachment:
    sanitized_name: str
    mime_type: str
    size_bytes: int
    sha256_hex: str
    extracted_text: str
    chunks_processed: int = 1

    def __repr__(self) -> str:  # Zero-Leak
        return "[REDACTED_LARGE_PAYLOAD]"


@dataclass(frozen=True, slots=True)
class StreamedChatPrepared:
    sanitized_name: str | None
    mime_type: str | None
    size_bytes: int
    sha256_hex: str | None
    chunks_processed: int
    reduced_masked_text: str
    ui_masked_preview: str
    document_context_masked: str | None
    shield_meta: ShieldMeta

    def __repr__(self) -> str:  # Zero-Leak
        return "[REDACTED_LARGE_PAYLOAD]"


def sanitize_attachment_filename(file_name: str, mime_type: str) -> tuple[str, str, str]:
    """Valida nombre de archivo, previene Path Traversal y verifica extensión/MIME."""
    raw_name = file_name.strip()
    if not raw_name or "\x00" in raw_name:
        raise AttachmentValidationError("Nombre de archivo adjunto vacío o inválido.")

    if ".." in raw_name or "/" in raw_name or "\\" in raw_name:
        raise AttachmentValidationError("Ruta de archivo no permitida (Path Traversal).")

    pure = PurePath(raw_name)
    ext = pure.suffix.lower()
    stem = _SAFE_FILENAME_RE.sub("_", pure.stem).strip("._-")
    if not stem:
        stem = "adjunto"
    cleaned = f"{stem[:MAX_FILENAME_CHARS]}{ext}"

    if ext not in ALLOWED_EXTENSIONS:
        raise AttachmentValidationError("Extensión de archivo no permitida en Chat IA.")

    clean_mime = mime_type.split(";")[0].strip().lower() if mime_type else ""
    allowed_mimes = ALLOWED_EXTENSIONS[ext]
    if clean_mime not in allowed_mimes:
        raise AttachmentValidationError("Tipo MIME no coincide con la extensión permitida.")

    return cleaned, clean_mime, ext


def _decode_pdf_literal(raw: bytes, cmap: dict[int, str] | None = None) -> str:
    """Decodifica literales PDF ``(...)`` incluyendo escapes octales ``\\ddd`` y CMap."""
    chars: list[str] = []
    lookup = cmap or {}
    i = 0
    n = len(raw)
    while i < n:
        ch = raw[i]
        if ch == 0x5C and i + 1 < n:
            nxt = raw[i + 1]
            if 0x30 <= nxt <= 0x37:
                j = i + 1
                while j < min(i + 4, n) and 0x30 <= raw[j] <= 0x37:
                    j += 1
                code = int(raw[i + 1 : j].decode("ascii"), 8) & 0xFF
                chars.append(lookup.get(code, chr(code)))
                i = j
            elif nxt in (0x6E, 0x72, 0x74):
                chars.append(" ")
                i += 2
            elif nxt in (0x0A, 0x0D):
                i += 2
            else:
                chars.append(lookup.get(nxt, chr(nxt)))
                i += 2
        else:
            chars.append(lookup.get(ch, chr(ch)))
            i += 1
    return "".join(chars)


def _decode_pdf_hex_string(
    hex_bytes: bytes,
    active_cmap: dict[int, str],
    global_cmap: dict[int, str],
) -> str:
    """Decodifica cadenas hexadecimales PDF ``<...>`` (UTF-16BE o glifos ToUnicode)."""
    compact = re.sub(rb"\s+", b"", hex_bytes).decode("ascii", errors="ignore")
    if not compact:
        return ""
    if len(compact) % 2 == 1:
        compact += "0"

    if compact.upper().startswith("FEFF"):
        try:
            return bytes.fromhex(compact[4:]).decode("utf-16-be", errors="ignore")
        except ValueError:
            return ""

    # Si el CMap tiene claves de 2 bytes (Skia/Chrome Identity-H) o longitud múltiplo de 4
    out_chars: list[str] = []
    if len(compact) % 4 == 0:
        mapped_2b: list[str] = []
        hits = 0
        for idx in range(0, len(compact), 4):
            code = int(compact[idx : idx + 4], 16)
            ch = active_cmap.get(code) or global_cmap.get(code)
            if ch:
                mapped_2b.append(ch)
                hits += 1
            elif 0x20 <= code <= 0x7E or 0xA0 <= code <= 0x024F:
                mapped_2b.append(chr(code))
        if hits > 0 or (mapped_2b and len(mapped_2b) == len(compact) // 4):
            return "".join(mapped_2b)

    for idx in range(0, len(compact), 2):
        code = int(compact[idx : idx + 2], 16)
        ch = active_cmap.get(code) or global_cmap.get(code)
        if ch:
            out_chars.append(ch)
        elif 0x20 <= code <= 0x7E or 0xA0 <= code <= 0xFF:
            out_chars.append(chr(code))
    return "".join(out_chars)


def _decompress_pdf_obj_stream(body: bytes) -> bytes | None:
    """Descomprime un stream de objeto PDF ignorando imágenes, fuentes binarias y XRef."""
    if _PDF_SKIP_DICT_RE.search(body):
        return None
    m = _PDF_STREAM_RE.search(body)
    if m is None:
        return None
    raw = m.group(1)
    hdr = body[: m.start()]
    try:
        if b"ASCII85Decode" in hdr or b"/A85" in hdr:
            s = raw.strip()
            if not s.endswith(b"~>"):
                s += b"~>"
            raw = base64.a85decode(s, adobe=True)
        elif b"ASCIIHexDecode" in hdr or b"/AHx" in hdr:
            cleaned_hex = re.sub(rb"[^0-9A-Fa-f]", b"", raw.split(b">")[0])
            if len(cleaned_hex) % 2 == 1:
                cleaned_hex += b"0"
            raw = bytes.fromhex(cleaned_hex.decode("ascii"))

        if b"FlateDecode" in hdr or b"/Fl" in hdr:
            try:
                raw = zlib.decompressobj().decompress(raw, MAX_RAW_TEXT_CHARS * 8)
            except zlib.error:
                raw = zlib.decompress(raw, -15)
        elif b"/Filter" in hdr:
            # Filtro binario no soportado: jamás devolver bytes comprimidos crudos
            return None
        return raw
    except Exception:
        return None


def _parse_tounicode_cmap(stream_bytes: bytes) -> dict[int, str]:
    """Extrae el mapa de glifos -> Unicode de un stream ``/ToUnicode``."""
    cmap: dict[int, str] = {}
    for block in _PDF_BFCHAR_BLOCK_RE.findall(stream_bytes):
        for src_hex, dst_hex in _PDF_BFCHAR_PAIR_RE.findall(block):
            try:
                val = bytes.fromhex(dst_hex.decode("ascii")).decode("utf-16-be", errors="ignore")
                if val and "\x00" not in val:
                    cmap[int(src_hex, 16)] = val
            except ValueError:
                continue

    for block in _PDF_BFRANGE_BLOCK_RE.findall(stream_bytes):
        for start_hex, end_hex, arr_body in _PDF_BFRANGE_ARRAY_RE.findall(block):
            start_code = int(start_hex, 16)
            end_code = int(end_hex, 16)
            targets = re.findall(rb"<([0-9A-Fa-f]+)>", arr_body)
            for offset, target_hex in enumerate(targets):
                if start_code + offset > end_code:
                    break
                try:
                    val = bytes.fromhex(target_hex.decode("ascii")).decode(
                        "utf-16-be", errors="ignore"
                    )
                    if val and "\x00" not in val:
                        cmap[start_code + offset] = val
                except ValueError:
                    continue

        cleaned_block = _PDF_BFRANGE_ARRAY_RE.sub(b"", block)
        for start_hex, end_hex, dst_hex in _PDF_BFRANGE_SIMPLE_RE.findall(cleaned_block):
            start_code = int(start_hex, 16)
            end_code = int(end_hex, 16)
            if end_code - start_code > 1024:
                continue
            try:
                base_val = bytes.fromhex(dst_hex.decode("ascii")).decode(
                    "utf-16-be", errors="ignore"
                )
                if len(base_val) == 1:
                    base_cp = ord(base_val)
                    for offset in range(end_code - start_code + 1):
                        cmap[start_code + offset] = chr(base_cp + offset)
            except ValueError:
                continue
    return cmap


def _clean_extracted_pdf_lines(raw_text: str) -> str:
    """Elimina cualquier residuo de sintaxis PDF o metadatos de navegador."""
    normalized = unicodedata.normalize("NFKC", raw_text)
    clean_lines: list[str] = []
    for line in normalized.splitlines():
        stripped = " ".join(line.split())
        if not stripped:
            continue
        if _PDF_NOISE_LINE_RE.search(stripped):
            continue
        # Ignorar líneas compuestas sólo por operadores gráficos PDF
        if re.fullmatch(r"[0-9.\-\s]+(?:cm|re|rg|RG|w|J|j|M|d|q|Q|f\*?|S|s|n|W\*?)", stripped):
            continue
        clean_lines.append(stripped)
    return "\n".join(clean_lines).strip()


def _extract_pdf_text_from_buffer(buf: bytes) -> str:
    """Extrae texto humano limpio de un PDF en RAM sin volcar jamás ``%PDF-1.4`` ni ``obj``."""
    if not buf.startswith(b"%PDF-"):
        raise AttachmentValidationError("Encabezado PDF inválido.")

    objs = dict(_PDF_OBJ_RE.findall(buf))
    decompressed_streams: dict[bytes, bytes] = {}
    cmaps_by_obj: dict[bytes, dict[int, str]] = {}
    global_cmap: dict[int, str] = {}

    for oid, body in objs.items():
        st = _decompress_pdf_obj_stream(body)
        if st is None:
            continue
        decompressed_streams[oid] = st
        if b"beginbfchar" in st or b"beginbfrange" in st:
            cmap = _parse_tounicode_cmap(st)
            if cmap:
                cmaps_by_obj[oid] = cmap
                global_cmap.update(cmap)

    font_to_cmap: dict[bytes, dict[int, str]] = {}
    for oid, body in objs.items():
        m = _PDF_TOUNICODE_REF_RE.search(body)
        if m and m.group(1) in cmaps_by_obj:
            font_to_cmap[oid] = cmaps_by_obj[m.group(1)]

    name_to_cmap: dict[str, dict[int, str]] = {}
    for body in objs.values():
        for fname, fobj in _PDF_FONT_RES_RE.findall(body):
            if fobj in font_to_cmap:
                name_to_cmap[fname.decode("latin-1")] = font_to_cmap[fobj]

    fragments: list[str] = []

    def _extract_from_content_stream(st: bytes) -> None:
        if b"BT" not in st or b"beginbfchar" in st or b"beginbfrange" in st:
            return
        active_cmap: dict[int, str] = {}
        for tok in _PDF_BT_TOKEN_RE.finditer(st):
            if tok.group(1) is not None:
                fname = tok.group(1).decode("latin-1", errors="ignore")
                active_cmap = name_to_cmap.get(fname, global_cmap)
            elif tok.group(2) is not None:
                piece = _decode_pdf_literal(tok.group(2), active_cmap or global_cmap)
                if piece:
                    fragments.append(piece)
            elif tok.group(3) is not None:
                piece = _decode_pdf_hex_string(tok.group(3), active_cmap, global_cmap)
                if piece:
                    fragments.append(piece)
            elif tok.group(4) is not None:
                fragments.append("\n")

    if decompressed_streams:
        for oid in sorted(decompressed_streams, key=lambda x: int(x)):
            _extract_from_content_stream(decompressed_streams[oid])
    else:
        for stream_match in _PDF_STREAM_RE.finditer(buf):
            raw_stream = stream_match.group(1)
            try:
                dec = zlib.decompressobj().decompress(raw_stream, MAX_RAW_TEXT_CHARS * 4)
            except zlib.error:
                dec = raw_stream
            _extract_from_content_stream(dec)

    cleaned = _clean_extracted_pdf_lines("".join(fragments))
    if not cleaned:
        raise AttachmentValidationError(
            "El archivo PDF no contiene texto extraíble o está escaneado como imagen."
        )
    return cleaned[:MAX_REDUCED_DOC_CHARS]


def _shield_fragment(
    fragment: str, state: _StreamShieldState, *, preserve_existing_tokens: bool = False
) -> str:
    """Aplica SHIELD al vuelo sobre un fragmento compartiendo el estado de tokens del stream."""
    if not fragment:
        return ""
    bounded = fragment[: MAX_RAW_TEXT_CHARS // 2]
    try:
        normalized = normalize_text(bounded)
    except ValueError:
        raise ShieldResidualPiiError("Fragmento no anonimizable de forma segura.") from None

    text = (
        normalized
        if preserve_existing_tokens
        else _TOKEN_LITERAL_RE.sub(lambda m: "［" + m.group(0)[1:], normalized)
    )
    matches = find_pii(text)
    remaining = len(_TOKEN_LITERAL_RE.sub("", text))
    for _ in range(MAX_PASSES):
        if not matches:
            break
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
        text = "".join(parts)

        next_remaining = len(_TOKEN_LITERAL_RE.sub("", text))
        if next_remaining >= remaining:
            raise ShieldResidualPiiError("Fragmento no anonimizable de forma segura.")
        remaining = next_remaining
        matches = find_pii(text, regions=_token_windows(text))

    if matches:
        raise ShieldResidualPiiError("PII residual tras el máximo de pasadas.")

    return text


def _map_distill_masked_chunk(
    masked_chunk: str,
    *,
    prompt_keywords: set[str],
    chunk_index: int,
) -> str:
    """Fase MAP en RAM: destila las líneas relevantes y con tokens PII de cada fragmento."""
    lines = [ln.strip() for ln in masked_chunk.splitlines() if ln.strip()]
    if not lines:
        return ""

    selected: list[str] = []
    for line in lines:
        lower = line.lower()
        has_token = bool(_TOKEN_LITERAL_RE.search(line))
        has_kw = any(kw in lower for kw in _DOMAIN_KEYWORDS) or any(
            pk in lower for pk in prompt_keywords
        )
        if has_token or has_kw or len(selected) < 4:
            compact_line = " ".join(line.split())[:200]
            if compact_line not in selected:
                selected.append(compact_line)
        if sum(len(s) for s in selected) >= MAX_MAP_FRAGMENT_CHARS:
            break

    if not selected:
        selected.append(" ".join(lines[0].split())[:200])

    joined = " | ".join(selected)
    return f"[Frag#{chunk_index}] {joined[:MAX_MAP_FRAGMENT_CHARS]}"


def _rolling_reduce_summaries(summaries: list[str]) -> list[str]:
    """Fase REDUCE jerárquica en RAM."""
    if len(summaries) <= ROLLING_REDUCE_BATCH // 2:
        return summaries

    reduced: list[str] = []
    for idx in range(0, len(summaries), 2):
        pair = summaries[idx : idx + 2]
        merged = " // ".join(pair)
        if len(merged) > MAX_MAP_FRAGMENT_CHARS:
            merged = merged[:MAX_MAP_FRAGMENT_CHARS]
        reduced.append(merged)
    return reduced


def _format_history_block(
    history_turns: Sequence[tuple[str, str]],
    state: _StreamShieldState,
) -> str:
    """Sanitiza y acota los turnos previos de la sesión en RAM (últimos 6 turnos)."""
    if not history_turns:
        return ""
    recent = list(history_turns)[-6:]
    formatted: list[str] = []
    for role, text in recent:
        clean_turn = _shield_fragment(text.strip()[:400], state, preserve_existing_tokens=True)
        if clean_turn:
            label = "Funcionario" if role == "user" else "AuditorIA"
            formatted.append(f"- {label}: {clean_turn}")
    if not formatted:
        return ""
    return "[HISTORIAL_SESION_RAM]:\n" + "\n".join(formatted)


def _build_ui_preview(
    masked_user_prompt: str,
    *,
    sanitized_name: str | None,
    first_summary: str | None,
    has_active_doc: bool,
) -> str:
    """Construye un resumen corto y limpio para el recuadro Perímetro SHIELD del frontend."""
    prompt_short = " ".join(masked_user_prompt.split())
    if len(prompt_short) > 120:
        prompt_short = prompt_short[:117] + "..."
    if sanitized_name and first_summary:
        snippet = " ".join(first_summary.split())
        if len(snippet) > 140:
            snippet = snippet[:137] + "..."
        return f"{prompt_short}\n[Adjunto {sanitized_name}]: {snippet}"[:MAX_UI_PREVIEW_CHARS]
    if has_active_doc:
        return f"{prompt_short} (Contexto documental activo en RAM)"[:MAX_UI_PREVIEW_CHARS]
    return prompt_short[:MAX_UI_PREVIEW_CHARS]


async def _slice_async_stream(
    stream: AsyncIterable[bytes], chunk_size: int = STREAM_CHUNK_SIZE
) -> AsyncIterable[bytes]:
    """Garantiza fragmentos de a lo sumo ``chunk_size`` (64 KB) en el stream."""
    async for raw_chunk in stream:
        if not raw_chunk:
            continue
        if len(raw_chunk) <= chunk_size:
            yield raw_chunk
        else:
            mv = memoryview(raw_chunk)
            for offset in range(0, len(mv), chunk_size):
                yield bytes(mv[offset : offset + chunk_size])


async def process_attachment_stream(
    stream: AsyncIterable[bytes],
    *,
    request_id: str,
    prompt: str,
    file_name: str,
    file_mime_type: str,
    vault: EphemeralVault,
    blind_citizen_id: str,
    history_turns: Sequence[tuple[str, str]] = (),
) -> StreamedChatPrepared:
    """Procesa un stream de hasta 100 MB en fragmentos de 64 KB sin tocar disco."""
    started = time.perf_counter()
    sanitized_name, clean_mime, ext = sanitize_attachment_filename(file_name, file_mime_type)
    effective_prompt = prompt.strip() or DEFAULT_ATTACHMENT_PROMPT
    hasher = hashlib.sha256()
    state = _StreamShieldState()
    prompt_keywords = {
        w.lower() for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]{4,}", effective_prompt)
    }

    masked_history = _format_history_block(history_turns, state)
    masked_user_prompt = _shield_fragment(effective_prompt, state)

    total_bytes = 0
    chunks_processed = 0
    carry_bytes = bytearray()
    pdf_buf = bytearray()
    map_summaries: list[str] = []
    completed_ok = False

    try:
        async for raw_chunk in _slice_async_stream(stream, STREAM_CHUNK_SIZE):
            chunk_buf = bytearray(raw_chunk)
            try:
                total_bytes += len(chunk_buf)
                if total_bytes > MAX_CHAT_ATTACHMENT_BYTES:
                    raise AttachmentValidationError(
                        "Archivo adjunto supera el límite soberano de 100 MB."
                    )

                hasher.update(chunk_buf)
                chunks_processed += 1

                if ext == ".pdf":
                    if len(pdf_buf) < MAX_PDF_RAM_BUFFER:
                        take = min(len(chunk_buf), MAX_PDF_RAM_BUFFER - len(pdf_buf))
                        pdf_buf.extend(chunk_buf[:take])
                    continue

                if b"\x00" in chunk_buf:
                    raise AttachmentValidationError(
                        "Archivo de texto contiene bytes nulos binarios."
                    )

                window_bytes = carry_bytes + chunk_buf
                carry_bytes.clear()

                if len(window_bytes) >= 128:
                    split_pos = max(window_bytes.rfind(b"\n"), window_bytes.rfind(b" "))
                    if split_pos != -1 and (len(window_bytes) - split_pos) <= 64:
                        carry_bytes.extend(window_bytes[split_pos:])
                        del window_bytes[split_pos:]

                try:
                    chunk_text = unicodedata.normalize(
                        "NFKC", bytes(window_bytes).decode("utf-8")
                    )
                except UnicodeDecodeError:
                    chunk_text = unicodedata.normalize(
                        "NFKC", bytes(window_bytes).decode("latin-1")
                    )
                finally:
                    window_bytes[:] = bytes(len(window_bytes))

                masked_chunk = _shield_fragment(chunk_text, state)
                if masked_chunk:
                    distilled = _map_distill_masked_chunk(
                        masked_chunk,
                        prompt_keywords=prompt_keywords,
                        chunk_index=chunks_processed,
                    )
                    if distilled:
                        map_summaries.append(distilled)
                        if len(map_summaries) >= ROLLING_REDUCE_BATCH:
                            map_summaries = _rolling_reduce_summaries(map_summaries)
            finally:
                chunk_buf[:] = bytes(len(chunk_buf))
            await asyncio.sleep(0)

        if total_bytes == 0:
            raise AttachmentValidationError("Archivo adjunto vacío.")

        if ext == ".pdf":
            extracted_pdf = _extract_pdf_text_from_buffer(bytes(pdf_buf))
            masked_pdf = _shield_fragment(extracted_pdf, state)
            for idx, offset in enumerate(range(0, len(masked_pdf), 1200), start=1):
                slice_pdf = masked_pdf[offset : offset + 1200]
                distilled = _map_distill_masked_chunk(
                    slice_pdf,
                    prompt_keywords=prompt_keywords,
                    chunk_index=idx,
                )
                if distilled:
                    map_summaries.append(distilled)
        elif carry_bytes:
            try:
                tail_text = unicodedata.normalize("NFKC", bytes(carry_bytes).decode("utf-8"))
            except UnicodeDecodeError:
                tail_text = unicodedata.normalize("NFKC", bytes(carry_bytes).decode("latin-1"))
            masked_tail = _shield_fragment(tail_text, state)
            if masked_tail:
                distilled = _map_distill_masked_chunk(
                    masked_tail,
                    prompt_keywords=prompt_keywords,
                    chunk_index=chunks_processed,
                )
                if distilled:
                    map_summaries.append(distilled)

        if not map_summaries:
            raise AttachmentValidationError("El archivo adjunto no contiene texto válido.")

        vault.put(request_id, state.token_map)

        sha_hex = hasher.hexdigest()
        tokens_found = list(state.token_map.keys())[:10]
        tokens_header = ", ".join(tokens_found) if tokens_found else "ninguno"
        joined_reduce = "\n".join(map_summaries)[:MAX_REDUCED_DOC_CHARS]
        doc_ctx = (
            f"[DOCUMENTO_SESION nombre={sanitized_name} sha256={sha_hex[:16]} "
            f"tokens_pii={tokens_header}]:\n{joined_reduce[:MAX_DOC_CONTEXT_CHARS]}"
        )

        sections: list[str] = []
        if masked_history:
            sections.append(masked_history)
        sections.append(f"[INSTRUCCION_FUNCIONARIO]: {masked_user_prompt}")
        sections.append(
            f"[DOCUMENTO_STREAM_MAP_REDUCE nombre={sanitized_name} "
            f"sha256={sha_hex[:16]} bytes={total_bytes} "
            f"fragmentos={chunks_processed} tokens_pii={tokens_header}]:\n"
            f"{joined_reduce}"
        )
        reduced_masked_text = "\n\n".join(sections)[:MAX_RAW_TEXT_CHARS]
        ui_preview = _build_ui_preview(
            masked_user_prompt,
            sanitized_name=sanitized_name,
            first_summary=map_summaries[0] if map_summaries else None,
            has_active_doc=True,
        )

        rif_verified = all(state.rif_results) if state.rif_results else None
        meta = ShieldMeta(
            blind_citizen_id=blind_citizen_id,
            pii_count=state.occurrences,
            detected_types=tuple(sorted(state.kinds)),
            rif_mod11_verified=rif_verified,
            validation_passed=rif_verified is not False,
            latency_ms=(time.perf_counter() - started) * 1000.0,
        )
        completed_ok = True
        return StreamedChatPrepared(
            sanitized_name=sanitized_name,
            mime_type=clean_mime,
            size_bytes=total_bytes,
            sha256_hex=sha_hex,
            chunks_processed=chunks_processed,
            reduced_masked_text=reduced_masked_text,
            ui_masked_preview=ui_preview,
            document_context_masked=doc_ctx,
            shield_meta=meta,
        )
    finally:
        carry_bytes[:] = bytes(len(carry_bytes))
        pdf_buf[:] = bytes(len(pdf_buf))
        if not completed_ok:
            vault.zeroize(request_id)


def prepare_text_only_chat(
    *,
    request_id: str,
    prompt: str,
    vault: EphemeralVault,
    blind_citizen_id: str,
    history_turns: Sequence[tuple[str, str]] = (),
    active_document_context: str | None = None,
    active_document_name: str | None = None,
    active_document_sha256: str | None = None,
) -> StreamedChatPrepared:
    """Prepara Caso A (solo texto + historial/documento en RAM) pasando todo por SHIELD."""
    started = time.perf_counter()
    clean_prompt = prompt.strip()
    if not clean_prompt:
        raise AttachmentValidationError("Debe ingresar una consulta o adjuntar un documento.")

    state = _StreamShieldState()
    masked_history = _format_history_block(history_turns, state)
    masked_doc_ctx = (
        _shield_fragment(
            active_document_context.strip()[:MAX_DOC_CONTEXT_CHARS],
            state,
            preserve_existing_tokens=True,
        )
        if active_document_context and active_document_context.strip()
        else ""
    )
    masked_user_prompt = _shield_fragment(clean_prompt, state)
    vault.put(request_id, state.token_map)

    sections: list[str] = []
    if masked_doc_ctx:
        sections.append(masked_doc_ctx)
    if masked_history:
        sections.append(masked_history)
    sections.append(f"[INSTRUCCION_FUNCIONARIO]: {masked_user_prompt}")

    reduced_masked = "\n\n".join(sections)[:MAX_RAW_TEXT_CHARS]
    ui_preview = _build_ui_preview(
        masked_user_prompt,
        sanitized_name=active_document_name,
        first_summary=None,
        has_active_doc=bool(masked_doc_ctx),
    )

    rif_verified = all(state.rif_results) if state.rif_results else None
    meta = ShieldMeta(
        blind_citizen_id=blind_citizen_id,
        pii_count=state.occurrences,
        detected_types=tuple(sorted(state.kinds)),
        rif_mod11_verified=rif_verified,
        validation_passed=rif_verified is not False,
        latency_ms=(time.perf_counter() - started) * 1000.0,
    )
    return StreamedChatPrepared(
        sanitized_name=active_document_name,
        mime_type=None,
        size_bytes=0,
        sha256_hex=active_document_sha256,
        chunks_processed=0,
        reduced_masked_text=reduced_masked,
        ui_masked_preview=ui_preview,
        document_context_masked=masked_doc_ctx or None,
        shield_meta=meta,
    )


async def iter_bytes_in_chunks(
    data: bytes | bytearray, chunk_size: int = STREAM_CHUNK_SIZE
) -> AsyncIterable[bytes]:
    """Generador asíncrono que emite un buffer en fragmentos de 64 KB."""
    total = len(data)
    for offset in range(0, total, chunk_size):
        yield bytes(data[offset : offset + chunk_size])


async def iter_b64_in_chunks(
    b64_text: str, chunk_size: int = STREAM_CHUNK_SIZE
) -> AsyncIterable[bytes]:
    """Decodifica Base64 por múltiplos de 4 caracteres sin materializar 100 MB de golpe."""
    stripped = b64_text.strip()
    if "," in stripped and stripped.lower().startswith("data:"):
        stripped = stripped.split(",", 1)[1].strip()
    compact = "".join(stripped.split())
    if not compact:
        raise AttachmentValidationError("Contenido Base64 vacío.")

    step = max(4, (chunk_size // 3) * 4)
    total = len(compact)
    for offset in range(0, total, step):
        slice_str = compact[offset : offset + step]
        try:
            decoded = base64.b64decode(slice_str, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise AttachmentValidationError("Contenido Base64 del adjunto inválido.") from exc
        yield decoded


def extract_attachment_from_bytes(
    raw_bytes: bytes | bytearray,
    *,
    file_name: str,
    file_mime_type: str,
) -> ExtractedAttachment:
    """Compatibilidad síncrona para adjuntos en memoria."""
    if not raw_bytes:
        raise AttachmentValidationError("Archivo adjunto vacío.")
    if len(raw_bytes) > MAX_CHAT_ATTACHMENT_BYTES:
        raise AttachmentValidationError("Archivo adjunto supera el límite de 100 MB.")

    sanitized_name, clean_mime, ext = sanitize_attachment_filename(file_name, file_mime_type)
    mutable_buf = bytearray(raw_bytes)
    try:
        digest = crypto.sha256_hex(bytes(mutable_buf))
        size_bytes = len(mutable_buf)
        chunks_cnt = max(1, (size_bytes + STREAM_CHUNK_SIZE - 1) // STREAM_CHUNK_SIZE)

        if ext == ".pdf":
            extracted = _extract_pdf_text_from_buffer(bytes(mutable_buf))
        else:
            if b"\x00" in mutable_buf:
                raise AttachmentValidationError("Archivo de texto contiene bytes nulos binarios.")
            try:
                extracted = unicodedata.normalize("NFKC", bytes(mutable_buf).decode("utf-8"))
            except UnicodeDecodeError:
                extracted = unicodedata.normalize("NFKC", bytes(mutable_buf).decode("latin-1"))

        cleaned_text = extracted.strip()
        if not cleaned_text:
            raise AttachmentValidationError("El archivo adjunto no contiene texto válido.")
        if len(cleaned_text) > MAX_REDUCED_DOC_CHARS:
            cleaned_text = cleaned_text[:MAX_REDUCED_DOC_CHARS]

        return ExtractedAttachment(
            sanitized_name=sanitized_name,
            mime_type=clean_mime,
            size_bytes=size_bytes,
            sha256_hex=digest,
            extracted_text=cleaned_text,
            chunks_processed=chunks_cnt,
        )
    finally:
        mutable_buf[:] = bytes(len(mutable_buf))


def extract_attachment_from_b64(
    file_content_b64: str,
    *,
    file_name: str,
    file_mime_type: str,
) -> ExtractedAttachment:
    """Decodifica un adjunto Base64 en RAM, extrae su texto y destruye el buffer intermedio."""
    stripped = file_content_b64.strip()
    if "," in stripped and stripped.lower().startswith("data:"):
        stripped = stripped.split(",", 1)[1].strip()
    try:
        decoded = bytearray(base64.b64decode(stripped, validate=True))
    except (binascii.Error, ValueError) as exc:
        raise AttachmentValidationError("Contenido Base64 del adjunto inválido.") from exc

    try:
        return extract_attachment_from_bytes(
            decoded,
            file_name=file_name,
            file_mime_type=file_mime_type,
        )
    finally:
        decoded[:] = bytes(len(decoded))


def compose_gateway_raw_text(
    prompt: str,
    attachment: ExtractedAttachment | None,
    *,
    chunks_Streamed: Iterable[str] | None = None,
) -> str:
    """Combina el prompt del usuario y el contenido extraído del archivo para GatewayPipeline."""
    del chunks_Streamed
    clean_prompt = prompt.strip() or (DEFAULT_ATTACHMENT_PROMPT if attachment else "")
    if attachment is None:
        return clean_prompt
    combined = (
        f"{clean_prompt}\n"
        f"[DOCUMENTO_ADJUNTO nombre={attachment.sanitized_name} "
        f"sha256={attachment.sha256_hex[:16]}]:\n"
        f"{attachment.extracted_text}"
    )
    if len(combined) > MAX_RAW_TEXT_CHARS:
        return combined[:MAX_RAW_TEXT_CHARS]
    return combined


def derive_chat_features(
    masked_text: str,
    *,
    has_attachment: bool,
    pii_count: int,
    detected_types: tuple[str, ...],
) -> dict[str, float]:
    """Deriva de forma 100% determinista las 5 variables del modelo institucional EXPLICA."""
    lower = masked_text.lower()
    has_medical = "CLINICAL" in detected_types or any(
        kw in lower
        for kw in ("salud", "clínic", "clinic", "médic", "medic", "patolog", "hospital", "cirug")
    )
    has_social = any(
        kw in lower
        for kw in ("beca", "apoyo", "vulnerab", "exoneraci", "subsidio", "ayuda", "arancel")
    )

    completitud = (
        0.95 if (has_attachment and pii_count >= 1) else (0.85 if has_attachment else 0.75)
    )
    urgencia = 0.90 if has_medical else 0.30
    vulnerabilidad = 0.85 if (has_social or has_medical) else 0.55
    tiempo_espera = float(min(120, max(20, 35 + (len(masked_text) // 20))))
    complejidad = 0.35 if has_attachment else 0.50

    return {
        "tiempo_espera_dias": tiempo_espera,
        "vulnerabilidad_socioeconomica": vulnerabilidad,
        "completitud_recaudos": completitud,
        "urgencia_medica": urgencia,
        "complejidad_caso": complejidad,
    }
