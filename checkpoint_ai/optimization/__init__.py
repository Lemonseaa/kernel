"""Isolated continuous parameter optimization support.

Optimization remains advisory. It may suggest bounded candidate values from
evidence, but execution still goes through comparison, policy, and decision
records.
"""

from checkpoint_ai.optimization.bayesian import SimpleBayesianOptimizer
from checkpoint_ai.optimization.models import (
    OptimizationDirection,
    ParameterBounds,
    ParameterObservation,
    ParameterSuggestion,
    ParameterSuggestionStatus,
)
from checkpoint_ai.optimization.store import ParameterSuggestionStore

CLEANUP_STATUS = "isolate"
REPLACEMENT_PATH = "bounded candidate suggestions after evidence review"

__all__ = [
    "OptimizationDirection",
    "ParameterBounds",
    "ParameterObservation",
    "ParameterSuggestion",
    "ParameterSuggestionStatus",
    "ParameterSuggestionStore",
    "SimpleBayesianOptimizer",
]
