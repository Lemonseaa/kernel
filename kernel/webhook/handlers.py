"""Webhook event handlers."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from typing import Any

from kernel.models import TaskSpec

if TYPE_CHECKING:
    from kernel.kernel import Kernel


class WebhookHandler:
    """Handle inbound webhook events."""

    def __init__(self, kernel: "Kernel") -> None:
        """Create handler for one kernel."""

        self.kernel = kernel

    def handle(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle one external webhook event."""

        if event_type == "workflow.trigger":
            return self._trigger_workflow(payload)
        self.kernel.event_bus.emit(
            "webhook:received",
            {"event_type": event_type, "payload": payload},
        )
        return {"status": "ignored", "event_type": event_type}

    def _trigger_workflow(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create and execute a workflow from a webhook payload."""

        description = str(payload.get("description", "webhook workflow"))
        task_specs = [
            TaskSpec(
                description=str(item.get("description", "webhook task")),
                capability=str(item.get("capability", "simple.execute")),
                input=item.get("input"),
            )
            for item in payload.get("tasks", [])
            if isinstance(item, dict)
        ]
        if not task_specs:
            task_specs = [TaskSpec(description=description)]
        run = asyncio.run(self.kernel.run(description, task_specs))
        return {"status": "accepted", "run_id": run.id, "state": run.state.value}
