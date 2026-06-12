"""V5.1 console read model tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from loop_harness.adapter import AgentRunRequest, AgentRunResult
from loop_harness.console import ConsoleReadModel
from loop_harness.logs import RawLogStore, SummaryLogStore
from loop_harness.loop import AgentLoopStore, LoopRun, LoopStatus
from loop_harness.prompt import (
    PromptPatch,
    PromptProposal,
    PromptProposalStatus,
    PromptProposalStore,
    PromptSlot,
)
from loop_harness.scenario import Scenario, ScenarioStatus, ScenarioStore
from tests.helpers import project_root


class V51ConsoleReadModelTest(unittest.TestCase):
    """Validate the human-facing V5 console snapshot."""

    def test_console_snapshot_is_scope_aware_and_human_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "console.db"
            scenarios = ScenarioStore(db_path)
            scenarios.save(
                Scenario(
                    id="quant",
                    name="Quant",
                    description="Quant research",
                    adapter_type="quant_research_demo",
                    metadata={"domain_tags": ["quant", "backtest"]},
                )
            )
            scenarios.save(
                Scenario(
                    id="content",
                    name="Content",
                    description="Content growth",
                    adapter_type="dummy_stock_signal",
                    status=ScenarioStatus.ARCHIVED,
                    metadata={"domain_tags": ["content"]},
                )
            )
            raw_logs = RawLogStore(db_path)
            summary_logs = SummaryLogStore(db_path)
            quant_result = AgentRunResult(
                scenario_id="quant",
                task="backtest",
                answer="result",
                metrics={"sharpe": 1.2, "latency_ms": 15},
                value_summary="quant run completed",
                status="success",
            )
            raw_logs.save(quant_result.run_id, AgentRunRequest(scenario_id="quant", task="backtest"), quant_result)
            summary_logs.save(quant_result)
            failed_result = AgentRunResult(
                scenario_id="quant",
                task="backtest",
                answer="failed",
                metrics={},
                value_summary="adapter failed",
                status="failed",
                error_type="adapter_error",
            )
            raw_logs.save(failed_result.run_id, AgentRunRequest(scenario_id="quant", task="backtest"), failed_result)
            summary_logs.save(failed_result)
            proposal = PromptProposal(
                scenario_id="quant",
                agent_id="researcher",
                patch=PromptPatch(
                    slot=PromptSlot.CONSTRAINTS,
                    operation="replace",
                    before="loose",
                    after="strict",
                ),
                reason="Reduce invalid backtests.",
                expected_metric="sharpe",
                status=PromptProposalStatus.APPROVED,
                metadata={"awaiting_human_confirmation": True},
            )
            PromptProposalStore(db_path).create(proposal)
            loop = LoopRun(
                scenario_id="quant",
                trigger_type="manual",
                reason="daily review",
                task="backtest",
                status=LoopStatus.FAILED,
                adapter_run_id=failed_result.run_id,
                adapter_status="failed",
                adapter_value_summary="adapter failed",
            )
            AgentLoopStore(db_path).save(loop)

            snapshot = ConsoleReadModel(db_path).snapshot(scenario_id="quant")
            all_snapshot = ConsoleReadModel(db_path).snapshot(allow_cross_scenario=True, reason="operator overview")

        self.assertEqual(snapshot.scope.scenario_id, "quant")
        self.assertEqual(snapshot.scenario_count, 1)
        self.assertEqual(snapshot.active_scenario_count, 1)
        self.assertEqual(snapshot.archived_scenario_count, 0)
        self.assertEqual(snapshot.recent_run_count, 2)
        self.assertEqual(snapshot.failed_run_count, 1)
        self.assertEqual(snapshot.pending_approval_count, 1)
        self.assertEqual(snapshot.latest_runs[0].scenario_id, "quant")
        self.assertIn("需要处理 1 个审批项", snapshot.operator_summary)
        self.assertEqual(all_snapshot.scenario_count, 2)
        self.assertEqual(all_snapshot.archived_scenario_count, 1)

    def test_console_snapshot_rejects_unscoped_global_access(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "console.db"
            with self.assertRaisesRegex(ValueError, "Cross-scenario access requires reason"):
                ConsoleReadModel(db_path).snapshot(allow_cross_scenario=True)

    def test_console_snapshot_cli_is_human_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "console.db"
            ScenarioStore(db_path).save(
                Scenario(
                    id="quant",
                    name="Quant",
                    description="Quant research",
                    adapter_type="quant_research_demo",
                )
            )

            result = self._run(db_path, "console", "snapshot", "--scenario-id", "quant")

        self.assertIn("Console Snapshot", result.stdout)
        self.assertIn("scope: quant", result.stdout)
        self.assertIn("scenario_count: 1", result.stdout)
        self.assertIn("operator_summary", result.stdout)

    @staticmethod
    def _run(db_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        root = project_root()
        result = subprocess.run(
            ["./loopharness", "--db", str(db_path), *args],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr or result.stdout)
        return result


if __name__ == "__main__":
    unittest.main()
