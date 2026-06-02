"""Webhook receiver."""

from __future__ import annotations

from typing import Any

from checkpoint_ai.auth import BearerTokenAuth
from checkpoint_ai.webhook.handlers import WebhookHandler


class WebhookReceiver:
    """Receive external webhook requests and dispatch to handlers."""

    def __init__(
        self,
        handler: WebhookHandler,
        auth: BearerTokenAuth | None = None,
    ) -> None:
        """Create a webhook receiver."""

        self.handler = handler
        self.auth = auth

    def receive(
        self,
        body: dict[str, Any],
        authorization: str | None = None,
    ) -> dict[str, Any]:
        """Validate and handle one webhook request body."""

        if self.auth is not None:
            self.auth.require(authorization)
        event_type = str(body.get("event_type", ""))
        if not event_type:
            return {"status": "rejected", "reason": "missing event_type"}
        payload = body.get("payload", {})
        if not isinstance(payload, dict):
            return {"status": "rejected", "reason": "payload must be an object"}
        return self.handler.handle(event_type, payload)
