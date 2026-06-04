"""V4.1 scenario isolation hardening tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.adapter import AgentRunRequest, AgentRunResult
from checkpoint_ai.isolation import ScenarioIsolationAuditor, ScenarioScope
from checkpoint_ai.logs import RawLogStore, SummaryLogStore
from checkpoint_ai.optimization import ParameterSuggestion, ParameterSuggestionStore
from checkpoint_ai.recommendation import (
    RecommendationDecision,
    VersionRecommendation,
    VersionRecommendationStore,
)
from checkpoint_ai.scenario import Scenario, ScenarioStatus, ScenarioStore


class V41ScenarioIsolationTest(unittest.TestCase):
    """Validate explicit scenario isolation contracts."""

    def test_scenario_scope_requires_explicit_cross_scenario_reason(self) -> None:
        scope = ScenarioScope(scenario_id="quant")
        self.assertEqual(scope.scenario_id, "quant")
        self.assertFalse(scope.allow_cross_scenario)

        cross = ScenarioScope.cross_scenario(reason="admin audit")

        self.assertTrue(cross.allow_cross_scenario)
        self.assertEqual(cross.reason, "admin audit")
        with self.assertRaises(ValueError):
            ScenarioScope.cross_scenario(reason="")

    def test_scenario_archive_stops_new_runs_without_deleting_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v41.db"
            scenarios = ScenarioStore(db_path)
            scenario = Scenario(
                id="quant",
                name="Quant",
                description="quant scenario",
                adapter_type="dummy_stock_signal",
            )
            scenarios.save(scenario)

            archived = scenarios.archive("quant", reason="pause experiments")
            loaded = scenarios.get("quant")

            self.assertTrue(archived)
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.status, ScenarioStatus.ARCHIVED)
            self.assertIn("pause experiments", loaded.metadata["archive_reason"])

    def test_isolation_auditor_reports_scenario_ids_across_stores(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v41.db"
            raw_logs = RawLogStore(db_path)
            summary_logs = SummaryLogStore(db_path)
            recommendations = VersionRecommendationStore(db_path)
            suggestions = ParameterSuggestionStore(db_path)
            for scenario_id in ["quant", "content"]:
                request = AgentRunRequest(scenario_id=scenario_id, task="task")
                result = AgentRunResult(
                    scenario_id=scenario_id,
                    task="task",
                    answer="answer",
                    metrics={"score": 1.0},
                    value_summary="value",
                    status="success",
                )
                raw_logs.save(result.run_id, request, result)
                summary_logs.save(result)
            recommendations.save(
                VersionRecommendation(
                    scenario_id="quant",
                    target_id="strategy",
                    decision=RecommendationDecision.INSUFFICIENT_EVIDENCE,
                    confidence=0.0,
                    objective_score=0.0,
                    reason="synthetic only",
                    recommended_action="collect_more_evidence",
                )
            )
            suggestions.save(
                ParameterSuggestion(
                    scenario_id="content",
                    target_id="writer.temperature",
                    parameter_name="temperature",
                    suggested_value=0.5,
                    expected_score=0.0,
                    confidence=0.0,
                    reason="exploration",
                    observations_used=0,
                )
            )

            results = ScenarioIsolationAuditor().audit_sqlite(db_path)
            by_store = {result.store_name: result for result in results}

            self.assertEqual(by_store["raw_logs"].scenario_ids, ["content", "quant"])
            self.assertEqual(by_store["summary_logs"].missing_scenario_id_count, 0)
            self.assertEqual(by_store["version_recommendations"].scenario_ids, ["quant"])
            self.assertEqual(by_store["parameter_suggestions"].scenario_ids, ["content"])

    def test_isolation_audit_cli_is_human_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v41.db"
            RawLogStore(db_path).save(
                "run-1",
                AgentRunRequest(scenario_id="quant", task="task"),
                AgentRunResult(
                    scenario_id="quant",
                    task="task",
                    answer="answer",
                    metrics={},
                    value_summary="value",
                    status="success",
                    run_id="run-1",
                ),
            )

            result = _run_cli(db_path, "isolation", "audit")

            self.assertIn("Scenario Isolation Audit", result.stdout)
            self.assertIn("raw_logs", result.stdout)
            self.assertIn("quant", result.stdout)


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
