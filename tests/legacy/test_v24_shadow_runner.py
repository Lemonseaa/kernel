"""V2.4 ShadowRunner tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.adapter import AdapterRegistry, DummyAdapter
from checkpoint_ai.prompt import (
    PromptPatch,
    PromptProposal,
    PromptProposalStore,
    PromptSlot,
    PromptVersionStore,
)
from checkpoint_ai.scenario import Scenario, ScenarioRegistry
from checkpoint_ai.shadow import ShadowResultStore, ShadowRunner


class V24ShadowRunnerTest(unittest.TestCase):
    """Validate shadow execution, baseline comparison, and persistence."""

    def test_shadow_run_does_not_change_deployed_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner, version_store, proposal = self._build_runner(tmp)
            before = version_store.get_latest("scenario-1", "writer")

            result = runner.run(proposal)
            after = version_store.get_latest("scenario-1", "writer")

        self.assertTrue(result.passed)
        self.assertIsNotNone(before)
        self.assertIsNotNone(after)
        self.assertEqual(before.id, after.id)
        self.assertEqual(after.slots[PromptSlot.OUTPUT_FORMAT], "输出自然语言。")

    def test_shadow_result_is_marked_and_comparable_to_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner, _, proposal = self._build_runner(tmp)

            result = runner.run(proposal)

        self.assertTrue(result.is_shadow)
        self.assertEqual(result.proposal_id, proposal.id)
        self.assertEqual(result.status, "success")
        self.assertIn("shadow result", result.value_summary.lower())
        self.assertIn("signal_quality", result.metric_diff)
        self.assertAlmostEqual(result.metric_diff["signal_quality"], 0.08)
        self.assertIn("confidence", result.metric_diff)

    def test_shadow_result_store_saves_and_queries_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner, _, proposal = self._build_runner(tmp)
            result = runner.run(proposal)

            loaded = runner.results.get(result.id)
            by_proposal = runner.results.query_by_proposal(proposal.id)
            by_scenario = runner.results.query_by_scenario("scenario-1")

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.id, result.id)
        self.assertEqual([item.id for item in by_proposal], [result.id])
        self.assertEqual([item.id for item in by_scenario], [result.id])

    def test_shadow_failure_is_stored_and_does_not_pollute_main_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner, version_store, proposal = self._build_runner(tmp, proposal_config={"force_failure": True})
            before = version_store.get_latest("scenario-1", "writer")

            result = runner.run(proposal)
            after = version_store.get_latest("scenario-1", "writer")
            stored = runner.results.get(result.id)

        self.assertFalse(result.passed)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_type, "adapter_error")
        self.assertIsNotNone(before)
        self.assertIsNotNone(after)
        self.assertEqual(before.id, after.id)
        self.assertIsNotNone(stored)
        self.assertEqual(stored.status, "failed")

    def test_policy_service_uses_shadow_result_boolean(self) -> None:
        from checkpoint_ai.policy import ScenarioPolicy, ScenarioPolicyService

        with tempfile.TemporaryDirectory() as tmp:
            runner, version_store, proposal = self._build_runner(tmp)
            proposals = PromptProposalStore(Path(tmp) / "v24.db")
            proposals.create(proposal)
            service = ScenarioPolicyService(
                policy=ScenarioPolicy(),
                proposals=proposals,
                versions=version_store,
                shadow_runner=runner,
            )

            process_result = service.process(proposal.id)
            latest = version_store.get_latest("scenario-1", "writer")
            shadow_results = runner.results.query_by_proposal(proposal.id)

        self.assertTrue(process_result.shadow_passed)
        self.assertEqual(process_result.action, "auto_applied")
        self.assertIsNotNone(latest)
        self.assertEqual(latest.slots[PromptSlot.OUTPUT_FORMAT], "输出 JSON。")
        self.assertEqual(len(shadow_results), 1)

    @staticmethod
    def _build_runner(
        tmp: str,
        proposal_config: dict[str, object] | None = None,
    ) -> tuple[ShadowRunner, PromptVersionStore, PromptProposal]:
        db_path = Path(tmp) / "v24.db"
        scenarios = ScenarioRegistry()
        scenarios.create(
            Scenario(
                id="scenario-1",
                name="Quant demo",
                description="Shadow runner scenario.",
                adapter_type="dummy_stock_signal",
            )
        )
        adapters = AdapterRegistry()
        adapters.register(DummyAdapter())
        versions = PromptVersionStore(db_path)
        versions.save_version(
            scenario_id="scenario-1",
            agent_id="writer",
            slots={PromptSlot.OUTPUT_FORMAT: "输出自然语言。"},
            reason="baseline prompt",
        )
        proposal = PromptProposal(
            scenario_id="scenario-1",
            agent_id="writer",
            patch=PromptPatch(
                slot=PromptSlot.OUTPUT_FORMAT,
                operation="replace",
                before="输出自然语言。",
                after="输出 JSON。",
            ),
            reason="结构化输出更稳定。",
            expected_metric="signal_quality",
            metadata=proposal_config or {},
        )
        return (
            ShadowRunner(
                scenarios=scenarios,
                adapters=adapters,
                versions=versions,
                results=ShadowResultStore(db_path),
                task="analyze_signal",
                context={"symbol": "AAPL"},
            ),
            versions,
            proposal,
        )


if __name__ == "__main__":
    unittest.main()
