"""Config versioning and branching models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ConfigVersion(BaseModel):
    """Immutable configuration snapshot once locked."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    business_line_id: str
    scenario_id: str
    config: dict[str, Any] = Field(default_factory=dict)
    reason: str
    parent_version_id: str | None = None
    locked: bool = False
    locked_reason: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("business_line_id", "scenario_id", "reason")
    @classmethod
    def required_text(cls, value: str) -> str:
        """Reject unscoped versions."""

        if not value.strip():
            raise ValueError("config version scope and reason are required")
        return value


class ConfigBranch(BaseModel):
    """Optimization branch based on a locked config version."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    business_line_id: str
    scenario_id: str
    name: str
    base_version_id: str
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)
