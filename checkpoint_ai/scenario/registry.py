"""Scenario registry."""

from __future__ import annotations

from checkpoint_ai.scenario.models import Scenario


class ScenarioRegistry:
    """In-memory scenario registry for V2.1 contract execution."""

    def __init__(self) -> None:
        self._scenarios: dict[str, Scenario] = {}

    def create(self, scenario: Scenario) -> Scenario:
        """Create or replace a scenario."""

        self._scenarios[scenario.id] = scenario
        return scenario

    def get(self, scenario_id: str) -> Scenario:
        """Load a scenario or raise a clear error."""

        try:
            return self._scenarios[scenario_id]
        except KeyError as exc:
            raise KeyError(f"Scenario not found: {scenario_id}") from exc

    def list(self) -> list[Scenario]:
        """List scenarios in insertion order."""

        return list(self._scenarios.values())
