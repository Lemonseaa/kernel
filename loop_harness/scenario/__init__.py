"""Scenario models, registry, and runner.

Scenario is the main evidence scope for runs, metrics, prompts, reports, and
decisions. Keep it focused on evidence isolation, not multi-tenant platform
management.
"""

from loop_harness.scenario.models import Scenario, ScenarioStatus
from loop_harness.scenario.registry import ScenarioRegistry
from loop_harness.scenario.runner import ScenarioRunner
from loop_harness.scenario.store import ScenarioStore

CLEANUP_STATUS = "evidence_support"
REPLACEMENT_PATH = "evidence scenario scope"

__all__ = ["Scenario", "ScenarioRegistry", "ScenarioRunner", "ScenarioStatus", "ScenarioStore"]
