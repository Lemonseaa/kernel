"""Prompt version and proposal models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class PromptSlot(str, Enum):
    """Supported prompt slots."""

    ROLE = "role"
    GOAL = "goal"
    CONSTRAINTS = "constraints"
    OUTPUT_FORMAT = "output_format"
    STYLE = "style"
    EXAMPLES = "examples"
    TOOLS_POLICY = "tools_policy"


class PromptVersion(BaseModel):
    """A complete prompt snapshot for one scenario and agent."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str
    agent_id: str
    slots: dict[PromptSlot, str]
    reason: str
    parent_version_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @field_validator("reason")
    @classmethod
    def reason_required(cls, value: str) -> str:
        """Reject empty version reasons."""

        if not value.strip():
            raise ValueError("reason is required")
        return value


class PromptProposalStatus(str, Enum):
    """Lifecycle status for prompt proposals."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    CANCELLED = "cancelled"


class PromptPatch(BaseModel):
    """Bounded prompt patch targeting one slot."""

    slot: PromptSlot
    operation: Literal["add", "remove", "replace", "compress", "refactor"]
    before: str
    after: str


class PromptProposal(BaseModel):
    """Manual prompt proposal. Patch-first, not whole-prompt-first."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str
    agent_id: str
    patch: PromptPatch
    reason: str
    expected_metric: str
    status: PromptProposalStatus = PromptProposalStatus.PROPOSED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @field_validator("reason", "expected_metric")
    @classmethod
    def required_text(cls, value: str) -> str:
        """Reject empty required text fields."""

        if not value.strip():
            raise ValueError("reason and expected_metric are required")
        return value
