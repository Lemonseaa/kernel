"""Task executor."""

from __future__ import annotations

from dataclasses import asdict

from kernel.evaluation import EvaluationGate
from kernel.events import EventBus, EventType
from kernel.models import AgentState, Artifact, Task, TaskState
from kernel.runtime import BaseAgent


class TaskExecutor:
    """Execute tasks with selected agents."""

    def __init__(
        self,
        event_bus: EventBus | None = None,
        evaluation_gate: EvaluationGate | None = None,
    ) -> None:
        """Create a task executor."""

        self.event_bus = event_bus or EventBus()
        self.evaluation_gate = evaluation_gate

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
            if self._requires_evaluation(task):
                passed, results = self.evaluation_gate.check(
                    self._content_for_evaluation(artifact.content),
                    platform=str(task.metadata.get("evaluation_platform", "public")),
                    min_score=float(task.metadata.get("min_score", 70.0)),
                )
                task.metadata["evaluation"] = [asdict(result) for result in results]
                if not passed:
                    suggestions = self.evaluation_gate.get_suggestions(results)
                    task.result = {
                        "output": artifact.content,
                        "evaluation_failed": True,
                        "evaluation": task.metadata["evaluation"],
                        "suggestions": suggestions,
                    }
                    task.transition_to(TaskState.EVALUATION_FAILED)
                    self.event_bus.emit(
                        "evaluation:failed",
                        {
                            "task_id": task.id,
                            "agent": agent.name,
                            "suggestions": suggestions,
                        },
                    )
                    self.event_bus.emit(
                        EventType.TASK_FAILED,
                        {"task_id": task.id, "error": "Evaluation gate failed."},
                    )
                    return artifact
                self.event_bus.emit(
                    "evaluation:passed",
                    {"task_id": task.id, "agent": agent.name},
                )
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

    def _requires_evaluation(self, task: Task) -> bool:
        """Return true when this task should pass through the evaluation gate."""

        return bool(task.metadata.get("evaluation_required")) and self.evaluation_gate is not None

    def _content_for_evaluation(self, content: object) -> str:
        """Extract text from an artifact content payload."""

        if isinstance(content, dict):
            output = content.get("output")
            if output is not None:
                return str(output)
        return str(content)
