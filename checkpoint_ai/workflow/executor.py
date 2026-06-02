"""Task executor."""

from __future__ import annotations

import time
from dataclasses import asdict

from checkpoint_ai.evaluation import EvaluationGate
from checkpoint_ai.events import EventBus, EventType
from checkpoint_ai.memory import ContextManager
from checkpoint_ai.models import AgentState, Artifact, Task, TaskState
from checkpoint_ai.observability import PerformanceMonitor
from checkpoint_ai.runtime import BaseAgent


class TaskExecutor:
    """Execute tasks with selected agents."""

    def __init__(
        self,
        event_bus: EventBus | None = None,
        evaluation_gate: EvaluationGate | None = None,
        memory: ContextManager | None = None,
        performance_monitor: PerformanceMonitor | None = None,
    ) -> None:
        """Create a task executor."""

        self.event_bus = event_bus or EventBus()
        self.evaluation_gate = evaluation_gate
        self.memory = memory
        self.performance_monitor = performance_monitor

    def execute(self, task: Task, agent: BaseAgent) -> Artifact:
        """Run a task through an agent and update state."""

        self.event_bus.emit(EventType.TASK_STARTED, {"task_id": task.id, "agent": agent.name})
        task.transition_to(TaskState.RUNNING)
        agent_model = agent.to_model()
        agent_model.state = AgentState.BUSY
        agent_model.current_task = task.id
        started_at = time.perf_counter()
        try:
            artifact = agent.execute(task)
            task.output_artifact_id = artifact.id
            task.result = artifact.content
            if self._requires_evaluation(task):
                gate = self.evaluation_gate
                if gate is None:
                    raise RuntimeError("Evaluation gate is required but not configured.")
                passed, results = gate.check(
                    self._content_for_evaluation(artifact.content),
                    platform=str(task.metadata.get("evaluation_platform", "public")),
                    min_score=float(task.metadata.get("min_score", 70.0)),
                )
                task.metadata["evaluation"] = [asdict(result) for result in results]
                if not passed:
                    suggestions = gate.get_suggestions(results)
                    task.result = {
                        "output": artifact.content,
                        "evaluation_failed": True,
                        "evaluation": task.metadata["evaluation"],
                        "suggestions": suggestions,
                    }
                    self._record_evaluation_feedback(task, suggestions)
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
            if self.performance_monitor is not None:
                self.performance_monitor.record_task(
                    task_id=task.id,
                    run_id=task.run_id or "",
                    agent=agent.name,
                    duration_seconds=time.perf_counter() - started_at,
                )
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

    def _record_evaluation_feedback(self, task: Task, suggestions: list[str]) -> None:
        """Persist evaluation failure feedback for future runs in the same BusinessLine."""

        if self.memory is None:
            return
        self.memory.add_shared(
            business_line_id=task.business_line_id,
            run_id=task.run_id or "",
            task_id=task.id,
            kind="evaluation_feedback",
            content={
                "evaluation_failed": True,
                "task_name": task.name,
                "suggestions": suggestions,
            },
        )
