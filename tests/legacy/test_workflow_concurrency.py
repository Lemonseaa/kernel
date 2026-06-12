"""Workflow concurrency tests."""

from __future__ import annotations

import threading
import time
import unittest

from loop_harness.models import Artifact, Run, Task, TaskState
from loop_harness.runtime import AgentRegistry, BaseAgent
from loop_harness.workflow import WorkflowEngine


class SleepAgent(BaseAgent):
    """Agent that sleeps to make concurrency observable."""

    name = "sleep"
    role = "Sleep"
    capabilities = {"sleep"}
    active_count = 0
    max_active_count = 0
    lock = threading.Lock()
    started: list[tuple[str, float]] = []
    finished: list[tuple[str, float]] = []

    def execute(self, task: Task) -> Artifact:
        """Sleep and return the task name."""

        with self.lock:
            type(self).active_count += 1
            type(self).max_active_count = max(type(self).max_active_count, type(self).active_count)
            type(self).started.append((task.id, time.perf_counter()))
        time.sleep(float(task.input or 0.1))
        with self.lock:
            type(self).finished.append((task.id, time.perf_counter()))
            type(self).active_count -= 1
        return Artifact(task_id=task.id, run_id=task.run_id or "", kind="text", content=task.name)


class WorkflowConcurrencyTest(unittest.TestCase):
    """Validate parallel task execution and dependency ordering."""

    def setUp(self) -> None:
        """Reset shared test agent state."""

        SleepAgent.active_count = 0
        SleepAgent.max_active_count = 0
        SleepAgent.started = []
        SleepAgent.finished = []

    def test_independent_tasks_run_in_parallel(self) -> None:
        registry = AgentRegistry()
        registry.register_agent_class(SleepAgent)
        engine = WorkflowEngine(agent_registry=registry, max_concurrency=3)
        run = Run(user_request="parallel")
        for index in range(3):
            run.add_task(Task(name=f"task-{index}", agent_capability="sleep", input=0.2))

        started_at = time.perf_counter()
        result = engine.run(run)
        elapsed = time.perf_counter() - started_at

        self.assertEqual(result.state.value, "succeeded")
        self.assertTrue(all(task.state == TaskState.SUCCEEDED for task in run.tasks))
        self.assertLess(elapsed, 0.45)

    def test_concurrency_limit_is_respected(self) -> None:
        registry = AgentRegistry()
        registry.register_agent_class(SleepAgent)
        engine = WorkflowEngine(agent_registry=registry, max_concurrency=2)
        run = Run(user_request="limited")
        for index in range(4):
            run.add_task(Task(name=f"task-{index}", agent_capability="sleep", input=0.1))

        engine.run(run)

        self.assertEqual(SleepAgent.max_active_count, 2)

    def test_task_dependencies_delay_downstream_tasks(self) -> None:
        registry = AgentRegistry()
        registry.register_agent_class(SleepAgent)
        engine = WorkflowEngine(agent_registry=registry, max_concurrency=2)
        run = Run(user_request="dependency")
        upstream = Task(name="upstream", agent_capability="sleep", input=0.15)
        downstream = Task(
            name="downstream",
            agent_capability="sleep",
            input=0.01,
            metadata={"depends_on": [upstream.id]},
        )
        run.add_task(upstream)
        run.add_task(downstream)

        engine.run(run)

        started = dict(SleepAgent.started)
        finished = dict(SleepAgent.finished)
        self.assertLess(finished[upstream.id], started[downstream.id])
        self.assertEqual(downstream.state, TaskState.SUCCEEDED)


if __name__ == "__main__":
    unittest.main()
