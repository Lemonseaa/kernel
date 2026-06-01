"""In-memory event bus."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4


@dataclass(slots=True)
class Event:
    """Kernel event."""

    type: str
    payload: dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EventBus:
    """Record and publish kernel events."""

    def __init__(self) -> None:
        """Create an in-memory event bus."""

        self.events: list[Event] = []
        self._subscribers: list[Callable[[Event], None]] = []
        self.subscriber_errors: list[dict[str, str]] = []

    def subscribe(self, handler: Callable[[Event], None]) -> None:
        """Subscribe to all events."""

        self._subscribers.append(handler)

    def emit(self, event_type: str, payload: dict[str, Any] | None = None) -> Event:
        """Emit and store an event."""

        event = Event(type=event_type, payload=payload or {})
        self.events.append(event)
        for handler in self._subscribers:
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
