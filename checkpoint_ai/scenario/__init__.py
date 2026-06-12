"""Scenario models, registry, and runner.

Scenario is the main evidence scope for runs, metrics, prompts, reports, and
decisions. Keep it focused on evidence isolation, not multi-tenant platform
management.
"""

from checkpoint_ai.scenario.models import Scenario, ScenarioStatus
from checkpoint_ai.scenario.registry import ScenarioRegistry
from checkpoint_ai.scenario.runner import ScenarioRunner
from checkpoint_ai.scenario.store import ScenarioStore

CLEANUP_STATUS = "evidence_support"
REPLACEMENT_PATH = "evidence scenario scope"

__all__ = ["Scenario", "ScenarioRegistry", "ScenarioRunner", "ScenarioStatus", "ScenarioStore"]
