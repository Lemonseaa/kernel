"""Decision audit models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DecisionKind(str, Enum):
    """Auditable decision or system outcome kind."""

    APPROVE = "approve"
    REJECT = "reject"
    ERROR = "error"
    BLOCKED = "blocked"
    SYSTEM = "system"


class DecisionRecord(BaseModel):
    """One auditable decision, rejection, or system safety event."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    source_type: str
    kind: DecisionKind
    scenario_id: str | None = None
    actor: str = "system"
    action: str
    comment: str
    before: dict[str, Any] = Field(default_factory=dict)
    after: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
