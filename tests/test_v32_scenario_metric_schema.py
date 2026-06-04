"""V3.2 scenario metric schema tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.adapter import (
    AdapterCapabilities,
    AdapterRegistry,
    AgentAdapter,
    AgentRunRequest,
    AgentRunResult,
    CapabilitySupport,
)
from checkpoint_ai.metrics import (
    MetricCategory,
    MetricDirection,
    MetricSchema,
    MetricSchemaStore,
)
from checkpoint_ai.prompt import (
    PromptPatch,
    PromptProposal,
    PromptSlot,
    PromptVersionStore,
)
from checkpoint_ai.reporting import ReportGenerator
from checkpoint_ai.scenario import Scenario, ScenarioRegistry
from checkpoint_ai.shadow import ShadowResultStore, ShadowRunner


class V32ScenarioMetricSchemaTest(unittest.TestCase):
    """Validate scenario-specific metric schemas and evidence reports."""

    def test_metric_schema_store_saves_and_loads_scenario_schemas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MetricSchemaStore(Path(tmp) / "schemas.db")
            store.save_for_scenario(
                "quant",
                [
                    MetricSchema(
                        name="sharpe",
                        direction=MetricDirection.HIGHER,
                        category=MetricCategory.BUSINESS,
                        weight=0.5,
                    ),
                    MetricSchema(
                        name="max_drawdown",
                        direction=MetricDirection.LOWER,
                        category=MetricCategory.GUARDRAIL,
                        weight=0.5,
                        threshold=0.2,
                        is_guardrail=True,
                    ),
                ],
            )

            loaded = store.list_for_scenario("quant")

            self.assertEqual([schema.name for schema in loaded], ["max_drawdown", "sharpe"])
            self.assertEqual(loaded[0].direction, MetricDirection.LOWER)
            self.assertTrue(loaded[0].is_guardrail)

    def test_metric_schema_store_isolates_scenarios(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MetricSchemaStore(Path(tmp) / "schemas.db")
            store.save_for_scenario(
                "quant",
                [MetricSchema(name="sharpe", direction=MetricDirection.HIGHER)],
            )
            store.save_for_scenario(
                "content",
                [MetricSchema(name="readability", direction=MetricDirection.HIGHER)],
            )

            self.assertEqual([schema.name for schema in store.list_for_scenario("quant")], ["sharpe"])
            self.assertEqual([schema.name for schema in store.list_for_scenario("content")], ["readability"])

    def test_shadow_runner_uses_scenario_metric_schema_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v32.db"
            schema_store = MetricSchemaStore(db_path)
            schema_store.save_for_scenario(
                "quant",
                [
                    MetricSchema(
                        name="risk",
                        direction=MetricDirection.LOWER,
                        category=MetricCategory.GUARDRAIL,
                        weight=1.0,
                        threshold=0.1,
                        is_guardrail=True,
                    )
                ],
            )
            scenarios = ScenarioRegistry()
            scenarios.create(
                Scenario(
                    id="quant",
                    name="Quant",
                    description="metric schema test",
                    adapter_type="risk_fixture",
                )
            )
            adapters = AdapterRegistry()
            adapters.register(_RiskFixtureAdapter())
            versions = PromptVersionStore(db_path)
            versions.save_version(
                scenario_id="quant",
                agent_id="strategy",
                slots={PromptSlot.CONSTRAINTS: "baseline"},
                reason="baseline",
            )
            results = ShadowResultStore(db_path)
            runner = ShadowRunner(
                scenarios=scenarios,
                adapters=adapters,
                versions=versions,
                results=results,
                task="backtest",
                metric_schema_store=schema_store,
            )

            result = runner.run(
                PromptProposal(
                    scenario_id="quant",
                    agent_id="strategy",
                    patch=PromptPatch(
                        slot=PromptSlot.CONSTRAINTS,
                        operation="replace",
                        before="baseline",
                        after="candidate",
                    ),
                    reason="raise risk to test guardrail",
                    expected_metric="risk",
                    metadata={
                        "baseline_metrics": {"risk": 0.05},
                        "run_kind": "historical",
                        "provenance": {"sample_count": 90},
                    },
                )
            )

            self.assertEqual(result.comparison_result["guardrail_violations"], ["risk"])

    def test_report_generator_prints_evidence_detail_for_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v32.db"
            scenarios = ScenarioRegistry()
            scenarios.create(
                Scenario(
                    id="quant",
                    name="Quant",
                    description="report test",
                    adapter_type="risk_fixture",
                )
            )
            adapters = AdapterRegistry()
            adapters.register(_RiskFixtureAdapter())
            versions = PromptVersionStore(db_path)
            versions.save_version(
                scenario_id="quant",
                agent_id="strategy",
                slots={PromptSlot.CONSTRAINTS: "baseline"},
                reason="baseline",
            )
            results = ShadowResultStore(db_path)
            proposal = PromptProposal(
                scenario_id="quant",
                agent_id="strategy",
                patch=PromptPatch(
                    slot=PromptSlot.CONSTRAINTS,
                    operation="replace",
                    before="baseline",
                    after="candidate",
                ),
                reason="report evidence",
                expected_metric="sharpe",
                metadata={
                    "baseline_metrics": {"sharpe": 0.1},
                    "run_kind": "synthetic",
                    "provenance": {"sample_count": 260},
                },
            )
            from checkpoint_ai.prompt import PromptProposalStore

            PromptProposalStore(db_path).create(proposal)
            ShadowRunner(
                scenarios=scenarios,
                adapters=adapters,
                versions=versions,
                results=results,
                task="backtest",
            ).run(proposal)

            report = ReportGenerator(db_path).proposal(proposal.id)

            self.assertIn("证据判断:", report)
            self.assertIn("evidence_decision: inconclusive", report)
            self.assertIn("recommended_action: collect_more_evidence", report)
            self.assertIn("run_kind: synthetic", report)
            self.assertIn("sample_count: 260", report)

    def test_metric_schema_cli_sets_and_lists_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v32.db"
            set_result = _run_cli(
                db_path,
                "metric-schema",
                "set",
                "--scenario-id",
                "quant",
                "--name",
                "sharpe",
                "--direction",
                "higher",
                "--category",
                "business",
                "--weight",
                "0.3",
            )
            list_result = _run_cli(db_path, "metric-schema", "list", "--scenario-id", "quant")

            self.assertIn("Metric schema saved", set_result.stdout)
            self.assertIn("sharpe", list_result.stdout)
            self.assertIn("higher", list_result.stdout)
            self.assertIn("business", list_result.stdout)
            self.assertIn("weight=0.3", list_result.stdout)


class _RiskFixtureAdapter(AgentAdapter):
    @property
    def name(self) -> str:
        return "risk_fixture"

    @property
    def supported_task_types(self) -> list[str]:
        return ["backtest"]

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        metrics = {"risk": 0.2, "sharpe": 0.9}
        return AgentRunResult(
            scenario_id=request.scenario_id,
            task=request.task,
            status="success",
            answer="fixture",
            metrics=metrics,
            value_summary="fixture metrics",
        )

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            prompt_injection=CapabilitySupport.SUPPORTED,
            metrics_capture=CapabilitySupport.SUPPORTED,
            shadow_run=CapabilitySupport.SUPPORTED,
        )


def _run_cli(db_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
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
