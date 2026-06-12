"""Frozen legacy cross-scenario insight previews.

Automatic cross-scenario learning is paused. If this concept returns, it
should re-enter as evidence-backed review suggestions with clear rejection
criteria, not as autonomous migration logic.
"""

from loop_harness.insights.cross_scenario import (
    CrossScenarioInsight,
    CrossScenarioInsightDecision,
    CrossScenarioInsightGenerator,
    ScenarioInsightInput,
)
from loop_harness.insights.store import CrossScenarioInsightStore

LEGACY_STATUS = "frozen"
REPLACEMENT_PATH = "evidence-backed review suggestions"

__all__ = [
    "CrossScenarioInsight",
    "CrossScenarioInsightDecision",
    "CrossScenarioInsightGenerator",
    "CrossScenarioInsightStore",
    "ScenarioInsightInput",
]
