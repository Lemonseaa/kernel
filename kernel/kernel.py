"""Kernel entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import overload

from kernel.control import HumanApprovalGate, PolicyEngine
from kernel.events import AuditLogger, EventBus
from kernel.models import Run, Task, TaskSpec
from kernel.persistence import SQLiteStore
from kernel.runtime import AgentRegistry, SimpleAgent
from kernel.tools import EchoTool, FileWriteTool, ToolPermission, ToolRegistry
from kernel.workflow import WorkflowEngine


class Kernel:
    """V0.1 Agent Workflow Kernel facade."""

    def __init__(self, sqlite_path: str | Path = "kernel.db") -> None:
        """Create kernel services and wire their dependencies."""

        self.event_bus = EventBus()
        self.audit_logger = AuditLogger()
        self.event_bus.subscribe(self.audit_logger.log)
        self.agent_registry = AgentRegistry()
        self.tool_registry = ToolRegistry(permission=ToolPermission())
        self.tool_registry.register(EchoTool())
        self.tool_registry.register(FileWriteTool(root_dir=Path.cwd()))
        self.policy_engine = PolicyEngine()
        self.human_gate = HumanApprovalGate()
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
        self.event_bus.emit("run.created", {"run_id": run.id, "user_request": user_request})
        return run

    def create_task(self, run: Run, name: str, agent_capability: str, input: object = None) -> Task:
        """Create and attach a task to a run."""

        task = Task(name=name, agent_capability=agent_capability, input=input)
        run.add_task(task)
        self.store.save_run(run)
        self.event_bus.emit("task.created", {"run_id": run.id, "task_id": task.id})
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
            self.event_bus.emit("task.created", {"run_id": run.id, "task_id": task.id})
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
        }
