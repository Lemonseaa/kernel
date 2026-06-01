"""Run model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from kernel.models.task import Task, TaskState


class RunState(str, Enum):
    """Run lifecycle states."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class Run:
    """A complete workflow run containing multiple tasks."""

    user_request: str
    id: str = field(default_factory=lambda: str(uuid4()))
    state: RunState = RunState.PENDING
    tasks: list[Task] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_task(self, task: Task) -> None:
        """Attach a task to this run."""

        task.run_id = self.id
        self.tasks.append(task)

    def mark_running(self) -> None:
        """Mark this run as running."""

        if self.state == RunState.PENDING:
            self.state = RunState.RUNNING

    def mark_completed_if_done(self) -> None:
        """Finish the run if all tasks are terminal."""

        if not self.tasks:
            return
        if any(task.state in {TaskState.FAILED, TaskState.EVALUATION_FAILED} for task in self.tasks):
            self.state = RunState.FAILED
            return
        if any(task.state == TaskState.CANCELLED for task in self.tasks):
            self.state = RunState.CANCELLED
            return
        if all(task.state == TaskState.SUCCEEDED for task in self.tasks):
            self.state = RunState.SUCCEEDED
