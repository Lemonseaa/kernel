"""Memory and context tests."""

from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from loop_harness import LoopHarness
from loop_harness.memory import ContextManager, PersistentMemory, WorkingMemory
from loop_harness.models import Task, TaskSpec
from loop_harness.persistence import SQLiteStore
from loop_harness.runtime import LLMAgent


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
            db_path = Path(tmp) / "loop_harness.db"
            memory = PersistentMemory(SQLiteStore(db_path))

            memory.add("run-1", "task-1", {"output": "saved"})

            reopened = PersistentMemory(SQLiteStore(db_path))
            context = reopened.get_context("run-1")

            self.assertEqual(context[0]["content"]["output"], "saved")

    def test_context_manager_merges_working_and_persistent_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(Path(tmp) / "loop_harness.db")
            manager = ContextManager(WorkingMemory(), PersistentMemory(store))

            manager.add("run-1", "task-1", {"output": "shared"})
            context_text = manager.build_prompt_context("run-1")

            self.assertIn("task-1", context_text)
            self.assertIn("shared", context_text)

    def test_business_line_context_survives_runs_and_stays_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
            manager = ContextManager(WorkingMemory(), PersistentMemory(SQLiteStore(db_path)))

            manager.add_shared(
                business_line_id="bl-a",
                run_id="run-1",
                task_id="task-1",
                content={"lesson": "标题太短，下次补充场景"},
                kind="evaluation_feedback",
            )
            manager.add_shared(
                business_line_id="bl-b",
                run_id="run-2",
                task_id="task-2",
                content={"lesson": "另一个业务线的经验"},
                kind="evaluation_feedback",
            )

            reopened = ContextManager(WorkingMemory(), PersistentMemory(SQLiteStore(db_path)))
            bl_a_text = reopened.build_business_line_prompt_context(
                "bl-a",
                kind="evaluation_feedback",
            )
            bl_b_items = reopened.get_business_line_context(
                "bl-b",
                kind="evaluation_feedback",
            )

            self.assertIn("标题太短", bl_a_text)
            self.assertNotIn("另一个业务线", bl_a_text)
            self.assertEqual(bl_b_items[0]["run_id"], "run-2")

    def test_llm_agent_includes_memory_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop_harness = LoopHarness(sqlite_path=Path(tmp) / "loop_harness.db")
            loop_harness.memory.add("run-1", "task-1", {"output": "previous result"})
            agent = LLMAgent(
                provider=loop_harness.llm_provider,
                memory=loop_harness.memory,
                transport=lambda request: request.prompt,
            )
            task = Task(name="next", agent_capability="llm.generate", input="continue")
            task.run_id = "run-1"

            artifact = agent.execute(task)

            self.assertIn("previous result", artifact.content["output"])
            self.assertIn("continue", artifact.content["output"])

    def test_llm_agent_includes_business_line_feedback_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop_harness = LoopHarness(sqlite_path=Path(tmp) / "loop_harness.db")
            loop_harness.memory.add_shared(
                business_line_id="bl-a",
                run_id="old-run",
                task_id="old-task",
                content={"suggestions": ["避免标题过短"]},
                kind="evaluation_feedback",
            )
            agent = LLMAgent(
                provider=loop_harness.llm_provider,
                memory=loop_harness.memory,
                transport=lambda request: request.prompt,
            )
            task = Task(
                name="next",
                agent_capability="llm.generate",
                business_line_id="bl-a",
                input="rewrite",
            )
            task.run_id = "new-run"

            artifact = agent.execute(task)

            self.assertIn("避免标题过短", artifact.content["output"])
            self.assertIn("rewrite", artifact.content["output"])

    def test_loop_harness_run_records_task_results_in_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop_harness = LoopHarness(sqlite_path=Path(tmp) / "loop_harness.db")

            async def run_loop_harness() -> object:
                return await loop_harness.run(
                    "context workflow",
                    [TaskSpec(description="first"), TaskSpec(description="second")],
                )

            run = asyncio.run(run_loop_harness())
            context = loop_harness.memory.get_context(run.id)

            self.assertEqual(len(context), 2)
            self.assertEqual(context[0]["content"], "first")
            self.assertEqual(context[1]["content"], "second")
