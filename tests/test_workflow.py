"""Workflow, tools, policy, and event tests."""

from __future__ import annotations

import unittest

from kernel.control import HumanApprovalGate, PolicyDecision, PolicyEngine
from kernel.events import EventBus
from kernel.models import Artifact, Run, Task, TaskState
from kernel.runtime import AgentRegistry, BaseAgent
from kernel.tools import EchoTool, ToolPermission, ToolRegistry
from kernel.workflow import TaskExecutor, WorkflowEngine


class EchoAgent(BaseAgent):
    """Test agent that returns a text artifact."""

    name = "echo"
    role = "Echo"
    capabilities = {"echo"}

    def execute(self, task: Task) -> Artifact:
        """Return task input as artifact content."""

        return Artifact(task_id=task.id, run_id=task.run_id or "", kind="text", content=task.input)


class WorkflowComponentTest(unittest.TestCase):
    """Validate workflow supporting components."""

    def test_tool_registry_checks_permission_before_call(self) -> None:
        registry = ToolRegistry(permission=ToolPermission(allowed_tools={"echo"}))
        registry.register("echo", lambda text: text.upper())

        self.assertEqual(registry.call("echo", {"text": "ok"}), "OK")

        with self.assertRaises(PermissionError):
            registry.call("missing", {})

    def test_tool_registry_supports_basetool_async_call(self) -> None:
        registry = ToolRegistry(permission=ToolPermission(allowed_tools={"echo"}))
        registry.register(EchoTool())

        result = registry.call("echo", {"text": "ok"})

        self.assertEqual(result, "ok")

    def test_policy_and_human_gate(self) -> None:
        policy = PolicyEngine(high_risk_keywords={"deploy"})
        gate = HumanApprovalGate(auto_approve=False)
        decision = policy.evaluate_action("deploy production")

        self.assertTrue(decision.requires_approval)
        self.assertEqual(decision.decision, PolicyDecision.REVIEW)
        self.assertFalse(gate.request_approval(decision))

    def test_executor_runs_agent_and_emits_events(self) -> None:
        bus = EventBus()
        executor = TaskExecutor(event_bus=bus)
        task = Task(name="echo", agent_capability="echo", input="hello")
        agent = EchoAgent()

        artifact = executor.execute(task, agent)

        self.assertEqual(task.state, TaskState.SUCCEEDED)
        self.assertEqual(artifact.content, "hello")
        self.assertTrue(bus.events)

    def test_workflow_schedule_is_idempotent(self) -> None:
        registry = AgentRegistry()
        registry.register_agent_class(EchoAgent)
        engine = WorkflowEngine(agent_registry=registry)
        run = Run(user_request="echo")
        task = Task(name="echo", agent_capability="echo", input="hello")
        run.add_task(task)

        engine.schedule(run)
        engine.schedule(run)
        result = engine.run(run)

        self.assertEqual(result.state.value, "succeeded")
        self.assertEqual(task.state, TaskState.SUCCEEDED)

    def test_event_bus_isolates_subscriber_failures(self) -> None:
        bus = EventBus()

        def broken_handler(_event: object) -> None:
            raise RuntimeError("audit sink unavailable")

        bus.subscribe(broken_handler)
        event = bus.emit("task.started", {"task_id": "task-1"})

        self.assertEqual(event.type, "task.started")
        self.assertEqual(len(bus.events), 1)
        self.assertEqual(len(bus.subscriber_errors), 1)
