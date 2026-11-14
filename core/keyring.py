"""KeyRing: única llave maestra en RAM con subllaves separadas por dominio.

- La llave vive en un ``bytearray`` que ``wipe()`` sobrescribe.
- Los bytes crudos nunca salen: solo operaciones (``hmac_hex``, ``verify``).
- No es copiable, picklable ni imprimible (``repr`` redactado).
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Final, NoReturn

MIN_KEY_BYTES: Final[int] = 32
_DOMAIN_PREFIX: Final[bytes] = b"aduana/v1/"

# Dominios permitidos: una llave comprometida en un uso no compromete a las demás.
DOMAINS: Final[frozenset[str]] = frozenset(
    {"ledger-sign", "canary", "blind-index", "rate-guard", "consent", "key-id", "justification"}
)


class KeyRing:
    __slots__ = ("_master", "_wiped")

    def __init__(self, master: bytes) -> None:
        if len(master) < MIN_KEY_BYTES:
            raise ValueError("La llave maestra debe tener al menos 32 bytes.")
        if len(set(master)) < 4:  # solo guardarrail contra llaves triviales, no mide entropía
            raise ValueError("Llave maestra degenerada.")
        self._master = bytearray(master)
        self._wiped = False

    def _subkey(self, domain: str) -> bytes:
        if self._wiped:
            raise RuntimeError("KeyRing destruido: llave sobrescrita.")
        if domain not in DOMAINS:
            raise ValueError("Dominio de llave desconocido.")
        return hmac.new(
            bytes(self._master), _DOMAIN_PREFIX + domain.encode(), hashlib.sha256
        ).digest()

    def hmac_hex(self, domain: str, data: bytes) -> str:
        """HMAC-SHA256 con la subllave del dominio."""
        return hmac.new(self._subkey(domain), data, hashlib.sha256).hexdigest()

    def verify(self, domain: str, data: bytes, expected_hex: str) -> bool:
        """Comparación en tiempo constante; tolera no ASCII y valores no str (NULL de BD)."""
        if not isinstance(expected_hex, str):
            return False
        return hmac.compare_digest(self.hmac_hex(domain, data).encode(), expected_hex.encode())

    @property
    def key_id(self) -> str:
        """Identificador público (64 bits) de la época de llave; no revela la llave."""
        return self.hmac_hex("key-id", b"")[:16]

    def wipe(self) -> None:
        """Sobrescribe la llave (mejor esfuerzo: ``bytes`` temporales no se pueden borrar)."""
        self._master[:] = bytes(len(self._master))
        self._wiped = True

    def __repr__(self) -> str:
        return "KeyRing(<redacted>)"

    __str__ = __repr__

    def __reduce__(self) -> NoReturn:
        raise TypeError("KeyRing no es serializable.")

    def __copy__(self) -> NoReturn:
        raise TypeError("KeyRing no es copiable.")

    def __deepcopy__(self, memo: object) -> NoReturn:
        raise TypeError("KeyRing no es copiable.")
