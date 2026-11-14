"""Jerarquía de errores del dominio.

Regla Zero-Leak: ningún mensaje de excepción puede incluir texto crudo del
ciudadano. Los mensajes describen la categoría del fallo, nunca el contenido.
"""

from __future__ import annotations


class AduanaError(Exception):
    """Base de todos los errores del dominio."""


class ConsentError(AduanaError):
    """Consentimiento ausente o sin propósito declarado (BLOCKED_NO_CONSENT)."""


class RateLimitError(AduanaError):
    """Tasa por ``blind_citizen_id`` excedida."""


class VaultError(AduanaError):
    """Error genérico de la bóveda efímera."""


class VaultExpiredError(VaultError):
    """La sesión superó el TTL de 180 s y fue purgada."""


class VaultSessionNotFoundError(VaultError):
    """No existe sesión en la bóveda para el ``request_id`` dado."""


class ImmutableLedgerError(AduanaError):
    """Intento de UPDATE/DELETE sobre ``ledger_blocks`` (ERR_IMMUTABLE_LEDGER)."""


class StorageError(AduanaError):
    """Fallo de persistencia no relacionado con inmutabilidad."""


class LLMUnavailableError(AduanaError):
    """El adaptador LLM agotó el timeout o falló la red (activa Circuit Breaker)."""


class ShieldResidualPiiError(AduanaError):
    """SHIELD no logró anonimizar el texto (fail-closed); sin contenido en el mensaje."""


class InvalidFeaturesError(AduanaError, ValueError):
    """Variables de EXPLICA ausentes, sobrantes o no finitas (HTTP 422 ERR_INVALID_FEATURES).

    Hereda de ``ValueError`` para no romper a quien ya capturaba ese tipo. El mensaje nombra las
    variables, que son parámetros del modelo y no texto ciudadano.
    """


class OverrideJustificationError(AduanaError):
    """Override humano sin justificación de al menos 20 caracteres (RF-20)."""
