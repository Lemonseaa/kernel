"""Scenario query scope contracts."""

from __future__ import annotations

from pydantic import BaseModel, model_validator


class ScenarioScope(BaseModel):
    """Explicit scope for scenario-bound queries."""

    scenario_id: str | None = None
    allow_cross_scenario: bool = False
    reason: str | None = None

    @classmethod
    def cross_scenario(cls, reason: str) -> "ScenarioScope":
        """Create a cross-scenario scope with an audit reason."""

        if not reason.strip():
            raise ValueError("cross-scenario scope requires reason")
        return cls(allow_cross_scenario=True, reason=reason)

    @model_validator(mode="after")
    def validate_scope(self) -> "ScenarioScope":
        """Ensure ordinary scopes include one scenario id."""

        if self.allow_cross_scenario:
            if not self.reason or not self.reason.strip():
                raise ValueError("cross-scenario scope requires reason")
        elif not self.scenario_id:
            raise ValueError("scenario_id is required unless cross-scenario is allowed")
        return self
