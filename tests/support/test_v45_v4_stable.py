"""V4.5 stable end-to-end tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.adapter import (
    AdapterCompatibilityDecision,
    AdapterCompatibilityEvaluator,
    AdapterCompatibilityInput,
    AdapterRegistry,
    DummyAdapter,
    QuantResearchDemoAdapter,
)
from checkpoint_ai.insights import (
    CrossScenarioInsightDecision,
    CrossScenarioInsightGenerator,
    ScenarioInsightInput,
)
from checkpoint_ai.isolation import ScenarioIsolationAuditor
from checkpoint_ai.logs import RawLogStore, SummaryLogStore
from checkpoint_ai.metrics import MetricDirection, MetricSchema, MetricSchemaStore
from checkpoint_ai.scenario import Scenario, ScenarioRegistry, ScenarioRunner, ScenarioStore


class V45V4StableTest(unittest.TestCase):
    """Validate multi-scenario, multi-adapter infrastructure."""

    def test_v4_stable_multi_scenario_multi_adapter_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v45.db"
            scenario_store = ScenarioStore(db_path)
            scenario_store.save(
                Scenario(
                    id="quant",
                    name="Quant",
                    description="quant scenario",
                    adapter_type="quant_research_demo",
                )
            )
            scenario_store.save(
                Scenario(
                    id="content",
                    name="Content",
                    description="content scenario",
                    adapter_type="dummy_stock_signal",
                )
            )
            metric_schemas = MetricSchemaStore(db_path)
            metric_schemas.save_for_scenario(
                "quant",
                [MetricSchema(name="sharpe", direction=MetricDirection.HIGHER)],
            )
            metric_schemas.save_for_scenario(
                "content",
                [MetricSchema(name="signal_quality", direction=MetricDirection.HIGHER)],
            )
            scenarios = ScenarioRegistry()
            for scenario in scenario_store.list():
                scenarios.create(scenario)
            adapters = AdapterRegistry()
            adapters.register(QuantResearchDemoAdapter())
            adapters.register(DummyAdapter())
            runner = ScenarioRunner(
                scenarios=scenarios,
                adapters=adapters,
                raw_logs=RawLogStore(db_path),
                summary_logs=SummaryLogStore(db_path),
            )

            quant = runner.run_scenario(
                "quant",
                "backtest_strategy",
                context={"symbol": "SPY", "strategy_type": "moving_average"},
            )
            content = runner.run_scenario(
                "content",
                "analyze_signal",
                context={"symbol": "AAPL"},
            )
            audit = ScenarioIsolationAuditor().audit_sqlite(db_path)
            compat = AdapterCompatibilityEvaluator().evaluate(
                AdapterCompatibilityInput(
                    name="TradingAgents",
                    structured_input=True,
                    structured_output=True,
                    prompt_slots=False,
                    prompt_injection=False,
                    shadow_run=False,
                    run_trace=True,
                    metrics_capture=True,
                    metric_format_compatible=False,
                    estimated_days=8,
                )
            )
            insight = CrossScenarioInsightGenerator().compare(
                ScenarioInsightInput(
                    scenario_id="quant",
                    domain_tags=["quant"],
                    metric_names=["sharpe"],
                    run_count=30,
                    non_synthetic_recommendation_count=1,
                ),
                ScenarioInsightInput(
                    scenario_id="content",
                    domain_tags=["content"],
                    metric_names=["signal_quality"],
                    run_count=30,
                    non_synthetic_recommendation_count=1,
                ),
            )

            self.assertEqual(quant.status, "success")
            self.assertEqual(content.status, "success")
            self.assertTrue(adapters.supports("quant_research_demo", "continuous_params"))
            self.assertFalse(adapters.supports("dummy_stock_signal", "continuous_params"))
            self.assertIn("quant", {scenario_id for result in audit for scenario_id in result.scenario_ids})
            self.assertEqual(compat.decision, AdapterCompatibilityDecision.NEEDS_SPIKE)
            self.assertEqual(insight.decision, CrossScenarioInsightDecision.REJECT)
            self.assertIn("domain_similarity", insight.rejection_reasons)


if __name__ == "__main__":
    unittest.main()
