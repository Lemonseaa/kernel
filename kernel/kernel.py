"""Kernel entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, overload

from kernel.control import HumanApprovalGate, PolicyEngine
from kernel.events import AuditLogger, Event, EventBus, EventType
from kernel.models import Run, Task, TaskSpec
from kernel.observability import MetricsCollector
from kernel.persistence import SQLiteStore
from kernel.runtime import AgentRegistry, SimpleAgent
from kernel.scheduler import Job, JobType, Scheduler
from kernel.tools import EchoTool, FileWriteTool, ToolPermission, ToolRegistry
from kernel.workflow import WorkflowEngine


class Kernel:
    """V0.1 Agent Workflow Kernel facade."""

    def __init__(self, sqlite_path: str | Path = "kernel.db") -> None:
        """Create kernel services and wire their dependencies."""

        self.event_bus = EventBus()
        self.audit_logger = AuditLogger()
        self.metrics = MetricsCollector()
        self.scheduler = Scheduler()
        self.event_bus.subscribe(self.audit_logger.log)
        self.event_bus.subscribe(self.metrics.record)
        self.agent_registry = AgentRegistry()
        self.tool_registry = ToolRegistry(permission=ToolPermission())
        self.tool_registry.register(EchoTool())
        self.tool_registry.register(FileWriteTool(root_dir=Path.cwd()))
        self.policy_engine = PolicyEngine()
        self.human_gate = HumanApprovalGate(event_bus=self.event_bus)
        self.store = SQLiteStore(sqlite_path)
        self.workflow = WorkflowEngine(
            agent_registry=self.agent_registry,
            event_bus=self.event_bus,
            policy_engine=self.policy_engine,
            human_gate=self.human_gate,
        )
        self.agent_registry.register_agent_class(SimpleAgent)

    def create_run(self, user_request: str) -> Run:
        """Create and persist a run."""

        run = Run(user_request=user_request)
        self.store.save_run(run)
        self.event_bus.emit(EventType.RUN_CREATED, {"run_id": run.id, "user_request": user_request})
        return run

    def create_task(self, run: Run, name: str, agent_capability: str, input: object = None) -> Task:
        """Create and attach a task to a run."""

        task = Task(name=name, agent_capability=agent_capability, input=input)
        run.add_task(task)
        self.store.save_run(run)
        self.event_bus.emit(EventType.TASK_CREATED, {"run_id": run.id, "task_id": task.id})
        return task

    @overload
    def run(self, run: Run) -> Run:
        """Execute an existing run synchronously."""

    @overload
    def run(self, run: str, tasks: list[TaskSpec]) -> object:
        """Create and execute a run asynchronously."""

    def run(self, run: Run | str, tasks: list[TaskSpec] | None = None) -> Run | object:
        """Execute an existing Run, or return a coroutine for TaskSpec execution."""

        if isinstance(run, Run):
            return self._execute_run(run)
        if tasks is None:
            raise ValueError("Kernel.run(description, tasks) requires tasks.")
        return self._run_from_specs(run, tasks)

    def _execute_run(self, run: Run) -> Run:
        """Execute and persist an existing run."""

        result = self.workflow.run(run)
        self.store.save_run(result)
        return result

    async def _run_from_specs(self, description: str, tasks: list[TaskSpec]) -> Run:
        """Create a run, create tasks from specs, execute tools, and return the run."""

        run = self.create_run(description)
        for spec in tasks:
            task = spec.to_task()
            run.add_task(task)
            self.event_bus.emit(EventType.TASK_CREATED, {"run_id": run.id, "task_id": task.id})
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

    def report(self) -> dict[str, object]:
        """Return an in-memory operational report."""

        return {
            "events": len(self.event_bus.events),
            "audit_records": len(self.audit_logger.records),
            "metrics": self.metrics.get_summary(),
        }

    def on(
        self,
        event_type_or_handler: str | EventType | Callable[[Event], None],
        handler: Callable[[Event], None] | None = None,
    ) -> None:
        """Subscribe to kernel events."""

        self.event_bus.subscribe(event_type_or_handler, handler)

    def schedule(
        self,
        name: str,
        tasks: list[TaskSpec],
        interval_seconds: int | None = None,
        cron: str | None = None,
    ) -> Job:
        """Schedule a workflow for later execution."""

        if interval_seconds is not None:
            job_type = JobType.INTERVAL
        elif cron is not None:
            job_type = JobType.CRON
        else:
            raise ValueError("schedule requires interval_seconds or cron.")
        job = Job(
            name=name,
            job_type=job_type,
            task_specs=tasks,
            interval_seconds=interval_seconds,
            cron=cron,
        )
        self.scheduler.add_job(job)
        self.event_bus.emit("schedule:created", {"job_id": job.id, "name": job.name})
        return job

    async def run_scheduled(self) -> int:
        """Run due scheduled jobs."""

        async def run_job(job: Job) -> None:
            await self.run(job.user_request or job.name, job.task_specs)

        count = 0
        for job in self.scheduler.due_jobs():
            await run_job(job)
            job.mark_ran()
            count += 1
        return count
