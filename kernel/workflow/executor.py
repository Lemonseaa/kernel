"""Task executor."""

from __future__ import annotations

from kernel.events import EventBus, EventType
from kernel.models import AgentState, Artifact, Task, TaskState
from kernel.runtime import BaseAgent


class TaskExecutor:
    """Execute tasks with selected agents."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Create a task executor."""

        self.event_bus = event_bus or EventBus()

    def execute(self, task: Task, agent: BaseAgent) -> Artifact:
        """Run a task through an agent and update state."""

        self.event_bus.emit(EventType.TASK_STARTED, {"task_id": task.id, "agent": agent.name})
        task.transition_to(TaskState.RUNNING)
        agent_model = agent.to_model()
        agent_model.state = AgentState.BUSY
        agent_model.current_task = task.id
        try:
            artifact = agent.execute(task)
            task.output_artifact_id = artifact.id
            task.result = artifact.content
            task.transition_to(TaskState.SUCCEEDED)
            self.event_bus.emit(
                EventType.TASK_COMPLETED,
                {"task_id": task.id, "artifact_id": artifact.id, "agent": agent.name},
            )
            return artifact
        except Exception as exc:
            task.error = str(exc)
            task.transition_to(TaskState.FAILED)
            self.event_bus.emit(EventType.TASK_FAILED, {"task_id": task.id, "error": str(exc)})
            raise
        finally:
            agent_model.state = AgentState.IDLE
            agent_model.current_task = None
