"""Autonomy action ledger models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class AutonomyActionStatus(str, Enum):
    """Lifecycle state for a low-risk autonomous action."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class AutonomyActionLog(BaseModel):
    """Auditable record for one autonomous action."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str
    proposal_id: str
    action_type: str
    checkpoint_id: str
    reason: str
    status: AutonomyActionStatus = AutonomyActionStatus.PENDING
    result: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("scenario_id", "proposal_id", "action_type", "checkpoint_id", "reason")
    @classmethod
    def required_text(cls, value: str) -> str:
        """Reject empty action ledger fields."""

        if not value.strip():
            raise ValueError("autonomy action fields are required")
        return value
