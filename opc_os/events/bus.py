"""In-memory event bus."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable
from uuid import uuid4


class EventType(str, Enum):
    """Built-in opc_os event types."""

    RUN_CREATED = "run:created"
    RUN_STARTED = "run:started"
    RUN_COMPLETED = "run:completed"
    TASK_CREATED = "task:created"
    TASK_SCHEDULED = "task:scheduled"
    TASK_STARTED = "task:started"
    TASK_COMPLETED = "task:completed"
    TASK_FAILED = "task:failed"
    TASK_SKIPPED = "task:skipped"
    APPROVAL_REQUESTED = "approval:requested"
    APPROVAL_APPROVED = "approval:approved"
    APPROVAL_REJECTED = "approval:rejected"


@dataclass(slots=True)
class Event:
    """OPC-OS event."""

    type: str
    payload: dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EventBus:
    """Record and publish opc_os events."""

    def __init__(self) -> None:
        """Create an in-memory event bus."""

        self.events: list[Event] = []
        self._subscribers: list[Callable[[Event], None]] = []
        self._typed_subscribers: dict[str, list[Callable[[Event], None]]] = {}
        self.subscriber_errors: list[dict[str, str]] = []

    def subscribe(
        self,
        event_type_or_handler: str | EventType | Callable[[Event], None],
        handler: Callable[[Event], None] | None = None,
    ) -> None:
        """Subscribe to all events or one event type."""

        if handler is None:
            if not callable(event_type_or_handler):
                raise ValueError("Global subscription requires a handler.")
            self._subscribers.append(event_type_or_handler)
            return
        event_type = self._normalize_type(event_type_or_handler)
        self._typed_subscribers.setdefault(event_type, []).append(handler)

    def emit(self, event_type: str | EventType, payload: dict[str, Any] | None = None) -> Event:
        """Emit and store an event."""

        normalized_type = self._normalize_type(event_type)
        event = Event(type=normalized_type, payload=payload or {})
        self.events.append(event)
        for handler in [*self._subscribers, *self._typed_subscribers.get(normalized_type, [])]:
            try:
                handler(event)
            except Exception as exc:
                self.subscriber_errors.append(
                    {
                        "event_id": event.id,
                        "event_type": event.type,
                        "handler": getattr(handler, "__name__", handler.__class__.__name__),
                        "error": str(exc),
                    }
                )
        return event

    @staticmethod
    def _normalize_type(event_type: str | EventType | Callable[[Event], None]) -> str:
        """Normalize enum and string event types."""

        if isinstance(event_type, EventType):
            return event_type.value
        if isinstance(event_type, str):
            return event_type
        raise ValueError("Event type must be a string or EventType.")
