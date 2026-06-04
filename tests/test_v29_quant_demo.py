"""V2.9 quant demo data-run tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.adapter import AdapterRegistry, AgentRunRequest, QuantResearchDemoAdapter
from checkpoint_ai.logs import RawLogStore, SummaryLogStore
from checkpoint_ai.loop import AgentLoopEngine, AgentLoopStore, LoopStatus
from checkpoint_ai.policy import ScenarioPolicy, ScenarioPolicyService
from checkpoint_ai.prompt import (
    PromptPatch,
    PromptProposal,
    PromptProposalStore,
    PromptSlot,
    PromptVersionStore,
)
from checkpoint_ai.scenario import Scenario, ScenarioRegistry, ScenarioRunner, ScenarioStore
from checkpoint_ai.shadow import ShadowResultStore, ShadowRunner


class V29QuantDemoTest(unittest.TestCase):
    """Validate a deterministic quant scenario before V3."""

    def test_quant_adapter_returns_replayable_backtest_metrics(self) -> None:
        adapter = QuantResearchDemoAdapter()

        result = adapter.run(
            AgentRunRequest(
                scenario_id="quant-demo",
                task="backtest_strategy",
                context={"symbol": "SPY", "strategy_type": "moving_average"},
                config={"fast_window": 8, "slow_window": 24},
            )
        )

        self.assertEqual(result.status, "success")
        self.assertIn("moving_average", result.answer)
        self.assertIn("total_return", result.metrics)
        self.assertIn("max_drawdown", result.metrics)
        self.assertIn("sharpe", result.metrics)
        self.assertIn("excess_return", result.metrics)
        self.assertIn("stability_score", result.metrics)
        self.assertGreater(result.metrics["trade_count"], 0)
        self.assertTrue(result.value_summary)

    def test_cli_and_report_capture_quant_demo_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v29.db"
            self._run(
                db_path,
                "scenario",
                "create",
                "--id",
                "quant-demo",
                "--name",
                "Quant Demo",
                "--description",
                "Pre-V3 quant data run",
                "--adapter",
                "quant_research_demo",
                "--adapter-config-json",
                '{"fast_window": 8, "slow_window": 24}',
            )
            adapter_run = self._run(
                db_path,
                "adapter",
                "run",
                "--scenario-id",
                "quant-demo",
                "--task",
                "backtest_strategy",
                "--context-json",
                '{"symbol": "SPY", "strategy_type": "moving_average"}',
            )
            report = self._run(db_path, "report", "latest")
            logs = RawLogStore(db_path).query_by_scenario("quant-demo")

        self.assertIn("Adapter Run Report", adapter_run.stdout)
        self.assertIn("total_return", adapter_run.stdout)
        self.assertIn("max_drawdown", adapter_run.stdout)
        self.assertIn("Run Report", report.stdout)
        self.assertIn("value_summary", report.stdout)
        self.assertEqual(len(logs), 1)
        self.assertIn("sharpe", logs[0]["result"]["metrics"])

    def test_quant_demo_runs_through_v2_loop_and_shadow_compare(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v29.db"
            scenarios = ScenarioRegistry()
            ScenarioStore(db_path).save(
                Scenario(
                    id="quant-demo",
                    name="Quant Demo",
                    description="Pre-V3 quant data run",
                    adapter_type="quant_research_demo",
                    adapter_config={"fast_window": 8, "slow_window": 24},
                )
            )
            for scenario in ScenarioStore(db_path).list():
                scenarios.create(scenario)
            adapters = AdapterRegistry()
            adapters.register(QuantResearchDemoAdapter())
            versions = PromptVersionStore(db_path)
            versions.save_version(
                scenario_id="quant-demo",
                agent_id="strategy",
                slots={PromptSlot.CONSTRAINTS: "fast_window=8, slow_window=24"},
                reason="baseline quant parameters",
            )
            proposals = PromptProposalStore(db_path)
            shadow_results = ShadowResultStore(db_path)
            runner = ScenarioRunner(
                scenarios=scenarios,
                adapters=adapters,
                raw_logs=RawLogStore(db_path),
                summary_logs=SummaryLogStore(db_path),
            )
            policy_service = ScenarioPolicyService(
                policy=ScenarioPolicy(),
                proposals=proposals,
                versions=versions,
                shadow_runner=ShadowRunner(
                    scenarios=scenarios,
                    adapters=adapters,
                    versions=versions,
                    results=shadow_results,
                    task="backtest_strategy",
                    context={"symbol": "SPY", "strategy_type": "moving_average"},
                ),
            )
            engine = AgentLoopEngine(
                scenario_runner=runner,
                proposals=proposals,
                policy_service=policy_service,
                shadow_results=shadow_results,
                loop_store=AgentLoopStore(db_path),
                proposal_factory=self._proposal_factory,
            )

            loop_run = engine.trigger_manual(
                scenario_id="quant-demo",
                task="backtest_strategy",
                reason="Pre-V3验证：量化demo能否为V3提供可比较数据。",
                context={"symbol": "SPY", "strategy_type": "moving_average"},
            )
            shadow = shadow_results.query_by_proposal(loop_run.proposal_id or "")[-1]

        self.assertEqual(loop_run.status, LoopStatus.COMPLETED)
        self.assertEqual(loop_run.policy_action, "awaiting_human_confirmation")
        self.assertIn("total_return", loop_run.baseline_comparison)
        self.assertIn("sharpe", loop_run.baseline_comparison)
        self.assertIn("max_drawdown", shadow.shadow_metrics)
        self.assertTrue(shadow.passed)

    @staticmethod
    def _proposal_factory(scenario_id: str, run_metrics: dict[str, float]) -> PromptProposal:
        return PromptProposal(
            scenario_id=scenario_id,
            agent_id="strategy",
            patch=PromptPatch(
                slot=PromptSlot.CONSTRAINTS,
                operation="replace",
                before="fast_window=8, slow_window=24",
                after="fast_window=10, slow_window=30",
            ),
            reason=f"baseline sharpe={run_metrics.get('sharpe', 0):.2f}，尝试放慢均线减少噪声。",
            expected_metric="sharpe",
            metadata={"fast_window": 10, "slow_window": 30},
        )

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


if __name__ == "__main__":
    unittest.main()
