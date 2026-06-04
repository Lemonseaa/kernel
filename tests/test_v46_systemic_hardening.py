"""V4.6 systemic hardening tests before V5."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.adapter import AgentRunRequest, AgentRunResult, DummyAdapter
from checkpoint_ai.logs import RawLogStore, SummaryLogStore
from checkpoint_ai.prompt import (
    PromptPatch,
    PromptProposal,
    PromptProposalStore,
    PromptSlot,
    Proposal,
    ProposalKind,
    ProposalPatch,
    ProposalStore,
    ProposalTargetType,
)
from checkpoint_ai.reporting import ReportGenerator
from checkpoint_ai.scenario import (
    Scenario,
    ScenarioRegistry,
    ScenarioRunner,
    ScenarioStatus,
    ScenarioStore,
)


class V46SystemicHardeningTest(unittest.TestCase):
    """Lock down hidden cross-scenario and archived scenario risks."""

    def test_latest_report_requires_scope_when_multiple_scenarios_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "hardening.db"
            raw_logs = RawLogStore(db_path)
            summary_logs = SummaryLogStore(db_path)
            first = AgentRunResult(
                scenario_id="scenario-a",
                task="task",
                answer="a",
                metrics={"quality": 0.7},
                value_summary="scenario a run",
                status="success",
            )
            second = AgentRunResult(
                scenario_id="scenario-b",
                task="task",
                answer="b",
                metrics={"quality": 0.8},
                value_summary="scenario b run",
                status="success",
            )
            raw_logs.save(first.run_id, AgentRunRequest(scenario_id="scenario-a", task="task"), first)
            raw_logs.save(second.run_id, AgentRunRequest(scenario_id="scenario-b", task="task"), second)
            summary_logs.save(first)
            summary_logs.save(second)

            unscoped = ReportGenerator(db_path).latest()
            scoped = ReportGenerator(db_path).latest(scenario_id="scenario-a")

        self.assertIn("需要指定 scenario_id", unscoped)
        self.assertIn("scenario_id: scenario-a", scoped)
        self.assertNotIn("scenario_id: scenario-b", scoped)

    def test_archived_scenario_cannot_start_new_adapter_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "hardening.db"
            store = ScenarioStore(db_path)
            store.save(
                Scenario(
                    id="archived",
                    name="Archived",
                    description="No new runs",
                    adapter_type="dummy_stock_signal",
                    status=ScenarioStatus.ARCHIVED,
                )
            )
            registry = ScenarioRegistry()
            registry.create(store.get("archived") or self.fail("scenario missing"))
            runner = ScenarioRunner(
                scenarios=registry,
                adapters=self._adapters(),
                raw_logs=RawLogStore(db_path),
                summary_logs=SummaryLogStore(db_path),
            )

            with self.assertRaisesRegex(ValueError, "archived"):
                runner.run_scenario("archived", "analyze_signal")

            self.assertEqual(RawLogStore(db_path).query_by_scenario("archived"), [])

    def test_generic_and_prompt_proposals_share_pending_inbox_view(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "hardening.db"
            prompt_store = PromptProposalStore(db_path)
            generic_store = ProposalStore(db_path)
            prompt = PromptProposal(
                scenario_id="scenario-a",
                agent_id="writer",
                patch=PromptPatch(
                    slot=PromptSlot.OUTPUT_FORMAT,
                    operation="replace",
                    before="text",
                    after="json",
                ),
                reason="Need structured output.",
                expected_metric="quality",
            )
            strategy = Proposal(
                scenario_id="scenario-a",
                proposal_kind=ProposalKind.STRATEGY,
                target_type=ProposalTargetType.STRATEGY_PARAM,
                target_id="fast_window",
                patch=ProposalPatch(operation="replace", before=8, after=10),
                reason="Improve signal responsiveness.",
                expected_metric="sharpe",
            )
            prompt_store.create(prompt)
            generic_store.create(strategy)

            pending = ReportGenerator(db_path).pending_items(scenario_id="scenario-a")

        self.assertEqual([item["source_id"] for item in pending], [prompt.id, strategy.id])
        self.assertEqual([item["item_type"] for item in pending], ["prompt_proposal", "strategy_proposal"])

    @staticmethod
    def _adapters() -> object:
        from checkpoint_ai.adapter import AdapterRegistry

        adapters = AdapterRegistry()
        adapters.register(DummyAdapter())
        return adapters


if __name__ == "__main__":
    unittest.main()
