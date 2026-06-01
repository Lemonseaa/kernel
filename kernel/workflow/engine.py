"""Workflow engine."""

from __future__ import annotations

from kernel.control import HumanApprovalGate, PolicyEngine
from kernel.events import EventBus
from kernel.models import Run, Task, TaskState
from kernel.runtime import AgentRegistry
from kernel.workflow.executor import TaskExecutor
from kernel.workflow.task_queue import TaskQueue


class WorkflowEngine:
    """Schedule and execute run tasks."""

    def __init__(
        self,
        agent_registry: AgentRegistry,
        event_bus: EventBus | None = None,
        policy_engine: PolicyEngine | None = None,
        human_gate: HumanApprovalGate | None = None,
    ) -> None:
        """Create a workflow engine."""

        self.agent_registry = agent_registry
        self.event_bus = event_bus or EventBus()
        self.policy_engine = policy_engine or PolicyEngine()
        self.human_gate = human_gate or HumanApprovalGate()
        self.executor = TaskExecutor(event_bus=self.event_bus)
        self.queue = TaskQueue()

    def schedule(self, run: Run) -> None:
        """Schedule pending tasks."""

        for task in run.tasks:
            if task.state == TaskState.PENDING:
                self.queue.push(task)
                self.event_bus.emit("task.scheduled", {"run_id": run.id, "task_id": task.id})

    def run(self, run: Run) -> Run:
        """Execute scheduled tasks until the queue is empty."""

        run.mark_running()
        self.event_bus.emit("run.started", {"run_id": run.id})
        self.schedule(run)
        while len(self.queue):
            task = self.queue.pop()
            if task is None:
                break
            policy = self.policy_engine.evaluate_action(task.name)
            if policy.requires_approval:
                task.transition_to(TaskState.RUNNING)
                task.transition_to(TaskState.WAITING_APPROVAL)
                self.event_bus.emit("approval.requested", {"task_id": task.id, "policy_id": policy.id})
                if not self.human_gate.request_approval(policy):
                    task.transition_to(TaskState.FAILED)
                    continue
                task.transition_to(TaskState.RUNNING)
            agent = self.agent_registry.create_agent_for_capability(task.agent_capability)
            if agent is None:
                task.transition_to(TaskState.RUNNING)
                task.error = f"No agent for capability: {task.agent_capability}"
                task.transition_to(TaskState.FAILED)
                self.event_bus.emit("task.failed", {"task_id": task.id, "error": task.error})
                continue
            self.executor.execute(task, agent)
        run.mark_completed_if_done()
        self.event_bus.emit("run.completed", {"run_id": run.id, "state": run.state.value})
        return run
