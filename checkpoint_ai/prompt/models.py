"""Prompt version and proposal models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal

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
    metadata: dict[str, Any] = Field(default_factory=dict)

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


class ProposalKind(str, Enum):
    """Generic proposal kind."""

    PROMPT = "prompt"
    STRATEGY = "strategy"
    PARAMETER = "parameter"
    DEPLOYMENT = "deployment"


class ProposalTargetType(str, Enum):
    """What a generic proposal targets."""

    PROMPT_SLOT = "prompt_slot"
    STRATEGY_PARAM = "strategy_param"
    ADAPTER_CONFIG = "adapter_config"
    DEPLOYMENT = "deployment"


class ProposalStatus(str, Enum):
    """Generic proposal lifecycle status."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    CANCELLED = "cancelled"


class ProposalPatch(BaseModel):
    """Patch for any proposal target."""

    operation: Literal["add", "remove", "replace", "compress", "refactor"]
    before: Any
    after: Any


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
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason", "expected_metric")
    @classmethod
    def required_text(cls, value: str) -> str:
        """Reject empty required text fields."""

        if not value.strip():
            raise ValueError("reason and expected_metric are required")
        return value


class Proposal(BaseModel):
    """Generic proposal contract used by V3 learning layers."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str
    proposal_kind: ProposalKind
    target_type: ProposalTargetType
    target_id: str
    patch: ProposalPatch
    reason: str
    expected_metric: str
    status: ProposalStatus = ProposalStatus.PROPOSED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("reason", "expected_metric", "target_id")
    @classmethod
    def generic_required_text(cls, value: str) -> str:
        """Reject empty required generic proposal text fields."""

        if not value.strip():
            raise ValueError("target_id, reason and expected_metric are required")
        return value

    @classmethod
    def from_prompt_proposal(cls, proposal: PromptProposal) -> Proposal:
        """Convert legacy PromptProposal into the generic proposal contract."""

        return cls(
            id=proposal.id,
            scenario_id=proposal.scenario_id,
            proposal_kind=ProposalKind.PROMPT,
            target_type=ProposalTargetType.PROMPT_SLOT,
            target_id=f"{proposal.agent_id}.{proposal.patch.slot.value}",
            patch=ProposalPatch(
                operation=proposal.patch.operation,
                before=proposal.patch.before,
                after=proposal.patch.after,
            ),
            reason=proposal.reason,
            expected_metric=proposal.expected_metric,
            status=ProposalStatus(proposal.status.value),
            created_at=proposal.created_at,
            updated_at=proposal.updated_at,
            metadata={**proposal.metadata, "agent_id": proposal.agent_id},
        )
