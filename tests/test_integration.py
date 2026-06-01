"""Kernel integration tests."""

from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from kernel import Kernel
from kernel.models import Artifact, Task, TaskSpec, TaskState
from kernel.persistence import SQLiteStore
from kernel.runtime import BaseAgent, SimpleAgent
from kernel.tools import EchoTool, FileWriteTool


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

    def test_kernel_async_run_executes_task_specs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            kernel = Kernel(sqlite_path=Path(tmp) / "kernel.db")

            async def run_kernel() -> object:
                return await kernel.run(
                    "测试Run",
                    [TaskSpec(description="说hello"), TaskSpec(description="再说一次")],
                )

            run = asyncio.run(run_kernel())

            self.assertEqual(run.state.value, "succeeded")
            self.assertEqual(len(run.tasks), 2)
            self.assertEqual(run.tasks[0].result, "说hello")
            self.assertEqual(run.tasks[1].result, "再说一次")

    def test_simple_agent_can_call_builtin_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "out.txt"
            kernel = Kernel(sqlite_path=Path(tmp) / "kernel.db")
            kernel.tool_registry.register(EchoTool())
            kernel.tool_registry.register(FileWriteTool(root_dir=tmp))

            async def run_kernel() -> object:
                return await kernel.run(
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

            run = asyncio.run(run_kernel())

            self.assertEqual(run.state.value, "succeeded")
            self.assertEqual(run.tasks[0].result, "hello")
            self.assertEqual(output_path.read_text(encoding="utf-8"), "saved")
            self.assertIn("out.txt", run.tasks[1].result["path"])

    def test_simple_agent_is_directly_executable(self) -> None:
        agent = SimpleAgent()
        task = Task(name="say", agent_capability="simple.execute", input="hello")

        artifact = agent.execute(task)

        self.assertEqual(artifact.content, "hello")
