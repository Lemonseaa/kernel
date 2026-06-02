"""Dry run mode tests."""

from __future__ import annotations

import asyncio
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from kernel import Kernel
from opc_os.cli import main
from opc_os.config import KernelConfig
from opc_os.dryrun import DryRunProvider, DryRunValidator
from opc_os.llm import LLMRequest
from opc_os.models import TaskSpec
from opc_os.tools import FileWriteTool, ToolPermission, ToolRegistry


class DryRunTest(unittest.TestCase):
    """Validate dry run simulation behavior."""

    def test_dryrun_provider_returns_simulated_llm_response(self) -> None:
        provider = DryRunProvider(model="dry-model")

        response = provider.generate(LLMRequest(prompt="写一篇内容"))

        self.assertEqual(response.provider, "dryrun")
        self.assertIn("写一篇内容", response.output)
        self.assertTrue(response.metadata["dry_run"])

    def test_tool_registry_simulates_tool_calls_in_dryrun(self) -> None:
        registry = ToolRegistry(permission=ToolPermission(allowed_tools={"dangerous"}), dry_run=True)
        registry.register("dangerous", lambda path: Path(path).write_text("changed", encoding="utf-8"))

        result = registry.call("dangerous", {"path": "real.txt"})

        self.assertTrue(result["dry_run"])
        self.assertEqual(result["tool"], "dangerous")
        self.assertEqual(result["arguments"]["path"], "real.txt")

    def test_kernel_dryrun_does_not_execute_file_write_tool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "out.txt"
            kernel = Kernel(sqlite_path=Path(tmp) / "kernel.db", config=KernelConfig(dry_run=True))
            kernel.tool_registry.register(FileWriteTool(root_dir=tmp))

            async def run_kernel() -> object:
                return await kernel.run(
                    "dryrun file write",
                    [
                        TaskSpec(
                            description="写文件",
                            tool_names=["file_write"],
                            input={"path": "out.txt", "content": "should not write"},
                        )
                    ],
                )

            run = asyncio.run(run_kernel())

            self.assertEqual(run.state.value, "succeeded")
            self.assertFalse(output_path.exists())
            self.assertTrue(run.tasks[0].result["dry_run"])

    def test_dryrun_context_temporarily_enables_simulation(self) -> None:
        kernel = Kernel()

        self.assertFalse(kernel.dry_run_enabled)
        with kernel.dry_run():
            self.assertTrue(kernel.dry_run_enabled)
            self.assertTrue(kernel.tool_registry.dry_run)
        self.assertFalse(kernel.dry_run_enabled)
        self.assertFalse(kernel.tool_registry.dry_run)

    def test_cli_dryrun_command_prints_preview(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = main(["dryrun", "--task", "预演任务"])

        self.assertEqual(exit_code, 0)
        self.assertIn("dry_run", stdout.getvalue())
        self.assertTrue(DryRunValidator().validate_task_specs([TaskSpec(description="预演任务")]).valid)
