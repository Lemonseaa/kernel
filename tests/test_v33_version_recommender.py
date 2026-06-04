"""V3.3 evidence-based version recommendation tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.metrics import ComparisonResult
from checkpoint_ai.recommendation import (
    RecommendationDecision,
    RecommendationStatus,
    VersionRecommendation,
    VersionRecommendationStore,
    VersionRecommender,
)
from checkpoint_ai.reporting import ReportGenerator
from checkpoint_ai.shadow import ShadowResult, ShadowResultStore


class V33VersionRecommenderTest(unittest.TestCase):
    """Validate evidence-based version recommendations."""

    def test_recommendation_store_saves_lists_and_updates_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = VersionRecommendationStore(Path(tmp) / "recommendations.db")
            recommendation = VersionRecommendation(
                scenario_id="quant",
                target_id="strategy.fast_window",
                proposal_id="proposal-1",
                decision=RecommendationDecision.RECOMMEND,
                confidence=0.81,
                objective_score=0.22,
                reason="historical evidence improved with enough samples.",
                recommended_action="approve_for_shadow_or_paper",
                source_shadow_ids=["shadow-1"],
                evidence={"run_kind": "historical", "sample_count": 90},
            )

            store.save(recommendation)
            loaded = store.get(recommendation.id)
            listed = store.list(scenario_id="quant")
            updated = store.update_status(recommendation.id, RecommendationStatus.ACCEPTED)

            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.decision, RecommendationDecision.RECOMMEND)
            self.assertEqual([item.id for item in listed], [recommendation.id])
            self.assertTrue(updated)
            updated_loaded = store.get(recommendation.id)
            self.assertIsNotNone(updated_loaded)
            assert updated_loaded is not None
            self.assertEqual(updated_loaded.status, RecommendationStatus.ACCEPTED)

    def test_recommender_refuses_synthetic_shadow_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "recommendations.db"
            shadows = ShadowResultStore(db_path)
            recommendations = VersionRecommendationStore(db_path)
            shadows.save(
                _shadow(
                    proposal_id="proposal-1",
                    comparison=ComparisonResult(
                        objective_score=0.9,
                        improved=True,
                        business_metric_diffs={"sharpe": 3.0},
                        run_kind="synthetic",
                        provenance={"sample_count": 260},
                    ),
                )
            )

            recommendation = VersionRecommender(shadows, recommendations).recommend_for_scenario("quant")

            self.assertEqual(recommendation.decision, RecommendationDecision.INSUFFICIENT_EVIDENCE)
            self.assertIn("synthetic", recommendation.reason)

    def test_recommender_recommends_best_historical_improvement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "recommendations.db"
            shadows = ShadowResultStore(db_path)
            recommendations = VersionRecommendationStore(db_path)
            shadows.save(
                _shadow(
                    proposal_id="proposal-1",
                    comparison=ComparisonResult(
                        objective_score=0.08,
                        improved=True,
                        business_metric_diffs={"sharpe": 0.08, "total_return": 0.03},
                        run_kind="historical",
                        provenance={"sample_count": 60},
                    ),
                )
            )
            shadows.save(
                _shadow(
                    proposal_id="proposal-2",
                    comparison=ComparisonResult(
                        objective_score=0.22,
                        improved=True,
                        business_metric_diffs={"sharpe": 0.4, "total_return": 0.08},
                        run_kind="historical",
                        provenance={"sample_count": 90},
                    ),
                )
            )

            recommendation = VersionRecommender(shadows, recommendations).recommend_for_scenario("quant")

            self.assertEqual(recommendation.decision, RecommendationDecision.RECOMMEND)
            self.assertEqual(recommendation.proposal_id, "proposal-2")
            self.assertGreaterEqual(recommendation.confidence, 0.6)

    def test_recommender_rejects_guardrail_violation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "recommendations.db"
            shadows = ShadowResultStore(db_path)
            recommendations = VersionRecommendationStore(db_path)
            shadows.save(
                _shadow(
                    proposal_id="proposal-1",
                    comparison=ComparisonResult(
                        objective_score=0.5,
                        improved=True,
                        business_metric_diffs={"max_drawdown": 0.3},
                        guardrail_violations=["max_drawdown"],
                        run_kind="historical",
                        provenance={"sample_count": 90},
                    ),
                )
            )

            recommendation = VersionRecommender(shadows, recommendations).recommend_for_scenario("quant")

            self.assertEqual(recommendation.decision, RecommendationDecision.REJECT)
            self.assertIn("max_drawdown", recommendation.reason)

    def test_report_generator_prints_recommendation_detail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "recommendations.db"
            store = VersionRecommendationStore(db_path)
            recommendation = VersionRecommendation(
                scenario_id="quant",
                target_id="strategy",
                proposal_id="proposal-1",
                decision=RecommendationDecision.RECOMMEND,
                confidence=0.7,
                objective_score=0.2,
                reason="historical evidence improved with enough samples.",
                recommended_action="approve_for_shadow_or_paper",
                source_shadow_ids=["shadow-1"],
                evidence={"run_kind": "historical", "sample_count": 90},
            )
            store.save(recommendation)

            report = ReportGenerator(db_path).recommendation(recommendation.id)

            self.assertIn("Recommendation Report", report)
            self.assertIn("decision: recommend", report)
            self.assertIn("confidence: 0.7", report)
            self.assertIn("source_shadow_ids", report)

    def test_recommendation_cli_runs_lists_and_updates_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "recommendations.db"
            shadows = ShadowResultStore(db_path)
            shadows.save(
                _shadow(
                    proposal_id="proposal-1",
                    comparison=ComparisonResult(
                        objective_score=0.22,
                        improved=True,
                        business_metric_diffs={"sharpe": 0.4, "total_return": 0.08},
                        run_kind="historical",
                        provenance={"sample_count": 90},
                    ),
                )
            )

            created = _run_cli(db_path, "recommendation", "run", "--scenario-id", "quant")
            recommendation_id = _extract_created_id(created.stdout)
            listed = _run_cli(db_path, "recommendation", "list", "--scenario-id", "quant")
            shown = _run_cli(db_path, "recommendation", "show", recommendation_id)
            accepted = _run_cli(db_path, "recommendation", "accept", recommendation_id)

            self.assertIn("Recommendation created", created.stdout)
            self.assertIn("decision: recommend", created.stdout)
            self.assertIn(recommendation_id, listed.stdout)
            self.assertIn("Recommendation Report", shown.stdout)
            self.assertIn("accepted", accepted.stdout)


def _shadow(proposal_id: str, comparison: ComparisonResult) -> ShadowResult:
    return ShadowResult(
        proposal_id=proposal_id,
        scenario_id="quant",
        agent_id="strategy",
        run_id=f"run-{proposal_id}",
        status="success",
        passed=True,
        answer="shadow answer",
        value_summary="shadow value",
        comparison_result=comparison.model_dump(mode="json"),
        business_metric_diff=comparison.business_metric_diffs,
        run_kind=comparison.run_kind,
        provenance=comparison.provenance,
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


def _extract_created_id(output: str) -> str:
    for line in output.splitlines():
        if line.startswith("Recommendation created:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"recommendation id not found:\n{output}")


if __name__ == "__main__":
    unittest.main()
