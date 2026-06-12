"""BusinessLine models."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class BusinessLineStatus(str, Enum):
    """BusinessLine lifecycle states.

    CREATE is an operation, not a durable state. A created line enters ACTIVE.
    """

    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass(slots=True)
class ResourceLimits:
    """Per-BusinessLine resource limits."""

    max_concurrent_runs: int = 10
    max_agents: int = 50


@dataclass(slots=True)
class BusinessLineConfig:
    """Per-BusinessLine configuration."""

    evaluation_rules: list[str] = field(default_factory=list)
    agent_templates: list[str] = field(default_factory=list)
    workflow_templates: list[str] = field(default_factory=list)
    policy_ids: list[str] = field(default_factory=list)
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)


@dataclass(slots=True)
class BusinessLine:
    """A first-class, isolated Loop Harness business line."""

    name: str
    id: str = field(default_factory=lambda: str(uuid4()))
    status: BusinessLineStatus = BusinessLineStatus.ACTIVE
    config: BusinessLineConfig = field(default_factory=BusinessLineConfig)
    created_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)
