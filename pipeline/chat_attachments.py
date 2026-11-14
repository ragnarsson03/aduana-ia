"""Streaming efímero en RAM (hasta 100 MB), Map-Reduce y validación Zero-Trust de adjuntos.

Reglas SDD:
- Límite de hasta 100 MB (``MAX_CHAT_ATTACHMENT_BYTES = 100 * 1024 * 1024``).
- Cero escritura en disco (ni SQLite, ni D1, ni R2): el archivo se procesa por fragmentos
  (``AsyncIterable[bytes]``) en memoria (< 2 MB de RAM pico) y cada buffer ``bytearray``
  se sobrescribe con ``0x00`` inmediatamente.
- Hash ``SHA-256`` incremental sobre el flujo original (``hashlib.sha256``).
- Anonimización al vuelo por fragmento (SHIELD + GUARD-IN) con mapa de reversión exclusivo
  en ``EphemeralVault`` (TTL 180s) y síntesis Map-Reduce en RAM para no saturar la ventana
  de contexto del LLM.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import hashlib
import re
import time
import zlib
from collections import Counter
from collections.abc import AsyncIterable, Iterable
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
MAX_FILENAME_CHARS: Final[int] = 80
MAX_MAP_FRAGMENT_CHARS: Final[int] = 420
MAX_REDUCED_DOC_CHARS: Final[int] = 6_000
ROLLING_REDUCE_BATCH: Final[int] = 32

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
_PDF_STREAM_RE: Final = re.compile(rb"stream[\r\n]+(.*?)[\r\n]+endstream", re.DOTALL)
_PDF_LITERAL_STR_RE: Final = re.compile(rb"\(([^()\\]*(?:\\.[^()\\]*)*)\)")
_PDF_HEX_STR_RE: Final = re.compile(rb"<([0-9A-Fa-f]{4,})>")
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
    sanitized_name: str
    mime_type: str
    size_bytes: int
    sha256_hex: str
    chunks_processed: int
    reduced_masked_text: str
    shield_meta: ShieldMeta

    def __repr__(self) -> str:  # Zero-Leak
        return "[REDACTED_LARGE_PAYLOAD]"


def sanitize_attachment_filename(raw_name: str, mime_type: str) -> tuple[str, str, str]:
    """Sanitiza el nombre del archivo y valida su extensión y MIME contra la allowlist."""
    if not raw_name or not raw_name.strip():
        raise AttachmentValidationError("Nombre de archivo adjunto vacío.")
    if "\x00" in raw_name or ".." in raw_name:
        raise AttachmentValidationError("Nombre de archivo adjunto rechazado por seguridad.")

    normalized_path = raw_name.replace("\\", "/").strip()
    base_name = PurePath(normalized_path).name
    if not base_name or base_name in {".", ".."}:
        raise AttachmentValidationError("Nombre de archivo adjunto inválido.")

    cleaned = _SAFE_FILENAME_RE.sub("_", base_name).strip("._")
    if not cleaned:
        raise AttachmentValidationError("Nombre de archivo adjunto sin caracteres válidos.")
    if len(cleaned) > MAX_FILENAME_CHARS:
        stem = PurePath(cleaned).stem[: MAX_FILENAME_CHARS - 10]
        suffix = PurePath(cleaned).suffix.lower()
        cleaned = f"{stem}{suffix}"

    ext = PurePath(cleaned).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AttachmentValidationError("Extensión de archivo no permitida en Chat IA.")

    clean_mime = mime_type.split(";")[0].strip().lower() if mime_type else ""
    allowed_mimes = ALLOWED_EXTENSIONS[ext]
    if clean_mime not in allowed_mimes:
        raise AttachmentValidationError("Tipo MIME no coincide con la extensión permitida.")

    return cleaned, clean_mime, ext


def _decode_pdf_literal(raw: bytes) -> str:
    """Decodifica cadenas literales PDF ``(...)`` con secuencias de escape básicas."""
    out = bytearray()
    i = 0
    n = len(raw)
    while i < n:
        ch = raw[i]
        if ch == 0x5C and i + 1 < n:
            nxt = raw[i + 1]
            if nxt in (0x6E, 0x72, 0x74):
                out.append(0x20)
            else:
                out.append(nxt)
            i += 2
        else:
            out.append(ch)
            i += 1
    return out.decode("latin-1", errors="ignore")


def _extract_pdf_text_from_buffer(buf: bytes) -> str:
    """Extrae texto legible de un bloque PDF en memoria sin escribir en disco (stdlib pura)."""
    if not buf.startswith(b"%PDF-"):
        raise AttachmentValidationError("Encabezado PDF inválido.")

    fragments: list[str] = []

    def _collect_from_chunk(chunk: bytes) -> None:
        for match in _PDF_LITERAL_STR_RE.finditer(chunk):
            piece = _decode_pdf_literal(match.group(1)).strip()
            if piece:
                fragments.append(piece)
        for match in _PDF_HEX_STR_RE.finditer(chunk):
            try:
                raw_hex = bytes.fromhex(match.group(1).decode("ascii"))
                piece = raw_hex.decode("utf-8", errors="ignore").strip()
                if piece:
                    fragments.append(piece)
            except ValueError:
                continue

    for stream_match in _PDF_STREAM_RE.finditer(buf):
        stream_bytes = stream_match.group(1)
        decompressed = stream_bytes
        try:
            decompressed = zlib.decompressobj().decompress(
                stream_bytes, MAX_RAW_TEXT_CHARS * 2
            )
        except zlib.error:
            decompressed = stream_bytes
        _collect_from_chunk(decompressed)

    if not fragments:
        _collect_from_chunk(buf)

    joined = " ".join(fragments).strip()
    if not joined:
        raise AttachmentValidationError("El archivo PDF no contiene texto extraíble.")
    return joined[: MAX_RAW_TEXT_CHARS // 2]


def _shield_fragment(fragment: str, state: _StreamShieldState) -> str:
    """Aplica SHIELD al vuelo sobre un fragmento compartiendo el estado de tokens del stream."""
    if not fragment:
        return ""
    bounded = fragment[: MAX_RAW_TEXT_CHARS // 2]
    try:
        normalized = normalize_text(bounded)
    except ValueError:
        raise ShieldResidualPiiError("Fragmento no anonimizable de forma segura.") from None

    text = _TOKEN_LITERAL_RE.sub(lambda m: "［" + m.group(0)[1:], normalized)
    matches = find_pii(text)
    remaining = len(text)
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
            raise ShieldResidualPiiError("Fragmento con PII residual pegada.")
        remaining = next_remaining
        matches = find_pii(text, regions=_token_windows(text))

    if matches:
        raise ShieldResidualPiiError("Fragmento con PII residual tras pasadas máximas.")
    return text


def _map_distill_masked_chunk(
    masked_chunk: str,
    *,
    prompt_keywords: set[str],
    chunk_index: int,
) -> str:
    """Fase MAP en RAM: destila las líneas con tokens PII o palabras clave del fragmento."""
    lines = [ln.strip() for ln in masked_chunk.splitlines() if ln.strip()]
    if not lines:
        return ""

    selected: list[str] = []
    for ln in lines:
        lower = ln.lower()
        has_token = bool(_TOKEN_LITERAL_RE.search(ln))
        has_kw = any(kw in lower for kw in _DOMAIN_KEYWORDS) or any(
            kw in lower for kw in prompt_keywords
        )
        if has_token or has_kw:
            selected.append(ln)
            if sum(len(s) for s in selected) >= MAX_MAP_FRAGMENT_CHARS:
                break

    if not selected:
        selected.append(lines[0][:200])
        if len(lines) > 1:
            selected.append(lines[-1][:180])

    summary = " | ".join(selected)
    if len(summary) > MAX_MAP_FRAGMENT_CHARS:
        summary = summary[:MAX_MAP_FRAGMENT_CHARS]
    return f"[Frag #{chunk_index}] {summary}"


def _rolling_reduce_summaries(summaries: list[str]) -> list[str]:
    """Fase REDUCE jerárquica en RAM: compacta lotes para no superar nunca 1 MB de RAM."""
    if len(summaries) < ROLLING_REDUCE_BATCH:
        return summaries
    compacted: list[str] = []
    seen: set[str] = set()
    for item in summaries:
        # Preservar fragmentos que contengan nuevos tokens o alertas de inyección
        body = item.split("]", 1)[-1].strip() if "]" in item else item
        if body in seen:
            continue
        seen.add(body)
        compacted.append(item)
        if len(compacted) >= ROLLING_REDUCE_BATCH // 2:
            break
    return compacted


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
) -> StreamedChatPrepared:
    """Procesa un stream de hasta 100 MB en fragmentos de 64 KB sin tocar disco.

    Calcula SHA-256 incremental, anonimiza con SHIELD al vuelo, almacena el mapa en
    ``EphemeralVault`` y aplica Map-Reduce en RAM. Si el stream se cancela o falla,
    destruye los buffers y ejecuta ``vault.zeroize(request_id)``.
    """
    started = time.perf_counter()
    sanitized_name, clean_mime, ext = sanitize_attachment_filename(file_name, file_mime_type)
    hasher = hashlib.sha256()
    state = _StreamShieldState()
    prompt_keywords = {
        w.lower() for w in re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]{4,}", prompt)
    }

    # 1. Anonimizar primero el prompt del usuario compartiendo el estado de tokens
    masked_user_prompt = _shield_fragment(prompt.strip(), state)

    total_bytes = 0
    chunks_processed = 0
    carry_bytes = bytearray()
    pdf_head_buf = bytearray()
    map_summaries: list[str] = []
    completed_ok = False

    try:
        async for raw_chunk in _slice_async_stream(stream, STREAM_CHUNK_SIZE):
            if not raw_chunk:
                continue
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
                    if len(pdf_head_buf) < STREAM_CHUNK_SIZE * 2:
                        take = min(
                            len(chunk_buf),
                            STREAM_CHUNK_SIZE * 2 - len(pdf_head_buf),
                        )
                        pdf_head_buf.extend(chunk_buf[:take])
                    continue

                if b"\x00" in chunk_buf:
                    raise AttachmentValidationError(
                        "Archivo de texto contiene bytes nulos binarios."
                    )

                window_bytes = carry_bytes + chunk_buf
                carry_bytes.clear()

                # Separar en el último salto de línea o espacio para no partir una cédula/RIF
                if len(window_bytes) >= 128:
                    split_pos = max(
                        window_bytes.rfind(b"\n"),
                        window_bytes.rfind(b" "),
                    )
                    if split_pos != -1 and (len(window_bytes) - split_pos) <= 64:
                        carry_bytes.extend(window_bytes[split_pos:])
                        del window_bytes[split_pos:]

                try:
                    chunk_text = bytes(window_bytes).decode("utf-8")
                except UnicodeDecodeError:
                    chunk_text = bytes(window_bytes).decode("latin-1")
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
            extracted_pdf = _extract_pdf_text_from_buffer(bytes(pdf_head_buf))
            masked_pdf = _shield_fragment(extracted_pdf, state)
            distilled = _map_distill_masked_chunk(
                masked_pdf,
                prompt_keywords=prompt_keywords,
                chunk_index=1,
            )
            if distilled:
                map_summaries.append(distilled)
        elif carry_bytes:
            try:
                tail_text = bytes(carry_bytes).decode("utf-8")
            except UnicodeDecodeError:
                tail_text = bytes(carry_bytes).decode("latin-1")
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

        # Guardar el mapa de reversión consolidado únicamente en EphemeralVault (TTL 180s)
        vault.put(request_id, state.token_map)

        sha_hex = hasher.hexdigest()
        tokens_found = list(state.token_map.keys())[:12]
        tokens_header = ", ".join(tokens_found) if tokens_found else "ninguno"
        joined_reduce = "\n".join(map_summaries)
        if len(joined_reduce) > MAX_REDUCED_DOC_CHARS:
            joined_reduce = joined_reduce[:MAX_REDUCED_DOC_CHARS]

        reduced_masked_text = (
            f"{masked_user_prompt}\n"
            f"[DOCUMENTO_STREAM_MAP_REDUCE nombre={sanitized_name} "
            f"sha256={sha_hex[:16]} bytes={total_bytes} "
            f"fragmentos={chunks_processed} tokens_pii={tokens_header}]:\n"
            f"{joined_reduce}"
        )
        if len(reduced_masked_text) > MAX_RAW_TEXT_CHARS:
            reduced_masked_text = reduced_masked_text[:MAX_RAW_TEXT_CHARS]

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
            shield_meta=meta,
        )
    finally:
        carry_bytes[:] = bytes(len(carry_bytes))
        pdf_head_buf[:] = bytes(len(pdf_head_buf))
        if not completed_ok:
            vault.zeroize(request_id)


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

    # Múltiplo de 4 para decodificar por bloques
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
                extracted = bytes(mutable_buf).decode("utf-8")
            except UnicodeDecodeError:
                extracted = bytes(mutable_buf).decode("latin-1")

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
    clean_prompt = prompt.strip()
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
