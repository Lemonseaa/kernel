"""Bearer token authentication."""

from __future__ import annotations

from dataclasses import dataclass

from checkpoint_ai.auth.api_key_manager import APIKeyManager


@dataclass(slots=True)
class BearerTokenAuth:
    """Validate Authorization headers using APIKeyManager."""

    api_key_manager: APIKeyManager

    def authenticate(self, authorization: str | None) -> bool:
        """Return true when Authorization contains a valid bearer token."""

        token = self.extract_token(authorization)
        return token is not None and self.api_key_manager.verify_token(token)

    def require(self, authorization: str | None) -> None:
        """Raise PermissionError when the token is missing or invalid."""

        if not self.authenticate(authorization):
            raise PermissionError("Invalid or missing bearer token.")

    def extract_token(self, authorization: str | None) -> str | None:
        """Extract token from a Bearer header."""

        if not authorization:
            return None
        scheme, separator, token = authorization.partition(" ")
        if separator != " " or scheme.lower() != "bearer" or not token:
            return None
        return token.strip()
