"""Workflow engine."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from loop_harness.control import HumanApprovalGate, PolicyEngine
from loop_harness.evaluation import EvaluationGate
from loop_harness.events import EventBus, EventType
from loop_harness.memory import ContextManager
from loop_harness.models import Run, Task, TaskState
from loop_harness.observability import PerformanceMonitor
from loop_harness.runtime import AgentRegistry, BaseAgent
from loop_harness.workflow.executor import TaskExecutor
from loop_harness.workflow.task_queue import TaskQueue


class WorkflowEngine:
    """Schedule and execute run tasks."""

    def __init__(
        self,
        agent_registry: AgentRegistry,
        event_bus: EventBus | None = None,
        policy_engine: PolicyEngine | None = None,
        human_gate: HumanApprovalGate | None = None,
        evaluation_gate: EvaluationGate | None = None,
        memory: ContextManager | None = None,
        performance_monitor: PerformanceMonitor | None = None,
        max_concurrency: int = 1,
    ) -> None:
        """Create a workflow engine."""

        if max_concurrency <= 0:
            raise ValueError("max_concurrency must be greater than zero.")
        self.agent_registry = agent_registry
        self.event_bus = event_bus or EventBus()
        self.policy_engine = policy_engine or PolicyEngine()
        self.human_gate = human_gate or HumanApprovalGate()
        self.evaluation_gate = evaluation_gate
        self.memory = memory
        self.max_concurrency = max_concurrency
        if self.human_gate.event_bus is None:
            self.human_gate.event_bus = self.event_bus
        self.executor = TaskExecutor(
            event_bus=self.event_bus,
            evaluation_gate=self.evaluation_gate,
            memory=self.memory,
            performance_monitor=performance_monitor,
        )
        self.queue = TaskQueue()

    def schedule(self, run: Run) -> None:
        """Schedule pending tasks."""

        for task in run.tasks:
            if task.state == TaskState.PENDING:
                self.queue.push(task)
                self.event_bus.emit(EventType.TASK_SCHEDULED, {"run_id": run.id, "task_id": task.id})

    def _emit_schedule_events(self, run: Run) -> None:
        """Emit schedule events without using the sequential queue."""

        for task in run.tasks:
            if task.state == TaskState.PENDING:
                self.event_bus.emit(EventType.TASK_SCHEDULED, {"run_id": run.id, "task_id": task.id})

    def run(self, run: Run) -> Run:
        """Execute scheduled tasks until the queue is empty."""

        run.mark_running()
        self.event_bus.emit(EventType.RUN_STARTED, {"run_id": run.id})
        if self.max_concurrency > 1:
            self._run_concurrent(run)
        else:
            self._run_sequential(run)
        run.mark_completed_if_done()
        self.event_bus.emit(EventType.RUN_COMPLETED, {"run_id": run.id, "state": run.state.value})
        return run

    def _run_sequential(self, run: Run) -> None:
        """Run tasks sequentially through the existing queue path."""

        self.schedule(run)
        while len(self.queue):
            task = self.queue.pop()
            if task is None:
                break
            if task.state != TaskState.PENDING:
                self.event_bus.emit(
                    EventType.TASK_SKIPPED,
                    {"task_id": task.id, "state": task.state.value},
                )
                continue
            self._execute_task(task)

    def _run_concurrent(self, run: Run) -> None:
        """Run independent pending tasks concurrently."""

        self._emit_schedule_events(run)
        with ThreadPoolExecutor(max_workers=self.max_concurrency) as pool:
            while True:
                pending = [task for task in run.tasks if task.state == TaskState.PENDING]
                if not pending:
                    break
                self._fail_tasks_with_failed_dependencies(run)
                ready_tasks = [
                    task
                    for task in pending
                    if task.state == TaskState.PENDING and self._dependencies_succeeded(task, run)
                ]
                if not ready_tasks:
                    self._fail_unresolved_dependencies(run)
                    break
                futures = [
                    pool.submit(self._execute_task, task)
                    for task in ready_tasks[: self.max_concurrency]
                ]
                for future in as_completed(futures):
                    future.result()

    def _execute_task(self, task: Task) -> None:
        """Execute one task with policy, approval, and agent routing."""

        if task.state != TaskState.PENDING:
            self.event_bus.emit(
                EventType.TASK_SKIPPED,
                {"task_id": task.id, "state": task.state.value},
            )
            return
        agent = self._prepare_agent(task)
        if agent is None:
            return
        try:
            self.executor.execute(task, agent)
        except Exception:
            return

    def _prepare_agent(self, task: Task) -> BaseAgent | None:
        """Apply policy and return a matching agent when executable."""

        policy = self.policy_engine.evaluate_action(task.name)
        if policy.requires_approval or bool(task.metadata.get("requires_approval")):
            task.transition_to(TaskState.RUNNING)
            task.transition_to(TaskState.WAITING_APPROVAL)
            if not self.human_gate.request_approval(
                policy,
                message=f"Task needs approval: {task.name}",
                subject=task,
            ):
                task.transition_to(TaskState.FAILED)
                self.event_bus.emit(
                    EventType.TASK_FAILED,
                    {"task_id": task.id, "error": "Approval rejected."},
                )
                return None
            task.transition_to(TaskState.RUNNING)
        agent = self.agent_registry.create_agent_for_capability(task.agent_capability)
        if agent is None:
            task.transition_to(TaskState.RUNNING)
            task.error = f"No agent for capability: {task.agent_capability}"
            task.transition_to(TaskState.FAILED)
            self.event_bus.emit(EventType.TASK_FAILED, {"task_id": task.id, "error": task.error})
            return None
        return agent

    def _dependencies_succeeded(self, task: Task, run: Run) -> bool:
        """Return true when all declared dependencies succeeded."""

        task_by_id = {candidate.id: candidate for candidate in run.tasks}
        for dependency_id in self._dependency_ids(task):
            dependency = task_by_id.get(dependency_id)
            if dependency is None or dependency.state != TaskState.SUCCEEDED:
                return False
        return True

    def _fail_tasks_with_failed_dependencies(self, run: Run) -> None:
        """Fail pending tasks whose dependencies are already terminal failures."""

        task_by_id = {task.id: task for task in run.tasks}
        failed_states = {
            TaskState.FAILED,
            TaskState.EVALUATION_FAILED,
            TaskState.CANCELLED,
        }
        for task in run.tasks:
            if task.state != TaskState.PENDING:
                continue
            for dependency_id in self._dependency_ids(task):
                dependency = task_by_id.get(dependency_id)
                if dependency is not None and dependency.state in failed_states:
                    task.transition_to(TaskState.RUNNING)
                    task.error = f"Dependency failed: {dependency_id}"
                    task.transition_to(TaskState.FAILED)
                    self.event_bus.emit(
                        EventType.TASK_FAILED,
                        {"task_id": task.id, "error": task.error},
                    )
                    break

    def _fail_unresolved_dependencies(self, run: Run) -> None:
        """Fail tasks with missing or cyclic dependencies."""

        for task in run.tasks:
            if task.state == TaskState.PENDING:
                task.transition_to(TaskState.RUNNING)
                task.error = "Dependencies could not be resolved."
                task.transition_to(TaskState.FAILED)
                self.event_bus.emit(EventType.TASK_FAILED, {"task_id": task.id, "error": task.error})

    def _dependency_ids(self, task: Task) -> list[str]:
        """Read dependency ids from task metadata."""

        dependencies = task.metadata.get("depends_on", [])
        if isinstance(dependencies, str):
            return [dependencies]
        if isinstance(dependencies, list):
            return [str(dependency) for dependency in dependencies]
        return []
