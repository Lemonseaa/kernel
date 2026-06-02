"""BusinessLine template models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AgentTemplate:
    """Template metadata for an Agent."""

    id: str
    name: str
    role: str
    capabilities: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WorkflowTemplate:
    """Template metadata for a workflow."""

    id: str
    name: str
    task_descriptions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class BusinessLineTemplate:
    """Template used to create a BusinessLine."""

    id: str
    name: str
    description: str = ""
    agents: list[AgentTemplate] = field(default_factory=list)
    workflows: list[WorkflowTemplate] = field(default_factory=list)
    evaluation_rules: list[str] = field(default_factory=list)
    policy_ids: list[str] = field(default_factory=list)
