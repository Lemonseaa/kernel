"""Evaluation result contracts."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class EvaluationResult:
    """A single evaluator result."""

    name: str
    score: float
    passed: bool
    details: dict[str, object] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)
