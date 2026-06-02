"""Optional HTTP API surface for the checkpoint_ai."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from checkpoint_ai.auth import APIKeyManager, BearerTokenAuth
from checkpoint_ai.checkpoint_ai import CheckpointAI


@dataclass(slots=True)
class FallbackApp:
    """Small app object used when FastAPI is not installed."""

    checkpoint_ai: CheckpointAI
    auth: BearerTokenAuth
    routes: list[dict[str, str]] = field(default_factory=list)

    def authenticate(self, authorization: str | None) -> bool:
        """Validate a bearer token in fallback mode."""

        return self.auth.authenticate(authorization)


def create_app(
    checkpoint_ai: CheckpointAI | None = None,
    auth_manager: APIKeyManager | None = None,
) -> Any:
    """Create a FastAPI app when available, otherwise return a fallback app."""

    active_checkpoint_ai = checkpoint_ai or CheckpointAI.from_env()
    active_auth = BearerTokenAuth(auth_manager or APIKeyManager())
    try:
        from fastapi import (  # type: ignore[import-not-found]
            Depends,
            FastAPI,
            Header,
            HTTPException,
        )
    except ImportError:
        return FallbackApp(
            checkpoint_ai=active_checkpoint_ai,
            auth=active_auth,
            routes=[
                {"method": "GET", "path": "/health"},
                {"method": "GET", "path": "/runs"},
                {"method": "GET", "path": "/metrics"},
            ],
        )

    app = FastAPI(title="Agent Workflow checkpointAI")

    def require_auth(authorization: str | None = Header(default=None)) -> None:
        if not active_auth.authenticate(authorization):
            raise HTTPException(status_code=401, detail="Invalid or missing bearer token.")

    @app.get("/health")
    def health(_auth: None = Depends(require_auth)) -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/runs")
    def list_runs(_auth: None = Depends(require_auth)) -> list[dict[str, Any]]:
        return active_checkpoint_ai.store.list_runs()

    @app.get("/metrics")
    def metrics(_auth: None = Depends(require_auth)) -> dict[str, Any]:
        return active_checkpoint_ai.metrics.get_summary()

    app.checkpoint_ai = active_checkpoint_ai
    app.auth = active_auth
    return app
