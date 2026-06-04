"""Scenario model for bounded Agent optimization domains."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class Scenario(BaseModel):
    """A scenario binds one optimization domain to one adapter type."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    adapter_type: str
    business_line_id: str | None = None
    adapter_config: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
