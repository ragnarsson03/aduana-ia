"""Controlador Zero-Trust para el Chat de IA con streaming efímero de hasta 100 MB.

Cumple estrictamente:
- Streaming efímero (100 MB máx., 0 escritura en disco/SQLite/D1/R2) por fragmentos de 64 KB.
- Zero-Plaintext-PII: anonimización al vuelo (SHIELD + GUARD-IN) y síntesis Map-Reduce en RAM
  con mapa de reversión en ``EphemeralVault`` (TTL 180s) y ``EphemeralVault.zeroize()`` en
  ``finally``.
- Auditoría Ledger de rastro sin dato: en ``ledger_blocks`` sólo se sella el hash SHA-256 del
  archivo, ``blind_citizen_id``, ``user_role``, ``timestamp_utc`` y ``action``.
"""

from __future__ import annotations

import json
import secrets
import urllib.parse
import uuid
from collections.abc import AsyncIterable
from typing import Any, Final

import msgspec
from litestar import Controller, Request, post
from litestar.connection import ASGIConnection
from litestar.datastructures import UploadFile
from litestar.exceptions import HTTPException, NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler
from litestar.status_codes import HTTP_200_OK

from app.dependencies import AppState
from app.schemas import ChatIAResponse, ChatIAUploadRequest, UserRole
from app.security import TOKEN_HEADER
from core import crypto
from core.config import API_PREFIX
from core.context import BlockedPacket
from core.errors import AttachmentValidationError
from pipeline.chat_attachments import (
    MAX_CHAT_ATTACHMENT_BYTES,
    STREAM_CHUNK_SIZE,
    StreamedChatPrepared,
    derive_chat_features,
    iter_b64_in_chunks,
    process_attachment_stream,
)
from pipeline.orchestrator import GatewayInput

MAX_CHAT_REQUEST_BYTES: Final[int] = 105 * 1024 * 1024  # 105 MB para cubrir cabeceras/multipart
VALID_ROLES: Final[frozenset[str]] = frozenset({"analista", "administrador", "auditor"})


def chat_api_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    expected: str = connection.app.state.aduana.api_token
    supplied = connection.headers.get(TOKEN_HEADER, "")
    if not secrets.compare_digest(supplied.encode(), expected.encode()):
        raise NotAuthorizedException(detail="UNAUTHORIZED")
    if connection.scope["method"] in {"POST", "PUT", "PATCH"}:
        content_type = connection.headers.get("content-type", "").split(";")[0].strip().lower()
        if content_type not in {
            "application/json",
            "multipart/form-data",
            "application/octet-stream",
        }:
            raise HTTPException(status_code=415, detail="UNSUPPORTED_MEDIA_TYPE")


def _normalize_role(raw_role: str | None) -> UserRole:
    cleaned = (raw_role or "analista").strip().lower()
    if cleaned == "admin":
        return "administrador"
    if cleaned in VALID_ROLES:
        return cleaned  # type: ignore[return-value]
    return "analista"


async def _iter_upload_file(
    upload: UploadFile, chunk_size: int = STREAM_CHUNK_SIZE
) -> AsyncIterable[bytes]:
    """Itera un ``UploadFile`` en fragmentos de 64 KB sin cargar el archivo entero en RAM."""
    while True:
        chunk = await upload.read(chunk_size)
        if not chunk:
            break
        yield chunk


def _verify_client_sha256(computed_sha256: str, client_sha256: str | None) -> None:
    if not client_sha256:
        return
    clean_client = client_sha256.strip().lower()
    if not secrets.compare_digest(computed_sha256.lower().encode(), clean_client.encode()):
        raise AttachmentValidationError(
            "Integridad fallida: el SHA-256 del stream no coincide con el hash del cliente."
        )


async def _prepare_from_octet_stream(
    request: Request,
    state: AppState,
    request_id: str,
) -> tuple[ChatIAUploadRequest, StreamedChatPrepared]:
    """Procesa un stream binario directo (`application/octet-stream`) desde `request.stream()`."""
    raw_prompt = urllib.parse.unquote(request.headers.get("x-chat-prompt", "")).strip()
    if not raw_prompt:
        raw_prompt = "Analizar documento adjunto en flujo efímero."
    file_name = urllib.parse.unquote(request.headers.get("x-file-name", "adjunto.txt")).strip()
    file_mime = request.headers.get("x-file-mime", "text/plain").strip()
    cedula_val = request.headers.get("x-citizen-cedula", "V-12345678").strip()
    role_val = _normalize_role(request.headers.get("x-user-role"))
    action_val = (request.headers.get("x-audit-action") or "CHAT_IA_STREAM_UPLOAD").strip()
    purpose_val = (request.headers.get("x-purpose-code") or "CHAT_IA_CONSULTA").strip()
    consent_raw = (request.headers.get("x-consent-granted") or "true").strip().lower()
    consent_val = consent_raw not in {"false", "0", "no"}
    client_sha = request.headers.get("x-client-file-sha256") or None

    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit():
        if int(content_length) > MAX_CHAT_ATTACHMENT_BYTES:
            raise AttachmentValidationError(
                "Archivo adjunto supera el límite soberano de 100 MB."
            )

    try:
        dto = msgspec.convert(
            {
                "prompt": raw_prompt,
                "citizen_cedula": cedula_val,
                "user_role": role_val,
                "action": action_val,
                "purpose_code": purpose_val,
                "consent_granted": consent_val,
                "file_name": file_name,
                "file_mime_type": file_mime,
                "client_file_sha256": client_sha,
            },
            type=ChatIAUploadRequest,
        )
    except msgspec.ValidationError as exc:
        raise HTTPException(status_code=400, detail="INVALID_CHAT_PAYLOAD") from exc

    blind_id = crypto.blind_citizen_id(state.keys, dto.citizen_cedula)

    prepared = await process_attachment_stream(
        request.stream(),
        request_id=request_id,
        prompt=dto.prompt,
        file_name=file_name,
        file_mime_type=file_mime,
        vault=state.vault,
        blind_citizen_id=blind_id,
    )
    _verify_client_sha256(prepared.sha256_hex, dto.client_file_sha256)
    return dto, prepared


async def _prepare_chat_request(
    request: Request,
    state: AppState,
    request_id: str,
) -> tuple[ChatIAUploadRequest, StreamedChatPrepared | None]:
    """Decodifica y procesa en streaming la solicitud de Chat IA (binario, multipart o JSON)."""
    content_type = (request.headers.get("content-type") or "").lower()

    if content_type.startswith("application/octet-stream"):
        dto, prepared = await _prepare_from_octet_stream(request, state, request_id)
        return dto, prepared

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        prompt_val = str(form.get("prompt") or "").strip()
        cedula_val = str(form.get("citizen_cedula") or "V-12345678").strip()
        role_val = _normalize_role(
            str(form.get("user_role") or request.headers.get("x-user-role") or "analista")
        )
        action_val = str(form.get("action") or "CHAT_IA_STREAM_UPLOAD").strip()
        purpose_val = str(form.get("purpose_code") or "CHAT_IA_CONSULTA").strip()
        consent_raw = str(form.get("consent_granted") or "true").strip().lower()
        consent_val = consent_raw not in {"false", "0", "no"}
        client_sha_raw = form.get("client_file_sha256") or request.headers.get(
            "x-client-file-sha256"
        )
        client_sha = str(client_sha_raw).strip() if client_sha_raw else None

        features_val: dict[str, float] | None = None
        if "features" in form and form.get("features"):
            try:
                parsed_feat = json.loads(str(form.get("features")))
                if isinstance(parsed_feat, dict):
                    features_val = {str(k): float(v) for k, v in parsed_feat.items()}
            except (ValueError, TypeError) as exc:
                raise HTTPException(status_code=422, detail="ERR_INVALID_FEATURES") from exc

        human_decision_val: Any = form.get("human_decision") or None
        override_just_val: Any = form.get("override_justification") or None
        upload_obj = form.get("file")
        file_name: str | None = None
        file_mime: str | None = None
        file_b64: str | None = None

        if isinstance(upload_obj, UploadFile):
            file_name = upload_obj.filename or "adjunto.txt"
            file_mime = upload_obj.content_type or "text/plain"
        elif form.get("file_content_b64"):
            file_name = str(form.get("file_name") or "adjunto.txt")
            file_mime = str(form.get("file_mime_type") or "text/plain")
            file_b64 = str(form.get("file_content_b64"))

        raw_dict: dict[str, Any] = {
            "prompt": prompt_val,
            "citizen_cedula": cedula_val,
            "user_role": role_val,
            "action": action_val,
            "purpose_code": purpose_val,
            "consent_granted": consent_val,
            "file_name": file_name,
            "file_mime_type": file_mime,
            "file_content_b64": "streamed" if isinstance(upload_obj, UploadFile) else file_b64,
            "client_file_sha256": client_sha,
            "features": features_val,
            "human_decision": human_decision_val,
            "override_justification": override_just_val,
        }
        try:
            dto = msgspec.convert(raw_dict, type=ChatIAUploadRequest)
        except msgspec.ValidationError as exc:
            raise HTTPException(status_code=400, detail="INVALID_CHAT_PAYLOAD") from exc

        blind_id = crypto.blind_citizen_id(state.keys, dto.citizen_cedula)

        if isinstance(upload_obj, UploadFile):
            prepared = await process_attachment_stream(
                _iter_upload_file(upload_obj),
                request_id=request_id,
                prompt=dto.prompt,
                file_name=file_name or "adjunto.txt",
                file_mime_type=file_mime or "text/plain",
                vault=state.vault,
                blind_citizen_id=blind_id,
            )
            _verify_client_sha256(prepared.sha256_hex, dto.client_file_sha256)
            return dto, prepared

        if file_b64:
            prepared = await process_attachment_stream(
                iter_b64_in_chunks(file_b64),
                request_id=request_id,
                prompt=dto.prompt,
                file_name=file_name or "adjunto.txt",
                file_mime_type=file_mime or "text/plain",
                vault=state.vault,
                blind_citizen_id=blind_id,
            )
            _verify_client_sha256(prepared.sha256_hex, dto.client_file_sha256)
            return dto, prepared

        return dto, None

    raw_body = await request.body()
    try:
        dto = msgspec.json.decode(raw_body, type=ChatIAUploadRequest)
    except msgspec.ValidationError as exc:
        raise HTTPException(status_code=400, detail="INVALID_CHAT_PAYLOAD") from exc
    except msgspec.DecodeError as exc:
        raise HTTPException(status_code=400, detail="MALFORMED_JSON") from exc

    has_any_file_field = any(
        x is not None for x in (dto.file_name, dto.file_mime_type, dto.file_content_b64)
    )
    if not has_any_file_field:
        return dto, None

    if not (dto.file_name and dto.file_mime_type and dto.file_content_b64):
        raise AttachmentValidationError(
            "Adjunto incompleto: requiere file_name, file_mime_type y file_content_b64."
        )

    blind_id = crypto.blind_citizen_id(state.keys, dto.citizen_cedula)
    prepared = await process_attachment_stream(
        iter_b64_in_chunks(dto.file_content_b64),
        request_id=request_id,
        prompt=dto.prompt,
        file_name=dto.file_name,
        file_mime_type=dto.file_mime_type,
        vault=state.vault,
        blind_citizen_id=blind_id,
    )
    _verify_client_sha256(prepared.sha256_hex, dto.client_file_sha256)
    return dto, prepared


async def _execute_chat_pipeline(request: Request) -> ChatIAResponse:
    state: AppState = request.app.state.aduana
    request_id = str(uuid.uuid4())
    try:
        dto, prepared = await _prepare_chat_request(request, state, request_id)
        analysis_text = prepared.reduced_masked_text if prepared is not None else dto.prompt
        features = (
            dict(dto.features)
            if dto.features is not None
            else derive_chat_features(
                analysis_text,
                has_attachment=prepared is not None,
                pii_count=prepared.shield_meta.pii_count if prepared is not None else 0,
                detected_types=prepared.shield_meta.detected_types if prepared is not None else (),
            )
        )

        gateway_in = GatewayInput(
            raw_text=dto.prompt,
            citizen_cedula=dto.citizen_cedula,
            consent_granted=dto.consent_granted,
            purpose_code=dto.purpose_code,
            features=features,
            human_decision=dto.human_decision,
            override_justification=dto.override_justification,
            attachment_sha256=prepared.sha256_hex if prepared else "NONE",
            attachment_size_bytes=prepared.size_bytes if prepared else 0,
            user_role=dto.user_role,
            audit_action=dto.action,
            pre_shielded_text=prepared.reduced_masked_text if prepared else None,
            pre_shielded_meta=prepared.shield_meta if prepared else None,
            request_id_override=request_id,
        )

        packet = await state.pipeline.process(gateway_in)
    finally:
        # Destrucción criptográfica garantizada si ocurre error antes de entrar al pipeline
        state.vault.zeroize(request_id)

    if isinstance(packet, BlockedPacket):
        return ChatIAResponse(
            request_id=packet.request_id,
            timestamp_utc=packet.timestamp_utc,
            policy_status=packet.policy_status,
            masked_prompt=None,
            sanitized_response="",
            restored_response="",
            ai_generated_notice=False,
            pii_count=0,
            detected_types=(),
            rif_mod11_verified=None,
            file_name_sanitized=prepared.sanitized_name if prepared else None,
            file_sha256=prepared.sha256_hex if prepared else None,
            file_size_bytes=prepared.size_bytes if prepared else 0,
            model_recommendation="BLOQUEADO_SEGURIDAD",
            human_decision="BLOQUEADO_SEGURIDAD",
            human_override=False,
            probability_score=None,
            linear_shap_values=None,
            citizen_receipt_code=packet.ledger.citizen_receipt_code,
            block_index=packet.ledger.block_index,
            chain_verified=packet.ledger.chain_verified,
            latency_ms=0.0,
            chunks_processed=prepared.chunks_processed if prepared else 0,
            user_role=dto.user_role,
            audit_action=dto.action,
        )

    total_latency = (
        packet.shield.latency_ms
        + packet.guard_in.latency_ms
        + packet.llm.latency_ms
        + packet.guard_out.latency_ms
    )
    restored = packet.guard_out.restored_response or packet.guard_out.sanitized_response

    return ChatIAResponse(
        request_id=packet.request_id,
        timestamp_utc=packet.timestamp_utc,
        policy_status=packet.guard_out.policy_status,
        masked_prompt=packet.masked_text,
        sanitized_response=packet.guard_out.sanitized_response,
        restored_response=restored,
        ai_generated_notice=packet.llm.ai_generated_notice,
        pii_count=packet.shield.pii_count,
        detected_types=packet.shield.detected_types,
        rif_mod11_verified=packet.shield.rif_mod11_verified,
        file_name_sanitized=prepared.sanitized_name if prepared else None,
        file_sha256=prepared.sha256_hex if prepared else None,
        file_size_bytes=prepared.size_bytes if prepared else 0,
        model_recommendation=packet.explica.model_recommendation,
        human_decision=packet.explica.human_decision,
        human_override=packet.explica.human_override,
        probability_score=packet.explica.probability_score,
        linear_shap_values=dict(packet.explica.linear_shap_values),
        citizen_receipt_code=packet.ledger.citizen_receipt_code,
        block_index=packet.ledger.block_index,
        chain_verified=packet.ledger.chain_verified,
        latency_ms=total_latency,
        chunks_processed=prepared.chunks_processed if prepared else 0,
        user_role=dto.user_role,
        audit_action=dto.action,
    )


class ChatController(Controller):
    path = f"{API_PREFIX}/chat"
    guards = [chat_api_guard]

    @post("/stream", status_code=HTTP_200_OK, request_max_body_size=MAX_CHAT_REQUEST_BYTES)
    async def stream_upload(self, request: Request) -> ChatIAResponse:
        return await _execute_chat_pipeline(request)

    @post("/message", status_code=HTTP_200_OK, request_max_body_size=MAX_CHAT_REQUEST_BYTES)
    async def message(self, request: Request) -> ChatIAResponse:
        return await _execute_chat_pipeline(request)

    @post("/upload", status_code=HTTP_200_OK, request_max_body_size=MAX_CHAT_REQUEST_BYTES)
    async def upload(self, request: Request) -> ChatIAResponse:
        return await _execute_chat_pipeline(request)

    @post("/process", status_code=HTTP_200_OK, request_max_body_size=MAX_CHAT_REQUEST_BYTES)
    async def process(self, request: Request) -> ChatIAResponse:
        return await _execute_chat_pipeline(request)
