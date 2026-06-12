"""Compatibility facade for historical runtime features.

New code should prefer `checkpoint_ai.EvidenceHarness` for external workflow
evidence ingestion, visualization, comparison, and reporting. This facade keeps
older runtime/workflow tests and API paths import-compatible while the product
direction moves away from an internal Agent platform.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Coroutine, overload

from checkpoint_ai.businessline import (
    BusinessLine,
    BusinessLineConfig,
    BusinessLineRegistry,
    BusinessLineStatus,
)
from checkpoint_ai.cache import LLMResponseCache
from checkpoint_ai.config import CheckpointAIConfig
from checkpoint_ai.control import HumanApprovalGate, PolicyEngine
from checkpoint_ai.control.defaults import builtin_policies
from checkpoint_ai.diagnostics import HealthChecker
from checkpoint_ai.dryrun import DryRunContext, DryRunProvider
from checkpoint_ai.evaluation import EvaluationGate, EvaluationRunner
from checkpoint_ai.events import AuditLogger, Event, EventBus, EventType
from checkpoint_ai.experiment import ExperimentLedger
from checkpoint_ai.llm import ProviderRegistry
from checkpoint_ai.memory import ContextManager, PersistentMemory, WorkingMemory
from checkpoint_ai.models import Run, RunState, Task, TaskSpec, TaskState
from checkpoint_ai.notification import NotificationManager
from checkpoint_ai.observability import CostTracker, MetricsCollector, PerformanceMonitor
from checkpoint_ai.persistence import SQLiteStore
from checkpoint_ai.policy import ScenarioPolicy
from checkpoint_ai.runtime import AgentRegistry, SimpleAgent
from checkpoint_ai.tools import EchoTool, FileWriteTool, ToolPermission, ToolRegistry
from checkpoint_ai.webhook import WebhookSender
from checkpoint_ai.workflow import WorkflowEngine


class CheckpointAI:
    """Compatibility service facade for legacy runtime components."""

    def __init__(self, sqlite_path: str | Path | None = None, config: CheckpointAIConfig | None = None) -> None:
        """Create checkpoint_ai services and wire their dependencies."""

        self.config = config or CheckpointAIConfig()
        active_sqlite_path = sqlite_path if sqlite_path is not None else self.config.sqlite_path
        self.dry_run_enabled = self.config.dry_run
        self.event_bus = EventBus()
        self.audit_logger = AuditLogger()
        self.metrics = MetricsCollector()
        self.webhook_sender: WebhookSender | None = None
        self.ha_manager = None
        self.llm_provider = self.config.llm_provider
        self.response_cache = (
            LLMResponseCache(
                max_size=self.config.llm_cache_max_size,
                ttl_seconds=self.config.llm_cache_ttl_seconds,
            )
            if self.config.llm_cache_enabled
            else None
        )
        self.performance = PerformanceMonitor(
            slow_task_threshold_seconds=self.config.slow_task_threshold_seconds,
            event_bus=self.event_bus,
        )
        self.llm_provider.response_cache = self.response_cache
        self.llm_provider.performance_monitor = self.performance
        self.provider_registry = ProviderRegistry()
        self.provider_registry.register(self.llm_provider, default=True)
        self.event_bus.subscribe(self.audit_logger.log)
        self.event_bus.subscribe(self.metrics.record)
        self.agent_registry = AgentRegistry()
        self.tool_registry = ToolRegistry(permission=ToolPermission(), dry_run=self.dry_run_enabled)
        self.tool_registry.register(EchoTool())
        self.tool_registry.register(FileWriteTool(root_dir=Path.cwd()))
        self.policy_engine = PolicyEngine()
        self.scenario_policy = ScenarioPolicy()
        for policy in builtin_policies():
            self.policy_engine.add_policy(policy)
        self.notification_manager = NotificationManager()
        self.human_gate = HumanApprovalGate(event_bus=self.event_bus, notification_manager=self.notification_manager)
        self.human_gate.subscribe_to_cost_events()
        self.evaluation_runner = EvaluationRunner()
        self.evaluation_gate = EvaluationGate(self.evaluation_runner)
        self.store = SQLiteStore(active_sqlite_path)
        self.experiments = ExperimentLedger(active_sqlite_path)
        self.health_checker = HealthChecker(checkpoint_ai=self)
        self.business_lines = BusinessLineRegistry(self.store)
        self.cost_tracker = CostTracker(self.event_bus)
        self.memory = ContextManager(WorkingMemory(), PersistentMemory(self.store))
        self.workflow = WorkflowEngine(
            agent_registry=self.agent_registry,
            event_bus=self.event_bus,
            policy_engine=self.policy_engine,
            human_gate=self.human_gate,
            evaluation_gate=self.evaluation_gate,
            memory=self.memory,
            performance_monitor=self.performance,
            max_concurrency=self.config.max_concurrency,
        )
        self.agent_registry.register_agent_class(SimpleAgent)

    @classmethod
    def from_env(cls, env_path: str | Path = ".env") -> CheckpointAI:
        """Create a checkpoint_ai from .env and environment variables."""

        config = CheckpointAIConfig.from_env(env_path)
        return cls(sqlite_path=config.sqlite_path, config=config)

    def set_dry_run(self, enabled: bool) -> None:
        """Enable or disable dry run simulation."""

        self.dry_run_enabled = enabled
        self.tool_registry.dry_run = enabled
        if enabled:
            provider = DryRunProvider(model="dryrun")
            self.llm_provider = provider
            self.llm_provider.performance_monitor = self.performance
            self.llm_provider.response_cache = self.response_cache
            self.provider_registry.register(provider, default=True)
        else:
            self.llm_provider = self.config.llm_provider
            self.llm_provider.performance_monitor = self.performance
            self.llm_provider.response_cache = self.response_cache
            self.provider_registry.register(self.llm_provider, default=True)

    def dry_run(self) -> DryRunContext:
        """Return a context manager that temporarily enables dry run mode."""

        return DryRunContext(self)

    def create_business_line(
        self,
        name: str,
        config: BusinessLineConfig | None = None,
    ) -> BusinessLine:
        """Create a BusinessLine."""

        return self.business_lines.create(name=name, config=config)

    def get_business_line(self, business_line_id: str) -> BusinessLine:
        """Return one BusinessLine."""

        return self.business_lines.get(business_line_id)

    def list_business_lines(
        self,
        status: BusinessLineStatus | str | None = None,
    ) -> list[BusinessLine]:
        """List BusinessLines."""

        return self.business_lines.list(status=status)

    def set_cost_budget(
        self,
        provider: str,
        daily_budget: float,
        business_line_id: str = "default",
    ) -> None:
        """Set a cost budget for one provider and BusinessLine."""

        self.cost_tracker.set_budget(provider, daily_budget, business_line_id=business_line_id)

    def configure_webhooks(
        self,
        urls: list[str],
        transport: Callable[[str, dict[str, object], dict[str, str]], object] | None = None,
        max_retries: int = 2,
        headers: dict[str, str] | None = None,
    ) -> WebhookSender:
        """Configure outbound webhooks for supported checkpoint_ai events."""

        self.webhook_sender = WebhookSender(
            event_bus=self.event_bus,
            urls=urls,
            transport=transport,
            max_retries=max_retries,
            headers=headers,
        )
        return self.webhook_sender

    def create_run(self, user_request: str, business_line_id: str = "default") -> Run:
        """Create and persist a run."""

        run = Run(user_request=user_request, business_line_id=business_line_id)
        self.store.save_run(run)
        self.event_bus.emit(
            EventType.RUN_CREATED,
            {
                "run_id": run.id,
                "business_line_id": business_line_id,
                "user_request": user_request,
            },
        )
        return run

    def create_task(self, run: Run, name: str, agent_capability: str, input: object = None) -> Task:
        """Create and attach a task to a run."""

        task = Task(
            name=name,
            agent_capability=agent_capability,
            business_line_id=run.business_line_id,
            input=input,
        )
        run.add_task(task)
        self.store.save_run(run)
        self.event_bus.emit(
            EventType.TASK_CREATED,
            {
                "run_id": run.id,
                "task_id": task.id,
                "business_line_id": task.business_line_id,
            },
        )
        return task

    def recover_run(self, run_id: str) -> Run:
        """Rebuild a run from persistence and reset interrupted tasks."""

        row = self.store.load_run(run_id)
        run_state = RunState(row["state"])
        if run_state == RunState.RUNNING:
            run_state = RunState.PENDING
        run = Run(
            user_request=row["user_request"],
            business_line_id=row["business_line_id"],
            id=row["id"],
            state=run_state,
            metadata=row["metadata"],
        )
        for task_row in self.store.list_tasks(run_id):
            task_state = TaskState(task_row["state"])
            if task_state in {TaskState.RUNNING, TaskState.WAITING_APPROVAL, TaskState.RETRYING}:
                task_state = TaskState.PENDING
            task = Task(
                name=task_row["name"],
                agent_capability=task_row["agent_capability"],
                business_line_id=task_row["business_line_id"],
                input=task_row["input"],
                id=task_row["id"],
                run_id=task_row["run_id"],
                state=task_state,
                output_artifact_id=task_row["output_artifact_id"],
                error=task_row["error"],
                result=task_row["result"],
                metadata=task_row["metadata"],
            )
            run.tasks.append(task)
        self.event_bus.emit("run:recovered", {"run_id": run.id, "tasks": len(run.tasks)})
        return run

    def resume_run(self, run_id: str, exclude_completed: bool = True) -> Run:
        """Recover a run and continue from failed or unexecuted tasks."""

        run = self.recover_run(run_id)
        run.state = RunState.PENDING
        for task in run.tasks:
            if exclude_completed and task.state == TaskState.SUCCEEDED:
                continue
            if task.state in {
                TaskState.FAILED,
                TaskState.EVALUATION_FAILED,
                TaskState.CANCELLED,
                TaskState.SUCCEEDED,
            }:
                task.state = TaskState.PENDING
                task.error = None
                if not (exclude_completed and task.result is not None):
                    task.result = None
                    task.output_artifact_id = None
        self.event_bus.emit(
            "run:resumed",
            {"run_id": run.id, "exclude_completed": exclude_completed},
        )
        return self._execute_run(run)

    @overload
    def run(self, run: Run) -> Run:
        """Execute an existing run synchronously."""

    @overload
    def run(self, run: str, tasks: list[TaskSpec]) -> Coroutine[Any, Any, Run]:
        """Create and execute a run asynchronously."""

    def run(self, run: Run | str, tasks: list[TaskSpec] | None = None) -> Run | Coroutine[Any, Any, Run]:
        """Execute an existing Run, or return a coroutine for TaskSpec execution."""

        if isinstance(run, Run):
            return self._execute_run(run)
        if tasks is None:
            raise ValueError("CheckpointAI.run(description, tasks) requires tasks.")
        return self._run_from_specs(run, tasks)

    def _execute_run(self, run: Run) -> Run:
        """Execute and persist an existing run."""

        result = self.workflow.run(run)
        self._record_run_memory(result)
        self.store.save_run(result)
        return result

    async def _run_from_specs(self, description: str, tasks: list[TaskSpec]) -> Run:
        """Create a run, create tasks from specs, execute tools, and return the run."""

        run = self.create_run(description)
        for spec in tasks:
            task = spec.to_task()
            task.business_line_id = run.business_line_id
            run.add_task(task)
            self.event_bus.emit(
                EventType.TASK_CREATED,
                {
                    "run_id": run.id,
                    "task_id": task.id,
                    "business_line_id": task.business_line_id,
                },
            )
            for tool_name in spec.tool_names:
                result = await self.tool_registry.acall(tool_name, self._tool_arguments(tool_name, spec, task))
                task.input = result
        self.store.save_run(run)
        return self._execute_run(run)

    @staticmethod
    def _tool_arguments(tool_name: str, spec: TaskSpec, task: Task) -> dict[str, object]:
        """Build MVP tool arguments from a task spec."""

        if isinstance(spec.input, dict):
            arguments = dict(spec.input)
        else:
            arguments = {"input": spec.input if spec.input is not None else spec.description}
        if tool_name == "echo":
            arguments.setdefault("text", spec.description)
        if tool_name == "file_write":
            arguments.setdefault("content", spec.description)
        arguments.setdefault("task_id", task.id)
        return arguments

    def _record_run_memory(self, run: Run) -> None:
        """Record completed task results into context memory."""

        for task in run.tasks:
            if task.result is not None:
                self.memory.add(run.id, task.id, task.result)

    def report(self) -> dict[str, object]:
        """Return an in-memory operational report."""

        return {
            "events": len(self.event_bus.events),
            "audit_records": len(self.audit_logger.records),
            "metrics": self.metrics.get_summary(),
            "performance": self.performance.report(),
            "cache": self.response_cache.stats() if self.response_cache is not None else None,
        }

    def on(
        self,
        event_type_or_handler: str | EventType | Callable[[Event], None],
        handler: Callable[[Event], None] | None = None,
    ) -> None:
        """Subscribe to checkpoint_ai events."""

        self.event_bus.subscribe(event_type_or_handler, handler)
