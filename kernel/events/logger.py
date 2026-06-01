"""Audit logger."""

from __future__ import annotations

from kernel.events.bus import Event


class AuditLogger:
    """Simple structured audit log sink."""

    def __init__(self) -> None:
        """Create an in-memory audit logger."""

        self.records: list[dict[str, object]] = []

    def log(self, event: Event) -> None:
        """Append an event to the audit log."""

        self.records.append(
            {
                "event_id": event.id,
                "type": event.type,
                "created_at": event.created_at,
                "payload": event.payload,
            }
        )
