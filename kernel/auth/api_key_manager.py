"""API key generation and verification."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from hashlib import sha256


@dataclass(slots=True)
class APIKeyRecord:
    """Stored API key metadata."""

    name: str
    token_hash: str
    active: bool = True
    created_at: float = field(default_factory=time.time)
    revoked_at: float | None = None


class APIKeyManager:
    """In-memory API key manager for bearer token authentication."""

    def __init__(self, initial_tokens: list[str] | None = None) -> None:
        """Create an API key manager."""

        self._records: dict[str, APIKeyRecord] = {}
        for token in initial_tokens or []:
            self.add_token(token, name="initial")

    def generate_token(self, name: str = "api") -> str:
        """Generate and store a new bearer token."""

        token = secrets.token_urlsafe(32)
        self.add_token(token, name=name)
        return token

    def add_token(self, token: str, name: str = "api") -> None:
        """Store an existing token."""

        self._records[self._hash(token)] = APIKeyRecord(name=name, token_hash=self._hash(token))

    def verify_token(self, token: str) -> bool:
        """Return true when token exists and is active."""

        record = self._records.get(self._hash(token))
        return record is not None and record.active

    def revoke_token(self, token: str) -> bool:
        """Revoke a token."""

        record = self._records.get(self._hash(token))
        if record is None or not record.active:
            return False
        record.active = False
        record.revoked_at = time.time()
        return True

    def list_keys(self) -> list[APIKeyRecord]:
        """List stored key metadata without raw tokens."""

        return list(self._records.values())

    def _hash(self, token: str) -> str:
        """Hash a token for storage."""

        return sha256(token.encode("utf-8")).hexdigest()
