"""V4.4 cross-scenario insight preview tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.insights import (
    CrossScenarioInsightDecision,
    CrossScenarioInsightGenerator,
    CrossScenarioInsightStore,
    ScenarioInsightInput,
)
from checkpoint_ai.reporting import ReportGenerator
from tests.helpers import project_root


class V44CrossScenarioInsightTest(unittest.TestCase):
    """Validate observation-only cross-scenario insight behavior."""

    def test_insight_rejects_underpowered_scenarios(self) -> None:
        insight = CrossScenarioInsightGenerator().compare(
            ScenarioInsightInput(
                scenario_id="quant",
                domain_tags=["quant"],
                metric_names=["sharpe"],
                run_count=10,
                non_synthetic_recommendation_count=1,
            ),
            ScenarioInsightInput(
                scenario_id="content",
                domain_tags=["content"],
                metric_names=["readability"],
                run_count=30,
                non_synthetic_recommendation_count=1,
            ),
        )

        self.assertEqual(insight.decision, CrossScenarioInsightDecision.REJECT)
        self.assertIn("run_count", insight.rejection_reasons)

    def test_insight_rejects_synthetic_only_evidence(self) -> None:
        insight = CrossScenarioInsightGenerator().compare(
            ScenarioInsightInput(
                scenario_id="quant-a",
                domain_tags=["quant", "strategy"],
                metric_names=["sharpe", "drawdown"],
                run_count=30,
                non_synthetic_recommendation_count=0,
            ),
            ScenarioInsightInput(
                scenario_id="quant-b",
                domain_tags=["quant", "strategy"],
                metric_names=["sharpe", "drawdown"],
                run_count=30,
                non_synthetic_recommendation_count=1,
            ),
        )

        self.assertEqual(insight.decision, CrossScenarioInsightDecision.REJECT)
        self.assertIn("non_synthetic_evidence", insight.rejection_reasons)

    def test_insight_suggests_only_when_similarity_and_real_evidence_exist(self) -> None:
        insight = CrossScenarioInsightGenerator().compare(
            ScenarioInsightInput(
                scenario_id="quant-a",
                domain_tags=["quant", "strategy"],
                metric_names=["sharpe", "max_drawdown"],
                run_count=30,
                non_synthetic_recommendation_count=1,
            ),
            ScenarioInsightInput(
                scenario_id="quant-b",
                domain_tags=["quant", "strategy"],
                metric_names=["sharpe", "max_drawdown"],
                run_count=30,
                non_synthetic_recommendation_count=2,
            ),
        )

        self.assertEqual(insight.decision, CrossScenarioInsightDecision.SUGGEST)
        self.assertIn("observation only", insight.reason)

    def test_insight_store_and_report_are_observation_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "insights.db"
            store = CrossScenarioInsightStore(db_path)
            insight = CrossScenarioInsightGenerator().compare(
                ScenarioInsightInput(
                    scenario_id="quant-a",
                    domain_tags=["quant", "strategy"],
                    metric_names=["sharpe"],
                    run_count=30,
                    non_synthetic_recommendation_count=1,
                ),
                ScenarioInsightInput(
                    scenario_id="quant-b",
                    domain_tags=["quant", "strategy"],
                    metric_names=["sharpe"],
                    run_count=30,
                    non_synthetic_recommendation_count=1,
                ),
            )
            store.save(insight)

            report = ReportGenerator(db_path).insight(insight.id)

            self.assertIn("Cross-Scenario Insight Report", report)
            self.assertIn("observation only", report)
            self.assertIn("does not migrate", report)

    def test_insight_cli_compare_and_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "insights.db"
            compared = _run_cli(
                db_path,
                "insight",
                "compare",
                "--source",
                "quant-a",
                "--target",
                "quant-b",
                "--source-tags",
                "quant,strategy",
                "--target-tags",
                "quant,strategy",
                "--source-metrics",
                "sharpe,drawdown",
                "--target-metrics",
                "sharpe,drawdown",
                "--source-runs",
                "30",
                "--target-runs",
                "30",
                "--source-non-synthetic-recommendations",
                "1",
                "--target-non-synthetic-recommendations",
                "1",
            )
            listed = _run_cli(db_path, "insight", "list")

            self.assertIn("Cross-scenario insight created", compared.stdout)
            self.assertIn("suggest", compared.stdout)
            self.assertIn("quant-a", listed.stdout)


def _run_cli(db_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    root = project_root()
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
