"""Kernel integration tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from kernel import Kernel
from kernel.models import Artifact, Task, TaskState
from kernel.persistence import SQLiteStore
from kernel.runtime import BaseAgent


class WriterAgent(BaseAgent):
    """Integration test agent."""

    name = "writer"
    role = "Writer"
    capabilities = {"content.write"}

    def execute(self, task: Task) -> Artifact:
        """Create a simple artifact."""

        return Artifact(task_id=task.id, run_id=task.run_id or "", kind="text", content="written")


class IntegrationTest(unittest.TestCase):
    """Validate the V0.1 kernel happy path."""

    def test_kernel_runs_workflow_and_persists_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "kernel.db"
            kernel = Kernel(sqlite_path=db_path)
            kernel.agent_registry.register_agent_class(WriterAgent)

            run = kernel.create_run("write content")
            task = kernel.create_task(run, name="write", agent_capability="content.write")
            result = kernel.run(run)

            loaded_run = kernel.store.load_run(run.id)
            loaded_task = kernel.store.load_task(task.id)

            self.assertEqual(result.state.value, "succeeded")
            self.assertEqual(loaded_run["state"], "succeeded")
            self.assertEqual(loaded_task["state"], TaskState.SUCCEEDED.value)
            self.assertTrue(kernel.event_bus.events)

    def test_sqlite_store_creates_parent_directory_and_handles_non_json_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "nested" / "kernel.db"
            store = SQLiteStore(db_path)
            task = Task(name="write", agent_capability="content.write", input={"path": Path(tmp)})

            store.save_task(task)
            loaded_task = store.load_task(task.id)

            self.assertEqual(loaded_task["state"], TaskState.PENDING.value)
            self.assertIn("path", loaded_task["input"])
