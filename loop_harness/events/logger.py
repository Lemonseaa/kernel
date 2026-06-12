"""Audit logger."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loop_harness.events.bus import Event


class AuditLogger:
    """Simple structured audit log sink."""

    def __init__(self, path: str | Path | None = None) -> None:
        """Create an in-memory audit logger."""

        self.path = Path(path) if path is not None else None
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.records: list[dict[str, object]] = []

    def log(self, event: Event) -> None:
        """Append an event to the audit log."""

        record = self._to_record(event)
        self.records.append(record)
        if self.path is not None:
            with self.path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    @staticmethod
    def _to_record(event: Event) -> dict[str, Any]:
        """Convert an event into a JSON-serializable audit record."""

        payload = event.payload
        return {
            "event_id": event.id,
            "event_type": event.type,
            "type": event.type,
            "created_at": event.created_at,
            "run_id": payload.get("run_id"),
            "task_id": payload.get("task_id"),
            "agent_name": payload.get("agent") or payload.get("agent_name"),
            "payload": payload,
        }
