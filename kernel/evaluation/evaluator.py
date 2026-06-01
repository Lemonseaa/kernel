"""Evaluator abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod

from kernel.evaluation.result import EvaluationResult


class Evaluator(ABC):
    """Base class for content quality evaluators."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return evaluator name."""

    @abstractmethod
    def evaluate(self, content: str, platform: str = "public") -> EvaluationResult:
        """Evaluate content and return a score."""

    @staticmethod
    def _clamp(score: float) -> float:
        """Clamp score into a 0-100 range."""

        return max(0.0, min(100.0, score))
