"""V3.4 Bayesian optimization spike tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from loop_harness.optimization import (
    OptimizationDirection,
    ParameterBounds,
    ParameterObservation,
    ParameterSuggestion,
    ParameterSuggestionStore,
    SimpleBayesianOptimizer,
)
from tests.helpers import project_root


class V34BayesianOptimizationTest(unittest.TestCase):
    """Validate conservative continuous-parameter suggestions."""

    def test_optimizer_suggests_in_bounds_candidate_not_already_observed(self) -> None:
        optimizer = SimpleBayesianOptimizer(grid_size=21)
        observations = [
            ParameterObservation(parameter_name="temperature", value=0.1, score=0.2),
            ParameterObservation(parameter_name="temperature", value=0.4, score=0.7),
            ParameterObservation(parameter_name="temperature", value=0.9, score=0.3),
        ]

        suggestion = optimizer.suggest(
            scenario_id="content",
            target_id="writer.temperature",
            bounds=ParameterBounds(
                parameter_name="temperature",
                minimum=0.0,
                maximum=1.0,
                step=0.05,
            ),
            observations=observations,
        )

        self.assertGreaterEqual(suggestion.suggested_value, 0.0)
        self.assertLessEqual(suggestion.suggested_value, 1.0)
        self.assertNotIn(suggestion.suggested_value, {0.1, 0.4, 0.9})
        self.assertEqual(suggestion.direction, OptimizationDirection.MAXIMIZE)
        self.assertIn("surrogate", suggestion.reason)

    def test_optimizer_explores_midpoint_when_evidence_is_too_sparse(self) -> None:
        optimizer = SimpleBayesianOptimizer(grid_size=11)

        suggestion = optimizer.suggest(
            scenario_id="quant",
            target_id="strategy.risk_threshold",
            bounds=ParameterBounds(
                parameter_name="risk_threshold",
                minimum=0.0,
                maximum=1.0,
                step=0.1,
            ),
            observations=[],
        )

        self.assertEqual(suggestion.suggested_value, 0.5)
        self.assertEqual(suggestion.confidence, 0.0)
        self.assertIn("exploration", suggestion.reason)

    def test_optimizer_supports_minimize_direction(self) -> None:
        optimizer = SimpleBayesianOptimizer(grid_size=21)
        observations = [
            ParameterObservation(parameter_name="latency_ms", value=100.0, score=100.0),
            ParameterObservation(parameter_name="latency_ms", value=200.0, score=200.0),
            ParameterObservation(parameter_name="latency_ms", value=300.0, score=300.0),
        ]

        suggestion = optimizer.suggest(
            scenario_id="runtime",
            target_id="provider.timeout",
            bounds=ParameterBounds(
                parameter_name="latency_ms",
                minimum=50.0,
                maximum=350.0,
                step=10.0,
            ),
            observations=observations,
            direction=OptimizationDirection.MINIMIZE,
        )

        self.assertLess(suggestion.expected_score, 200.0)
        self.assertEqual(suggestion.direction, OptimizationDirection.MINIMIZE)

    def test_suggestion_store_saves_and_lists_by_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ParameterSuggestionStore(Path(tmp) / "optimization.db")
            suggestion = ParameterSuggestion(
                scenario_id="quant",
                target_id="strategy.fast_window",
                parameter_name="fast_window",
                suggested_value=12.0,
                expected_score=0.4,
                confidence=0.5,
                reason="surrogate optimum from 4 observations.",
                observations_used=4,
            )

            store.save(suggestion)
            loaded = store.get(suggestion.id)
            listed = store.list(scenario_id="quant")

            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.parameter_name, "fast_window")
            self.assertEqual([item.id for item in listed], [suggestion.id])

    def test_optimization_cli_suggests_and_lists_parameter_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "optimization.db"
            suggested = _run_cli(
                db_path,
                "optimization",
                "suggest",
                "--scenario-id",
                "quant",
                "--target-id",
                "strategy.fast_window",
                "--parameter-name",
                "fast_window",
                "--min",
                "4",
                "--max",
                "20",
                "--step",
                "1",
                "--observations-json",
                '[{"value": 8, "score": 0.1}, {"value": 12, "score": 0.4}, {"value": 16, "score": 0.2}]',
            )
            listed = _run_cli(db_path, "optimization", "list", "--scenario-id", "quant")

            self.assertIn("Parameter suggestion created", suggested.stdout)
            self.assertIn("fast_window", suggested.stdout)
            self.assertIn("Parameter Suggestions", listed.stdout)
            self.assertIn("strategy.fast_window", listed.stdout)


def _run_cli(db_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
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
