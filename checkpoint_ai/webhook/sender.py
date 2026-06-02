"""Webhook event sender."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Callable
from urllib import request

from checkpoint_ai.events import Event, EventBus, EventType

WEBHOOK_EVENT_MAP = {
    EventType.RUN_COMPLETED.value: "run.completed",
    EventType.TASK_FAILED.value: "task.failed",
    EventType.APPROVAL_REQUESTED.value: "approval.required",
    "alert:triggered": "alert.triggered",
}


@dataclass(slots=True)
class WebhookDelivery:
    """Webhook delivery result."""

    url: str
    event_type: str
    success: bool
    attempts: int
    error: str | None = None
    created_at: float = field(default_factory=time.time)


class WebhookSender:
    """Send selected checkpoint_ai events to external webhook URLs."""

    def __init__(
        self,
        event_bus: EventBus,
        urls: list[str] | None = None,
        transport: Callable[[str, dict[str, object], dict[str, str]], object] | None = None,
        max_retries: int = 2,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Create sender and subscribe to supported events."""

        self.event_bus = event_bus
        self.urls = urls or []
        self.transport = transport or self._default_transport
        self.max_retries = max_retries
        self.headers = headers or {}
        self.deliveries: list[WebhookDelivery] = []
        self._subscribe()

    def send(self, event_type: str, payload: dict[str, object]) -> list[WebhookDelivery]:
        """Send one webhook event to all configured URLs."""

        deliveries: list[WebhookDelivery] = []
        webhook_payload = {"event_type": event_type, "payload": payload, "sent_at": time.time()}
        for url in self.urls:
            deliveries.append(self._send_to_url(url, event_type, webhook_payload))
        self.deliveries.extend(deliveries)
        return deliveries

    def _subscribe(self) -> None:
        """Subscribe to supported checkpoint_ai events."""

        for event_type in WEBHOOK_EVENT_MAP:
            self.event_bus.subscribe(event_type, self._handle_event)

    def _handle_event(self, event: Event) -> None:
        """Forward a checkpoint_ai event as an external webhook."""

        public_event = WEBHOOK_EVENT_MAP.get(event.type)
        if public_event is None:
            return
        self.send(public_event, dict(event.payload))

    def _send_to_url(
        self,
        url: str,
        event_type: str,
        payload: dict[str, object],
    ) -> WebhookDelivery:
        """Send to one URL with bounded retries."""

        attempts = 0
        last_error: str | None = None
        for attempt in range(self.max_retries + 1):
            attempts = attempt + 1
            try:
                self.transport(url, payload, self.headers)
                return WebhookDelivery(url=url, event_type=event_type, success=True, attempts=attempts)
            except Exception as exc:
                last_error = str(exc)
        return WebhookDelivery(
            url=url,
            event_type=event_type,
            success=False,
            attempts=attempts,
            error=last_error,
        )

    def _default_transport(self, url: str, payload: dict[str, object], headers: dict[str, str]) -> object:
        """POST JSON to a webhook URL with the standard library."""

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        merged_headers = {"Content-Type": "application/json", **headers}
        req = request.Request(url, data=body, headers=merged_headers, method="POST")
        with request.urlopen(req, timeout=10) as response:  # noqa: S310 - caller controls webhook URL.
            return {"status": response.status}
