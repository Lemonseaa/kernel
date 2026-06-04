"""Continuous-parameter optimization models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class OptimizationDirection(str, Enum):
    """Optimization direction."""

    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


class ParameterBounds(BaseModel):
    """Allowed range for one continuous parameter."""

    parameter_name: str
    minimum: float
    maximum: float
    step: float | None = None

    @model_validator(mode="after")
    def valid_range(self) -> "ParameterBounds":
        """Validate range values."""

        if self.maximum <= self.minimum:
            raise ValueError("maximum must be greater than minimum")
        if self.step is not None and self.step <= 0:
            raise ValueError("step must be positive")
        return self


class ParameterObservation(BaseModel):
    """Observed parameter value and resulting score."""

    parameter_name: str
    value: float
    score: float
    run_id: str | None = None
    evidence_id: str | None = None


class ParameterSuggestionStatus(str, Enum):
    """Human workflow status for a parameter suggestion."""

    OPEN = "open"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class ParameterSuggestion(BaseModel):
    """Suggested next value for a continuous parameter."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str
    target_id: str
    parameter_name: str
    suggested_value: float
    expected_score: float
    confidence: float
    reason: str
    observations_used: int
    direction: OptimizationDirection = OptimizationDirection.MAXIMIZE
    status: ParameterSuggestionStatus = ParameterSuggestionStatus.OPEN
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("reason")
    @classmethod
    def reason_required(cls, value: str) -> str:
        """Reject empty reasons."""

        if not value.strip():
            raise ValueError("reason is required")
        return value
