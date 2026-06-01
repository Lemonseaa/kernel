"""Agent registry."""

from __future__ import annotations

from kernel.models import Agent
from kernel.runtime.base import BaseAgent


class AgentRegistry:
    """Track agents and find them by capability."""

    def __init__(self) -> None:
        """Create an empty agent registry."""

        self._agents: dict[str, Agent] = {}
        self._agent_classes: dict[str, type[BaseAgent]] = {}

    def register(self, agent: Agent) -> None:
        """Register an agent metadata object."""

        self._agents[agent.id] = agent

    def register_agent_class(self, agent_class: type[BaseAgent]) -> None:
        """Register an executable agent class."""

        instance = agent_class()
        model = instance.to_model()
        self.register(model)
        for capability in model.capabilities:
            self._agent_classes[capability] = agent_class

    def unregister(self, agent_id: str) -> None:
        """Remove an agent from the registry."""

        self._agents.pop(agent_id, None)

    def get(self, agent_id: str) -> Agent | None:
        """Get an agent by id."""

        return self._agents.get(agent_id)

    def find_by_capability(self, capability: str) -> list[Agent]:
        """Find all registered agents that expose a capability."""

        return [agent for agent in self._agents.values() if capability in agent.capabilities]

    def create_agent_for_capability(self, capability: str) -> BaseAgent | None:
        """Instantiate an executable agent by capability."""

        agent_class = self._agent_classes.get(capability)
        if agent_class is None:
            return None
        return agent_class()
