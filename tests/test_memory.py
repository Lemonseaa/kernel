"""Memory and context tests."""

from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from kernel import Kernel
from kernel.memory import ContextManager, PersistentMemory, WorkingMemory
from kernel.models import Task, TaskSpec
from kernel.persistence import SQLiteStore
from kernel.runtime import LLMAgent


class MemoryContextTest(unittest.TestCase):
    """Validate working memory, persistent memory, context manager, and LLM integration."""

    def test_working_memory_stores_recent_context(self) -> None:
        memory = WorkingMemory(max_items=2)

        memory.add("run-1", "task-1", {"output": "first"})
        memory.add("run-1", "task-2", {"output": "second"})
        memory.add("run-1", "task-3", {"output": "third"})

        context = memory.get_context("run-1")

        self.assertEqual(len(context), 2)
        self.assertEqual(context[0]["task_id"], "task-2")
        self.assertEqual(context[1]["content"]["output"], "third")

    def test_persistent_memory_survives_store_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "kernel.db"
            memory = PersistentMemory(SQLiteStore(db_path))

            memory.add("run-1", "task-1", {"output": "saved"})

            reopened = PersistentMemory(SQLiteStore(db_path))
            context = reopened.get_context("run-1")

            self.assertEqual(context[0]["content"]["output"], "saved")

    def test_context_manager_merges_working_and_persistent_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(Path(tmp) / "kernel.db")
            manager = ContextManager(WorkingMemory(), PersistentMemory(store))

            manager.add("run-1", "task-1", {"output": "shared"})
            context_text = manager.build_prompt_context("run-1")

            self.assertIn("task-1", context_text)
            self.assertIn("shared", context_text)

    def test_llm_agent_includes_memory_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            kernel = Kernel(sqlite_path=Path(tmp) / "kernel.db")
            kernel.memory.add("run-1", "task-1", {"output": "previous result"})
            agent = LLMAgent(
                provider=kernel.llm_provider,
                memory=kernel.memory,
                transport=lambda request: request.prompt,
            )
            task = Task(name="next", agent_capability="llm.generate", input="continue")
            task.run_id = "run-1"

            artifact = agent.execute(task)

            self.assertIn("previous result", artifact.content["output"])
            self.assertIn("continue", artifact.content["output"])

    def test_kernel_run_records_task_results_in_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            kernel = Kernel(sqlite_path=Path(tmp) / "kernel.db")

            async def run_kernel() -> object:
                return await kernel.run(
                    "context workflow",
                    [TaskSpec(description="first"), TaskSpec(description="second")],
                )

            run = asyncio.run(run_kernel())
            context = kernel.memory.get_context(run.id)

            self.assertEqual(len(context), 2)
            self.assertEqual(context[0]["content"], "first")
            self.assertEqual(context[1]["content"], "second")
