"""V5.2-V5.7 control console tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from loop_harness.adapter import AgentRunRequest, AgentRunResult
from loop_harness.console import (
    ApprovalInbox,
    BackupManager,
    ConsoleDashboard,
    CostEvent,
    CostEventStore,
    NotificationRouter,
)
from loop_harness.logs import RawLogStore, SummaryLogStore
from loop_harness.notification import NotificationManager
from loop_harness.optimization import (
    OptimizationDirection,
    ParameterSuggestion,
    ParameterSuggestionStore,
)
from loop_harness.prompt import (
    PromptPatch,
    PromptProposal,
    PromptProposalStatus,
    PromptProposalStore,
    PromptSlot,
    Proposal,
    ProposalKind,
    ProposalPatch,
    ProposalStore,
    ProposalTargetType,
)
from loop_harness.recommendation import (
    RecommendationDecision,
    RecommendationStatus,
    VersionRecommendation,
    VersionRecommendationStore,
)
from loop_harness.scenario import Scenario, ScenarioStore
from tests.helpers import project_root


class V52V57ControlConsoleTest(unittest.TestCase):
    """Validate V5 control-plane features that prepare V6."""

    def test_approval_inbox_aggregates_and_resolves_all_actionable_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v5.db"
            prompt = PromptProposal(
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
            PromptProposalStore(db_path).create(prompt)
            strategy = Proposal(
                scenario_id="quant",
                proposal_kind=ProposalKind.STRATEGY,
                target_type=ProposalTargetType.STRATEGY_PARAM,
                target_id="risk_limit",
                patch=ProposalPatch(operation="replace", before=0.2, after=0.15),
                reason="Reduce drawdown.",
                expected_metric="max_drawdown",
            )
            ProposalStore(db_path).create(strategy)
            recommendation = VersionRecommendation(
                scenario_id="quant",
                target_id="researcher.constraints",
                decision=RecommendationDecision.RECOMMEND,
                status=RecommendationStatus.OPEN,
                confidence=0.72,
                objective_score=0.18,
                reason="Historical evidence improved.",
                recommended_action="approve_proposal",
            )
            VersionRecommendationStore(db_path).save(recommendation)
            suggestion = ParameterSuggestion(
                scenario_id="quant",
                target_id="strategy.fast_window",
                parameter_name="fast_window",
                suggested_value=10,
                expected_score=1.4,
                confidence=0.61,
                reason="Explore nearby value.",
                observations_used=8,
                direction=OptimizationDirection.MAXIMIZE,
            )
            ParameterSuggestionStore(db_path).save(suggestion)

            inbox = ApprovalInbox(db_path)
            items = inbox.list_items(scenario_id="quant")
            inbox.reject(strategy.id, reason="Too early for risk change.")
            inbox.approve(recommendation.id, reason="Evidence is enough.")

            self.assertEqual(
                [item.item_type for item in items],
                ["prompt_proposal", "strategy_proposal", "recommendation", "parameter_suggestion"],
            )
            self.assertEqual(ProposalStore(db_path).get(strategy.id).status.value, "rejected")
            self.assertEqual(VersionRecommendationStore(db_path).get(recommendation.id).status.value, "accepted")

    def test_dashboard_answers_run_and_experiment_questions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v5.db"
            ScenarioStore(db_path).save(
                Scenario(
                    id="quant",
                    name="Quant",
                    description="Quant dashboard",
                    adapter_type="quant_research_demo",
                )
            )
            result = AgentRunResult(
                scenario_id="quant",
                task="backtest",
                answer="strategy report",
                metrics={"sharpe": 1.3, "max_drawdown": -0.08},
                value_summary="Backtest improved risk-adjusted return.",
                status="success",
            )
            RawLogStore(db_path).save(result.run_id, AgentRunRequest(scenario_id="quant", task="backtest"), result)
            SummaryLogStore(db_path).save(result)

            report = ConsoleDashboard(db_path).run_report(result.run_id)

        self.assertEqual(report.run_id, result.run_id)
        self.assertIn("为什么运行", report.core_questions)
        self.assertIn("发生了什么", report.core_questions)
        self.assertIn("有没有变好", report.core_questions)
        self.assertEqual(report.metrics["sharpe"], 1.3)

    def test_cost_events_are_persisted_and_summarized_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v5.db"
            store = CostEventStore(db_path)
            store.record(
                CostEvent(
                    scenario_id="quant",
                    business_line_id="trading",
                    provider="minimax",
                    input_tokens=1000,
                    output_tokens=500,
                    estimated_cost=1.5,
                )
            )

            reopened = CostEventStore(db_path)
            summary = reopened.daily_summary(provider="minimax", business_line_id="trading")

        self.assertEqual(summary.total_tokens, 1500)
        self.assertEqual(summary.estimated_cost, 1.5)
        self.assertEqual(summary.provider, "minimax")

    def test_notification_router_sends_only_actionable_categories(self) -> None:
        manager = NotificationManager()
        router = NotificationRouter(
            notification_manager=manager,
            enabled_types={"approval_required", "budget_warning"},
        )

        sent = router.route(
            event_type="approval_required",
            title="Prompt approval",
            body="A prompt patch needs review.",
            source_id="p1",
        )
        skipped = router.route(
            event_type="run_completed",
            title="Run completed",
            body="No human action needed.",
            source_id="r1",
        )

        self.assertTrue(sent)
        self.assertFalse(skipped)
        self.assertEqual(len(manager.history), 1)
        self.assertEqual(manager.history[0].data["source_id"], "p1")

    def test_backup_manager_creates_lists_and_restores_sqlite_database(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "v5.db"
            backups = root / "backups"
            ScenarioStore(db_path).save(
                Scenario(
                    id="quant",
                    name="Quant",
                    description="Before backup",
                    adapter_type="quant_research_demo",
                )
            )
            manager = BackupManager(db_path=db_path, backup_dir=backups)
            backup = manager.create_backup(label="before-change")
            ScenarioStore(db_path).save(
                Scenario(
                    id="content",
                    name="Content",
                    description="After backup",
                    adapter_type="dummy_stock_signal",
                )
            )

            manager.restore(backup.id)
            scenarios = ScenarioStore(db_path).list()

            self.assertEqual([scenario.id for scenario in scenarios], ["quant"])
            self.assertEqual(manager.list_backups()[0].label, "before-change")

    def test_v5_stable_console_flow_combines_snapshot_inbox_cost_and_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "v5.db"
            ScenarioStore(db_path).save(
                Scenario(
                    id="quant",
                    name="Quant",
                    description="Stable flow",
                    adapter_type="quant_research_demo",
                )
            )
            PromptProposalStore(db_path).create(
                PromptProposal(
                    scenario_id="quant",
                    agent_id="researcher",
                    patch=PromptPatch(
                        slot=PromptSlot.OUTPUT_FORMAT,
                        operation="replace",
                        before="text",
                        after="json",
                    ),
                    reason="Improve evaluation stability.",
                    expected_metric="sharpe",
                )
            )
            CostEventStore(db_path).record(
                CostEvent(
                    scenario_id="quant",
                    business_line_id="trading",
                    provider="minimax",
                    input_tokens=100,
                    output_tokens=50,
                    estimated_cost=0.15,
                )
            )

            snapshot = ConsoleDashboard(db_path).stable_summary(
                scenario_id="quant",
                backup_dir=root / "backups",
            )

        self.assertEqual(snapshot["scenario_id"], "quant")
        self.assertEqual(snapshot["pending_approval_count"], 1)
        self.assertEqual(snapshot["cost"]["total_tokens"], 150)
        self.assertTrue(snapshot["backup_id"])

    def test_console_cli_exposes_approval_cost_and_backup_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "v5.db"
            PromptProposalStore(db_path).create(
                PromptProposal(
                    scenario_id="quant",
                    agent_id="researcher",
                    patch=PromptPatch(
                        slot=PromptSlot.OUTPUT_FORMAT,
                        operation="replace",
                        before="text",
                        after="json",
                    ),
                    reason="Improve structured evaluation.",
                    expected_metric="sharpe",
                )
            )
            CostEventStore(db_path).record(
                CostEvent(
                    scenario_id="quant",
                    business_line_id="trading",
                    provider="minimax",
                    input_tokens=10,
                    output_tokens=5,
                    estimated_cost=0.015,
                )
            )

            approvals = self._run(db_path, "console", "approvals", "--scenario-id", "quant")
            cost = self._run(
                db_path,
                "console",
                "cost",
                "--provider",
                "minimax",
                "--business-line-id",
                "trading",
            )
            backup = self._run(
                db_path,
                "console",
                "backup",
                "create",
                "--backup-dir",
                str(root / "backups"),
                "--label",
                "manual",
            )
            backup_list = self._run(db_path, "console", "backup", "list", "--backup-dir", str(root / "backups"))

        self.assertIn("Approval Inbox", approvals.stdout)
        self.assertIn("prompt_proposal", approvals.stdout)
        self.assertIn("Cost Summary", cost.stdout)
        self.assertIn("total_tokens: 15", cost.stdout)
        self.assertIn("Backup created", backup.stdout)
        self.assertIn("Backups", backup_list.stdout)

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
