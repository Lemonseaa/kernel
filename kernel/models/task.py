"""Task model and state machine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class TaskState(str, Enum):
    """Task execution states."""

    PENDING = "pending"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


ALLOWED_TASK_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.PENDING: {TaskState.RUNNING, TaskState.CANCELLED},
    TaskState.RUNNING: {
        TaskState.WAITING_APPROVAL,
        TaskState.SUCCEEDED,
        TaskState.FAILED,
        TaskState.RETRYING,
        TaskState.CANCELLED,
    },
    TaskState.WAITING_APPROVAL: {TaskState.RUNNING, TaskState.FAILED, TaskState.CANCELLED},
    TaskState.RETRYING: {TaskState.RUNNING, TaskState.FAILED, TaskState.CANCELLED},
    TaskState.SUCCEEDED: set(),
    TaskState.FAILED: {TaskState.RETRYING},
    TaskState.CANCELLED: set(),
}


@dataclass(slots=True)
class Task:
    """A unit of work routed to an agent by capability."""

    name: str
    agent_capability: str
    input: Any = None
    id: str = field(default_factory=lambda: str(uuid4()))
    run_id: str | None = None
    state: TaskState = TaskState.PENDING
    output_artifact_id: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def transition_to(self, next_state: TaskState) -> None:
        """Move the task through the allowed state machine."""

        if next_state == self.state:
            return
        if next_state not in ALLOWED_TASK_TRANSITIONS[self.state]:
            raise ValueError(f"Invalid task transition: {self.state.value} -> {next_state.value}")
        self.state = next_state
