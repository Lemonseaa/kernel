"""Risk hardening tests for V0.2."""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from loop_harness import LoopHarness
from loop_harness.llm import LLMProvider, LLMRequest
from loop_harness.models import Task, TaskState
from loop_harness.runtime import LLMAgent
from loop_harness.tools import ToolPermission, ToolRegistry


class RiskHardeningTest(unittest.TestCase):
    """Validate remaining V0.2 risks are covered."""

    def test_llm_context_is_isolated_by_run_id(self) -> None:
        prompts: list[str] = []

        def transport(request: LLMRequest) -> str:
            prompts.append(request.prompt)
            return f"seen {len(prompts)}"

        with tempfile.TemporaryDirectory() as tmp:
            loop_harness = LoopHarness(sqlite_path=Path(tmp) / "loop_harness.db")
            run1 = loop_harness.create_run("run 1")
            run2 = loop_harness.create_run("run 2")
            task1 = Task(name="agent1", agent_capability="llm.generate", run_id=run1.id, input="说出你的名字")
            task2 = Task(name="agent2", agent_capability="llm.generate", run_id=run2.id, input="说出你的名字")
            loop_harness.memory.add(run1.id, "memory-agent1", {"output": "Agent1 private context"})
            loop_harness.memory.add(run2.id, "memory-agent2", {"output": "Agent2 private context"})
            agent = LLMAgent(provider=loop_harness.llm_provider, memory=loop_harness.memory, transport=transport)

            agent.execute(task1)
            agent.execute(task2)

            self.assertIn("Agent1 private context", prompts[0])
            self.assertNotIn("Agent2 private context", prompts[0])
            self.assertIn("Agent2 private context", prompts[1])
            self.assertNotIn("Agent1 private context", prompts[1])

    def test_recover_run_rebuilds_tasks_from_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
            loop_harness = LoopHarness(sqlite_path=db_path)
            run = loop_harness.create_run("recover")
            task = loop_harness.create_task(run, name="interrupted", agent_capability="simple.execute", input="resume")
            task.transition_to(TaskState.RUNNING)
            loop_harness.store.save_run(run)

            recovered = LoopHarness(sqlite_path=db_path).recover_run(run.id)

            self.assertEqual(recovered.id, run.id)
            self.assertEqual(len(recovered.tasks), 1)
            self.assertEqual(recovered.tasks[0].state, TaskState.PENDING)

    def test_recovered_run_can_continue_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
            loop_harness = LoopHarness(sqlite_path=db_path)
            run = loop_harness.create_run("recover execute")
            task = loop_harness.create_task(run, name="interrupted", agent_capability="simple.execute", input="resume")
            task.transition_to(TaskState.RUNNING)
            loop_harness.store.save_run(run)
            restored_loop_harness = LoopHarness(sqlite_path=db_path)

            result = restored_loop_harness.run(restored_loop_harness.recover_run(run.id))

            self.assertEqual(result.state.value, "succeeded")
            self.assertEqual(result.tasks[0].result, "resume")

    def test_resume_run_skips_completed_tasks_and_reruns_failed_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
            loop_harness = LoopHarness(sqlite_path=db_path)
            run = loop_harness.create_run("resume failed point")
            completed = loop_harness.create_task(run, name="completed", agent_capability="simple.execute", input="done")
            completed.transition_to(TaskState.RUNNING)
            completed.result = "finished result"
            completed.transition_to(TaskState.SUCCEEDED)
            failed = loop_harness.create_task(run, name="failed", agent_capability="simple.execute", input="retry me")
            failed.transition_to(TaskState.RUNNING)
            failed.error = "old error"
            failed.transition_to(TaskState.FAILED)
            loop_harness.store.save_run(run)

            resumed = LoopHarness(sqlite_path=db_path).resume_run(run.id, exclude_completed=True)

            self.assertEqual(resumed.tasks[0].state, TaskState.SUCCEEDED)
            self.assertEqual(resumed.tasks[0].result, "finished result")
            self.assertEqual(resumed.tasks[1].state, TaskState.SUCCEEDED)
            self.assertEqual(resumed.tasks[1].result, "retry me")

    def test_high_risk_tool_is_blocked_by_permission(self) -> None:
        registry = ToolRegistry(permission=ToolPermission(allowed_tools={"publish"}, risk_levels={"publish": "high"}))
        registry.register("publish", lambda: "published")

        with self.assertRaises(PermissionError):
            registry.call("publish", {})

    def test_provider_retries_transient_failures(self) -> None:
        attempts = 0

        def transport(_request: LLMRequest) -> str:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RuntimeError("temporary")
            return "ok"

        provider = RetryProvider(transport=transport, max_retries=1)

        response = provider.generate(LLMRequest(prompt="hello"))

        self.assertEqual(response.output, "ok")
        self.assertEqual(attempts, 2)

    def test_provider_timeout_is_reported(self) -> None:
        def transport(_request: LLMRequest) -> str:
            time.sleep(0.2)
            return "late"

        provider = RetryProvider(transport=transport, timeout_seconds=0.01)

        with self.assertRaises(TimeoutError):
            provider.generate(LLMRequest(prompt="hello"))


class RetryProvider(LLMProvider):
    """Test provider for retry and timeout behavior."""

    name = "retry-test"

    def _fallback_output(self, request: LLMRequest) -> str:
        """Return fallback output."""

        return request.prompt
