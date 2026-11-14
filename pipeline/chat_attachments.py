"""Extracción efímera en RAM y validación Zero-Trust de adjuntos para Chat IA.

Reglas SDD:
- Cero escritura en disco: el archivo se procesa en memoria y su buffer ``bytearray``
  se sobrescribe con ``0x00`` en el bloque ``finally``.
- Validación estricta de tamaño, tipo MIME, extensión y sanitización de nombre.
- Derivación 100% determinista de características para ``stage5_explica.py`` (cero ``random()``).
"""

from __future__ import annotations

import base64
import binascii
import re
import zlib
from dataclasses import dataclass
from pathlib import PurePath
from typing import Final

from core import crypto
from core.config import MAX_RAW_TEXT_CHARS
from core.errors import AttachmentValidationError

MAX_CHAT_ATTACHMENT_BYTES: Final[int] = 32 * 1024
MAX_FILENAME_CHARS: Final[int] = 80

ALLOWED_EXTENSIONS: Final[dict[str, frozenset[str]]] = {
    ".txt": frozenset({"text/plain", "application/octet-stream"}),
    ".md": frozenset({"text/plain", "text/markdown", "application/octet-stream"}),
    ".csv": frozenset(
        {"text/csv", "application/csv", "text/plain", "application/vnd.ms-excel"}
    ),
    ".json": frozenset({"application/json", "text/plain"}),
    ".pdf": frozenset({"application/pdf", "application/x-pdf"}),
}

_SAFE_FILENAME_RE: Final = re.compile(r"[^A-Za-z0-9._-]+")
_PDF_STREAM_RE: Final = re.compile(rb"stream[\r\n]+(.*?)[\r\n]+endstream", re.DOTALL)
_PDF_LITERAL_STR_RE: Final = re.compile(rb"\(([^()\\]*(?:\\.[^()\\]*)*)\)")
_PDF_HEX_STR_RE: Final = re.compile(rb"<([0-9A-Fa-f]{4,})>")


@dataclass(frozen=True, slots=True)
class ExtractedAttachment:
    sanitized_name: str
    mime_type: str
    size_bytes: int
    sha256_hex: str
    extracted_text: str

    def __repr__(self) -> str:  # Zero-Leak
        return "[REDACTED_CHAT_PAYLOAD]"


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
        if ch == 0x5C and i + 1 < n:  # backslash
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
    """Extrae texto legible de un PDF en memoria sin escribir en disco (stdlib pura)."""
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


def extract_attachment_from_bytes(
    raw_bytes: bytes | bytearray,
    *,
    file_name: str,
    file_mime_type: str,
) -> ExtractedAttachment:
    """Valida, hashea y extrae texto de un archivo en RAM, limpiando el buffer temporal."""
    if not raw_bytes:
        raise AttachmentValidationError("Archivo adjunto vacío.")
    if len(raw_bytes) > MAX_CHAT_ATTACHMENT_BYTES:
        raise AttachmentValidationError("Archivo adjunto supera el límite de 32 KB.")

    sanitized_name, clean_mime, ext = sanitize_attachment_filename(file_name, file_mime_type)
    mutable_buf = bytearray(raw_bytes)
    try:
        digest = crypto.sha256_hex(bytes(mutable_buf))
        size_bytes = len(mutable_buf)

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
        if len(cleaned_text) > MAX_RAW_TEXT_CHARS // 2:
            cleaned_text = cleaned_text[: MAX_RAW_TEXT_CHARS // 2]

        return ExtractedAttachment(
            sanitized_name=sanitized_name,
            mime_type=clean_mime,
            size_bytes=size_bytes,
            sha256_hex=digest,
            extracted_text=cleaned_text,
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


def compose_gateway_raw_text(prompt: str, attachment: ExtractedAttachment | None) -> str:
    """Combina el prompt del usuario y el contenido extraído del archivo para GatewayPipeline."""
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
