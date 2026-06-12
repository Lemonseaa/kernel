"""Scenario policy models for prompt proposals."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class PolicyLevel(str, Enum):
    """Policy decision levels."""

    AUTO = "auto"
    APPROVAL = "approval"
    BLOCKED = "blocked"


class PolicyDecision(BaseModel):
    """Policy evaluation result."""

    proposal_id: str
    level: PolicyLevel
    reason: str


class PolicyProcessResult(BaseModel):
    """Result of policy + shadow gate processing."""

    proposal_id: str
    level: PolicyLevel
    policy_reason: str
    shadow_required: bool
    shadow_ran: bool
    shadow_passed: bool | None = None
    action: str
