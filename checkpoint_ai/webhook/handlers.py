"""Webhook event handlers."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, cast

from checkpoint_ai.models import Run, TaskSpec

if TYPE_CHECKING:
    from checkpoint_ai.checkpoint_ai import CheckpointAI


class WebhookHandler:
    """Handle inbound webhook events."""

    def __init__(self, checkpoint_ai: "CheckpointAI") -> None:
        """Create handler for one checkpoint_ai."""

        self.checkpoint_ai = checkpoint_ai

    def handle(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle one external webhook event."""

        if event_type == "workflow.trigger":
            return self._trigger_workflow(payload)
        self.checkpoint_ai.event_bus.emit(
            "webhook:received",
            {"event_type": event_type, "payload": payload},
        )
        return {"status": "ignored", "event_type": event_type}

    def _trigger_workflow(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create and execute a workflow from a webhook payload."""

        description = str(payload.get("description", "webhook workflow"))
        raw_tasks = payload.get("tasks", [])
        if not isinstance(raw_tasks, list):
            raw_tasks = []
        task_specs: list[TaskSpec] = [
            TaskSpec(
                description=str(item.get("description", "webhook task")),
                capability=str(item.get("capability", "simple.execute")),
                input=item.get("input"),
            )
            for item in raw_tasks
            if isinstance(item, dict)
        ]
        if not task_specs:
            task_specs = [TaskSpec(description=description)]
        run = cast(Run, asyncio.run(self.checkpoint_ai.run(description, task_specs)))
        return {"status": "accepted", "run_id": run.id, "state": run.state.value}
