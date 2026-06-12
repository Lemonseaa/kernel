"""Built-in Agent configuration models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class AgentRole(str, Enum):
    """Internal optimization-system roles."""

    OBSERVER = "observer"
    PROPOSER = "proposer"
    VALIDATOR = "validator"
    SAFETY_MONITOR = "safety_monitor"


class AgentConfig(BaseModel):
    """Business-line scoped internal Agent configuration."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    business_line_id: str
    role: AgentRole
    config_version_id: str
    skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    mcp_servers: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    model: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("business_line_id", "config_version_id", "model")
    @classmethod
    def required_text(cls, value: str) -> str:
        """Reject unscoped agent configs."""

        if not value.strip():
            raise ValueError("agent config scope fields are required")
        return value


class AgentRuntimeContext(BaseModel):
    """Context visible to an internal Agent."""

    formal_user_profile: str
    suggested_notes: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
