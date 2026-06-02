"""Agent model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class AgentState(str, Enum):
    """Agent runtime states."""

    IDLE = "idle"
    BUSY = "busy"
    STOPPED = "stopped"
    FAILED = "failed"


@dataclass(slots=True)
class Agent:
    """Registered agent metadata."""

    name: str
    role: str
    capabilities: set[str]
    business_line_id: str = "default"
    id: str = field(default_factory=lambda: str(uuid4()))
    state: AgentState = AgentState.IDLE
    current_task: str | None = None
