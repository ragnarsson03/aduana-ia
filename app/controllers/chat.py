"""Controlador Zero-Trust para el Chat de IA con adjuntos (POST /api/v1/chat/*).

Cumple estrictamente:
- Zero-Plaintext-PII: el texto extraído del archivo adjunto se inyecta en ``GatewayPipeline``
  junto con el prompt, pasando por SHIELD -> GUARD-IN -> LLM -> GUARD-OUT (con rehidratación
  en RAM desde ``EphemeralVault``) -> EXPLICA (SHAP lineal determinista) -> LEDGER (SHA-256 + HMAC)
  -> ``finally: EphemeralVault.zeroize()``.
- Soporta tanto ``application/json`` (``ChatIAUploadRequest`` con base64) como
  ``multipart/form-data``.
"""

from __future__ import annotations

import base64
import json
import secrets
from typing import Any

import msgspec
from litestar import Controller, Request, post
from litestar.connection import ASGIConnection
from litestar.datastructures import UploadFile
from litestar.exceptions import HTTPException, NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler
from litestar.status_codes import HTTP_200_OK

from app.dependencies import AppState
from app.schemas import ChatIAResponse, ChatIAUploadRequest
from app.security import TOKEN_HEADER
from core.config import API_PREFIX
from core.context import BlockedPacket
from core.errors import AttachmentValidationError
from pipeline.chat_attachments import (
    MAX_CHAT_ATTACHMENT_BYTES,
    ExtractedAttachment,
    compose_gateway_raw_text,
    derive_chat_features,
    extract_attachment_from_b64,
    extract_attachment_from_bytes,
)
from pipeline.orchestrator import GatewayInput


def chat_api_guard(connection: ASGIConnection, _: BaseRouteHandler) -> None:
    expected: str = connection.app.state.aduana.api_token
    supplied = connection.headers.get(TOKEN_HEADER, "")
    if not secrets.compare_digest(supplied.encode(), expected.encode()):
        raise NotAuthorizedException(detail="UNAUTHORIZED")
    if connection.scope["method"] in {"POST", "PUT", "PATCH"}:
        content_type = connection.headers.get("content-type", "").split(";")[0].strip().lower()
        if content_type not in {"application/json", "multipart/form-data"}:
            raise HTTPException(status_code=415, detail="UNSUPPORTED_MEDIA_TYPE")


async def _parse_chat_request(
    request: Request,
) -> tuple[ChatIAUploadRequest, ExtractedAttachment | None]:
    """Decodifica y valida la solicitud de Chat IA (JSON o multipart/form-data) en RAM."""
    content_type = (request.headers.get("content-type") or "").lower()

    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        prompt_val = str(form.get("prompt") or "").strip()
        cedula_val = str(form.get("citizen_cedula") or "V-12345678").strip()
        purpose_val = str(form.get("purpose_code") or "CHAT_IA_CONSULTA").strip()
        consent_raw = str(form.get("consent_granted") or "true").strip().lower()
        consent_val = consent_raw not in {"false", "0", "no"}

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
        attachment: ExtractedAttachment | None = None
        file_name: str | None = None
        file_mime: str | None = None
        file_b64: str | None = None

        if isinstance(upload_obj, UploadFile):
            raw_bytes = bytearray(await upload_obj.read())
            try:
                if len(raw_bytes) > MAX_CHAT_ATTACHMENT_BYTES:
                    raise AttachmentValidationError("Archivo adjunto supera el límite de 32 KB.")
                file_name = upload_obj.filename or "adjunto.txt"
                file_mime = upload_obj.content_type or "text/plain"
                attachment = extract_attachment_from_bytes(
                    raw_bytes,
                    file_name=file_name,
                    file_mime_type=file_mime,
                )
                file_b64 = base64.b64encode(b"validated").decode("ascii")
            finally:
                raw_bytes[:] = bytes(len(raw_bytes))
        elif form.get("file_content_b64"):
            file_name = str(form.get("file_name") or "adjunto.txt")
            file_mime = str(form.get("file_mime_type") or "text/plain")
            file_b64 = str(form.get("file_content_b64"))

        raw_dict: dict[str, Any] = {
            "prompt": prompt_val,
            "citizen_cedula": cedula_val,
            "purpose_code": purpose_val,
            "consent_granted": consent_val,
            "file_name": file_name,
            "file_mime_type": file_mime,
            "file_content_b64": file_b64,
            "features": features_val,
            "human_decision": human_decision_val,
            "override_justification": override_just_val,
        }
        try:
            dto = msgspec.convert(raw_dict, type=ChatIAUploadRequest)
        except msgspec.ValidationError as exc:
            raise HTTPException(status_code=400, detail="INVALID_CHAT_PAYLOAD") from exc

        if attachment is None and dto.file_content_b64:
            attachment = extract_attachment_from_b64(
                dto.file_content_b64,
                file_name=dto.file_name or "",
                file_mime_type=dto.file_mime_type or "",
            )
        return dto, attachment

    raw_body = await request.body()
    try:
        dto = msgspec.json.decode(raw_body, type=ChatIAUploadRequest)
    except msgspec.ValidationError as exc:
        raise HTTPException(status_code=400, detail="INVALID_CHAT_PAYLOAD") from exc
    except msgspec.DecodeError as exc:
        raise HTTPException(status_code=400, detail="MALFORMED_JSON") from exc

    attachment = None
    has_any_file_field = any(
        x is not None for x in (dto.file_name, dto.file_mime_type, dto.file_content_b64)
    )
    if has_any_file_field:
        if not (dto.file_name and dto.file_mime_type and dto.file_content_b64):
            raise AttachmentValidationError(
                "Adjunto incompleto: requiere file_name, file_mime_type y file_content_b64."
            )
        attachment = extract_attachment_from_b64(
            dto.file_content_b64,
            file_name=dto.file_name,
            file_mime_type=dto.file_mime_type,
        )

    return dto, attachment


async def _execute_chat_pipeline(request: Request) -> ChatIAResponse:
    state: AppState = request.app.state.aduana
    dto, attachment = await _parse_chat_request(request)

    combined_raw_text = compose_gateway_raw_text(dto.prompt, attachment)
    features = (
        dict(dto.features)
        if dto.features is not None
        else derive_chat_features(
            combined_raw_text,
            has_attachment=attachment is not None,
            pii_count=1 if attachment is not None else 0,
            detected_types=(),
        )
    )

    gateway_in = GatewayInput(
        raw_text=combined_raw_text,
        citizen_cedula=dto.citizen_cedula,
        consent_granted=dto.consent_granted,
        purpose_code=dto.purpose_code,
        features=features,
        human_decision=dto.human_decision,
        override_justification=dto.override_justification,
        attachment_sha256=attachment.sha256_hex if attachment else "NONE",
        attachment_size_bytes=attachment.size_bytes if attachment else 0,
    )

    packet = await state.pipeline.process(gateway_in)
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
            file_name_sanitized=attachment.sanitized_name if attachment else None,
            file_sha256=attachment.sha256_hex if attachment else None,
            file_size_bytes=attachment.size_bytes if attachment else 0,
            model_recommendation="BLOQUEADO_SEGURIDAD",
            human_decision="BLOQUEADO_SEGURIDAD",
            human_override=False,
            probability_score=None,
            linear_shap_values=None,
            citizen_receipt_code=packet.ledger.citizen_receipt_code,
            block_index=packet.ledger.block_index,
            chain_verified=packet.ledger.chain_verified,
            latency_ms=0.0,
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
        file_name_sanitized=attachment.sanitized_name if attachment else None,
        file_sha256=attachment.sha256_hex if attachment else None,
        file_size_bytes=attachment.size_bytes if attachment else 0,
        model_recommendation=packet.explica.model_recommendation,
        human_decision=packet.explica.human_decision,
        human_override=packet.explica.human_override,
        probability_score=packet.explica.probability_score,
        linear_shap_values=dict(packet.explica.linear_shap_values),
        citizen_receipt_code=packet.ledger.citizen_receipt_code,
        block_index=packet.ledger.block_index,
        chain_verified=packet.ledger.chain_verified,
        latency_ms=total_latency,
    )


class ChatController(Controller):
    path = f"{API_PREFIX}/chat"
    guards = [chat_api_guard]

    @post("/message", status_code=HTTP_200_OK)
    async def message(self, request: Request) -> ChatIAResponse:
        return await _execute_chat_pipeline(request)

    @post("/upload", status_code=HTTP_200_OK)
    async def upload(self, request: Request) -> ChatIAResponse:
        return await _execute_chat_pipeline(request)

    @post("/process", status_code=HTTP_200_OK)
    async def process(self, request: Request) -> ChatIAResponse:
        return await _execute_chat_pipeline(request)
