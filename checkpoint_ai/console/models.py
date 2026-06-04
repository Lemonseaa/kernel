"""Console read model contracts."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from checkpoint_ai.isolation import ScenarioScope


class ConsoleScenarioSummary(BaseModel):
    """One scenario row for the human console."""

    scenario_id: str
    name: str
    status: str
    adapter_type: str
    business_line_id: str | None = None
    domain_tags: list[str] = Field(default_factory=list)


class ConsoleRunSummary(BaseModel):
    """One recent run row for the human console."""

    run_id: str
    scenario_id: str
    task: str
    status: str
    value_summary: str
    metrics: dict[str, object] = Field(default_factory=dict)
    created_at: str


class ConsoleSnapshot(BaseModel):
    """Aggregated operator snapshot for one scope."""

    scope: ScenarioScope
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    scenario_count: int
    active_scenario_count: int
    archived_scenario_count: int
    recent_run_count: int
    failed_run_count: int
    pending_approval_count: int
    scenarios: list[ConsoleScenarioSummary] = Field(default_factory=list)
    latest_runs: list[ConsoleRunSummary] = Field(default_factory=list)
    pending_items: list[dict[str, object]] = Field(default_factory=list)
    operator_summary: str
