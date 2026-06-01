"""Base agent runtime abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod

from kernel.models import Agent, Artifact, Task


class BaseAgent(ABC):
    """Abstract base class for executable agents."""

    name: str = "base"
    role: str = "Base Agent"
    capabilities: set[str] = set()

    def to_model(self) -> Agent:
        """Return registry metadata for this agent."""

        return Agent(name=self.name, role=self.role, capabilities=set(self.capabilities))

    @abstractmethod
    def execute(self, task: Task) -> Artifact:
        """Execute a task and return an artifact."""


class SimpleAgent(BaseAgent):
    """Default executable agent for simple task specs."""

    name = "simple"
    role = "Simple Agent"
    capabilities = {"simple.execute"}

    def execute(self, task: Task) -> Artifact:
        """Echo task input or description as a text artifact."""

        content = task.input if task.input is not None else task.name
        return Artifact(task_id=task.id, run_id=task.run_id or "", kind="text", content=content)
