"""V2.6 CLI and report tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.prompt import PromptSlot, PromptVersionStore


class V26CliReportTest(unittest.TestCase):
    """Validate human-readable V2.6 commands and reports."""

    def test_scenario_create_list_show_and_adapter_run_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v26.db"

            create = self._run(
                db_path,
                "scenario",
                "create",
                "--id",
                "scenario-1",
                "--name",
                "Quant demo",
                "--description",
                "CLI scenario",
                "--adapter",
                "dummy_stock_signal",
                "--business-line-id",
                "quant",
            )
            listing = self._run(db_path, "scenario", "list")
            detail = self._run(db_path, "scenario", "show", "scenario-1")
            adapter = self._run(
                db_path,
                "adapter",
                "run",
                "--scenario-id",
                "scenario-1",
                "--task",
                "analyze_signal",
                "--context-json",
                '{"symbol": "AAPL"}',
            )
            report = self._run(db_path, "report", "latest")

        self.assertIn("Scenario created", create.stdout)
        self.assertIn("business_line_id: quant", create.stdout)
        self.assertIn("scenario-1", listing.stdout)
        self.assertIn("quant", listing.stdout)
        self.assertIn("Quant demo", detail.stdout)
        self.assertIn("business_line_id: quant", detail.stdout)
        self.assertIn("Adapter Run Report", adapter.stdout)
        self.assertIn("signal_quality", adapter.stdout)
        self.assertIn("Run Report", report.stdout)
        self.assertIn("为什么运行", report.stdout)
        self.assertIn("发生了什么", report.stdout)

    def test_prompt_history_rollback_and_proposal_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v26.db"
            versions = PromptVersionStore(db_path)
            versions.save_version(
                scenario_id="scenario-1",
                agent_id="writer",
                slots={PromptSlot.OUTPUT_FORMAT: "输出自然语言。"},
                reason="baseline",
            )
            versions.save_version(
                scenario_id="scenario-1",
                agent_id="writer",
                slots={PromptSlot.OUTPUT_FORMAT: "输出 JSON。"},
                reason="structured",
            )

            history_before = self._run(
                db_path,
                "prompt",
                "history",
                "--scenario-id",
                "scenario-1",
                "--agent-id",
                "writer",
            )
            rollback = self._run(
                db_path,
                "prompt",
                "rollback",
                "--scenario-id",
                "scenario-1",
                "--agent-id",
                "writer",
                "--reason",
                "JSON格式不稳定",
            )
            proposal_create = self._run(
                db_path,
                "proposal",
                "create",
                "--scenario-id",
                "scenario-1",
                "--agent-id",
                "writer",
                "--slot",
                "output_format",
                "--operation",
                "replace",
                "--before",
                "输出自然语言。",
                "--after",
                "输出 JSON。",
                "--reason",
                "结构化输出便于评估。",
                "--expected-metric",
                "signal_quality",
            )
            proposal_id = self._last_token(proposal_create.stdout)
            proposal_list = self._run(db_path, "proposal", "list")
            approve = self._run(db_path, "proposal", "approve", proposal_id)
            reject = self._run(db_path, "proposal", "reject", proposal_id)

        self.assertIn("Prompt History", history_before.stdout)
        self.assertIn("structured", history_before.stdout)
        self.assertIn("Rolled back", rollback.stdout)
        self.assertIn("Proposal created", proposal_create.stdout)
        self.assertIn("结构化输出", proposal_list.stdout)
        self.assertIn("approved", approve.stdout)
        self.assertIn("rejected", reject.stdout)

    def test_shadow_run_status_and_proposal_report_are_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v26.db"
            self._run(
                db_path,
                "scenario",
                "create",
                "--id",
                "scenario-1",
                "--name",
                "Quant demo",
                "--description",
                "CLI scenario",
                "--adapter",
                "dummy_stock_signal",
            )
            proposal_create = self._run(
                db_path,
                "proposal",
                "create",
                "--scenario-id",
                "scenario-1",
                "--agent-id",
                "writer",
                "--slot",
                "output_format",
                "--operation",
                "replace",
                "--before",
                "输出自然语言。",
                "--after",
                "输出 JSON。",
                "--reason",
                "结构化输出便于评估。",
                "--expected-metric",
                "signal_quality",
            )
            proposal_id = self._last_token(proposal_create.stdout)

            shadow = self._run(db_path, "shadow", "run", proposal_id, "--task", "analyze_signal")
            status = self._run(db_path, "shadow", "status", proposal_id)
            report = self._run(db_path, "report", "proposal", proposal_id)

        self.assertIn("Shadow Result", shadow.stdout)
        self.assertIn("shadow result", shadow.stdout.lower())
        self.assertIn("Shadow Status", status.stdout)
        self.assertIn("metric_diff", status.stdout)
        self.assertIn("Proposal Report", report.stdout)
        self.assertIn("比baseline好了还是差了", report.stdout)

    def test_report_run_includes_input_output_metrics_and_value_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v26.db"
            self._run(
                db_path,
                "scenario",
                "create",
                "--id",
                "scenario-1",
                "--name",
                "Quant demo",
                "--description",
                "CLI scenario",
                "--adapter",
                "dummy_stock_signal",
            )
            adapter = self._run(
                db_path,
                "adapter",
                "run",
                "--scenario-id",
                "scenario-1",
                "--task",
                "analyze_signal",
                "--context-json",
                '{"symbol": "MSFT"}',
            )
            run_id = self._extract_run_id(adapter.stdout)
            report = self._run(db_path, "report", "run", run_id)

        self.assertIn("Run Report", report.stdout)
        self.assertIn("scenario_id: scenario-1", report.stdout)
        self.assertIn("任务类型: analyze_signal", report.stdout)
        self.assertIn("输入摘要", report.stdout)
        self.assertIn("输出摘要", report.stdout)
        self.assertIn("metrics", report.stdout)
        self.assertIn("value_summary", report.stdout)

    @staticmethod
    def _run(db_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ["./checkpointai", "--db", str(db_path), *args],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr or result.stdout)
        return result

    @staticmethod
    def _last_token(output: str) -> str:
        return output.strip().split()[-1]

    @staticmethod
    def _extract_run_id(output: str) -> str:
        for line in output.splitlines():
            if line.startswith("run_id:"):
                return line.split(":", 1)[1].strip()
        raise AssertionError(f"run_id not found in output:\n{output}")


if __name__ == "__main__":
    unittest.main()
