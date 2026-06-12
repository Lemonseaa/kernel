"""Evaluation runner."""

from __future__ import annotations

from loop_harness.evaluation.evaluator import Evaluator
from loop_harness.evaluation.platform import PlatformEvaluator
from loop_harness.evaluation.readability import ReadabilityEvaluator
from loop_harness.evaluation.result import EvaluationResult
from loop_harness.evaluation.seo import SEOEvaluator


class EvaluationRunner:
    """Run all configured evaluators for a content artifact."""

    def __init__(self, evaluators: list[Evaluator] | None = None) -> None:
        """Create a runner with default quality evaluators."""

        self.evaluators = evaluators or [ReadabilityEvaluator(), SEOEvaluator(), PlatformEvaluator()]

    def run(self, content: str, platform: str = "public") -> list[EvaluationResult]:
        """Run all evaluators."""

        return [evaluator.evaluate(content, platform=platform) for evaluator in self.evaluators]

    def overall_score(self, results: list[EvaluationResult]) -> float:
        """Calculate average evaluation score."""

        if not results:
            return 0.0
        return round(sum(result.score for result in results) / len(results), 2)

    def passed_all(self, results: list[EvaluationResult], min_score: float = 70.0) -> bool:
        """Return true when every evaluator and overall score pass."""

        return all(result.score >= min_score for result in results)
