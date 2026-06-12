"""Loop Harness integration tests."""

from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from loop_harness import LoopHarness
from loop_harness.models import Artifact, Task, TaskSpec, TaskState
from loop_harness.persistence import SQLiteStore
from loop_harness.runtime import BaseAgent, SimpleAgent
from loop_harness.tools import EchoTool, FileWriteTool


class WriterAgent(BaseAgent):
    """Integration test agent."""

    name = "writer"
    role = "Writer"
    capabilities = {"content.write"}

    def execute(self, task: Task) -> Artifact:
        """Create a simple artifact."""

        return Artifact(task_id=task.id, run_id=task.run_id or "", kind="text", content="written")


class IntegrationTest(unittest.TestCase):
    """Validate the loop_harness runtime happy path."""

    def test_loop_harness_runs_workflow_and_persists_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
            loop_harness = LoopHarness(sqlite_path=db_path)
            loop_harness.agent_registry.register_agent_class(WriterAgent)

            run = loop_harness.create_run("write content")
            task = loop_harness.create_task(run, name="write", agent_capability="content.write")
            result = loop_harness.run(run)

            loaded_run = loop_harness.store.load_run(run.id)
            loaded_task = loop_harness.store.load_task(task.id)

            self.assertEqual(result.state.value, "succeeded")
            self.assertEqual(loaded_run["state"], "succeeded")
            self.assertEqual(loaded_task["state"], TaskState.SUCCEEDED.value)
            self.assertTrue(loop_harness.event_bus.events)

    def test_sqlite_store_creates_parent_directory_and_handles_non_json_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "nested" / "loop_harness.db"
            store = SQLiteStore(db_path)
            task = Task(name="write", agent_capability="content.write", input={"path": Path(tmp)})

            store.save_task(task)
            loaded_task = store.load_task(task.id)

            self.assertEqual(loaded_task["state"], TaskState.PENDING.value)
            self.assertIn("path", loaded_task["input"])

    def test_sqlite_store_lists_runs_and_tasks_for_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
            loop_harness = LoopHarness(sqlite_path=db_path)

            async def run_loop_harness() -> object:
                return await loop_harness.run("恢复测试", [TaskSpec(description="hello")])

            run = asyncio.run(run_loop_harness())
            store = SQLiteStore(db_path)

            runs = store.list_runs()
            tasks = store.list_tasks(run.id)

            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0]["id"], run.id)
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0]["run_id"], run.id)

    def test_loop_harness_async_run_executes_task_specs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop_harness = LoopHarness(sqlite_path=Path(tmp) / "loop_harness.db")

            async def run_loop_harness() -> object:
                return await loop_harness.run(
                    "测试Run",
                    [TaskSpec(description="说hello"), TaskSpec(description="再说一次")],
                )

            run = asyncio.run(run_loop_harness())

            self.assertEqual(run.state.value, "succeeded")
            self.assertEqual(len(run.tasks), 2)
            self.assertEqual(run.tasks[0].result, "说hello")
            self.assertEqual(run.tasks[1].result, "再说一次")

    def test_simple_agent_can_call_builtin_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "out.txt"
            loop_harness = LoopHarness(sqlite_path=Path(tmp) / "loop_harness.db")
            loop_harness.tool_registry.register(EchoTool())
            loop_harness.tool_registry.register(FileWriteTool(root_dir=tmp))

            async def run_loop_harness() -> object:
                return await loop_harness.run(
                    "工具测试",
                    [
                        TaskSpec(description="hello", tool_names=["echo"]),
                        TaskSpec(
                            description="写文件",
                            tool_names=["file_write"],
                            input={"path": "out.txt", "content": "saved"},
                        ),
                    ],
                )

            run = asyncio.run(run_loop_harness())

            self.assertEqual(run.state.value, "succeeded")
            self.assertEqual(run.tasks[0].result, "hello")
            self.assertEqual(output_path.read_text(encoding="utf-8"), "saved")
            self.assertIn("out.txt", run.tasks[1].result["path"])

    def test_loop_harness_on_subscribes_to_typed_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop_harness = LoopHarness(sqlite_path=Path(tmp) / "loop_harness.db")
            events = []
            loop_harness.on("task:completed", lambda event: events.append(event))

            async def run_loop_harness() -> object:
                return await loop_harness.run("测试", [TaskSpec(description="hello")])

            run = asyncio.run(run_loop_harness())

            self.assertEqual(run.state.value, "succeeded")
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].payload["task_id"], run.tasks[0].id)

    def test_simple_agent_is_directly_executable(self) -> None:
        agent = SimpleAgent()
        task = Task(name="say", agent_capability="simple.execute", input="hello")

        artifact = agent.execute(task)

        self.assertEqual(artifact.content, "hello")
