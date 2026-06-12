"""Human-owned user preference profile models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class UserProfileVersion(BaseModel):
    """Auditable formal profile version."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    actor: str
    reason: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class SuggestedProfileNotes(BaseModel):
    """Hermes draft notes that are never formal constraints."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    actor: str = "hermes"
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)
