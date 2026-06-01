"""Kernel entrypoint."""

from __future__ import annotations

from pathlib import Path

from kernel.control import HumanApprovalGate, PolicyEngine
from kernel.events import AuditLogger, EventBus
from kernel.models import Run, Task
from kernel.persistence import SQLiteStore
from kernel.runtime import AgentRegistry
from kernel.tools import ToolPermission, ToolRegistry
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
        self.policy_engine = PolicyEngine()
        self.human_gate = HumanApprovalGate()
        self.store = SQLiteStore(sqlite_path)
        self.workflow = WorkflowEngine(
            agent_registry=self.agent_registry,
            event_bus=self.event_bus,
            policy_engine=self.policy_engine,
            human_gate=self.human_gate,
        )

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

    def run(self, run: Run) -> Run:
        """Execute a run and persist final state."""

        result = self.workflow.run(run)
        self.store.save_run(result)
        return result

    def report(self) -> dict[str, object]:
        """Return an in-memory operational report."""

        return {
            "events": len(self.event_bus.events),
            "audit_records": len(self.audit_logger.records),
        }
