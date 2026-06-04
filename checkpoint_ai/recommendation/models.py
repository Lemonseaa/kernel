"""Recommendation models for evidence-based version selection."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RecommendationDecision(str, Enum):
    """Recommendation decision."""

    RECOMMEND = "recommend"
    REJECT = "reject"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class RecommendationStatus(str, Enum):
    """Human workflow status for a recommendation."""

    OPEN = "open"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class VersionRecommendation(BaseModel):
    """Auditable recommendation for an existing proposal or version."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str
    target_id: str
    proposal_id: str | None = None
    decision: RecommendationDecision
    status: RecommendationStatus = RecommendationStatus.OPEN
    confidence: float
    objective_score: float
    reason: str
    recommended_action: str
    source_shadow_ids: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
