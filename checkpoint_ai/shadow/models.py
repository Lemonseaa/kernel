"""Shadow run models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ShadowResult(BaseModel):
    """Stored shadow run result with baseline comparison."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str
    scenario_id: str
    agent_id: str
    run_id: str
    is_shadow: bool = True
    status: Literal["success", "failed"]
    passed: bool
    answer: str
    value_summary: str
    baseline_metrics: dict[str, Any] = Field(default_factory=dict)
    shadow_metrics: dict[str, Any] = Field(default_factory=dict)
    metric_diff: dict[str, float] = Field(default_factory=dict)
    comparison_result: dict[str, Any] = Field(default_factory=dict)
    business_metric_diff: dict[str, float] = Field(default_factory=dict)
    run_kind: str = "synthetic"
    provenance: dict[str, Any] = Field(default_factory=dict)
    error_type: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
