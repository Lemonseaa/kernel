"""Evaluation gate."""

from __future__ import annotations

from kernel.evaluation.result import EvaluationResult
from kernel.evaluation.runner import EvaluationRunner


class EvaluationGate:
    """Quality gate for generated content."""

    def __init__(self, runner: EvaluationRunner, auto_retry: bool = False) -> None:
        """Create an evaluation gate."""

        self.runner = runner
        self.auto_retry = auto_retry

    def check(
        self,
        content: str,
        platform: str = "public",
        min_score: float = 70.0,
    ) -> tuple[bool, list[EvaluationResult]]:
        """Evaluate content and return pass/fail with raw results."""

        results = self.runner.run(content, platform=platform)
        return self.runner.passed_all(results, min_score=min_score), results

    def get_suggestions(self, results: list[EvaluationResult]) -> list[str]:
        """Collect all improvement suggestions."""

        suggestions: list[str] = []
        for result in results:
            suggestions.extend(result.suggestions)
        return suggestions
