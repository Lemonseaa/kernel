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

    def list(self, business_line_id: str | None = None) -> list[Agent]:
        """List registered agents, optionally scoped to one BusinessLine."""

        if business_line_id is None:
            return list(self._agents.values())
        return [
            agent
            for agent in self._agents.values()
            if agent.business_line_id == business_line_id
        ]

    def get(self, agent_id: str, business_line_id: str | None = None) -> Agent | None:
        """Get an agent by id, optionally scoped to one BusinessLine."""

        agent = self._agents.get(agent_id)
        if agent is None:
            return None
        if business_line_id is not None and agent.business_line_id != business_line_id:
            return None
        return agent

    def find_by_capability(self, capability: str, business_line_id: str | None = None) -> list[Agent]:
        """Find all registered agents that expose a capability."""

        return [
            agent
            for agent in self._agents.values()
            if capability in agent.capabilities
            and (business_line_id is None or agent.business_line_id == business_line_id)
        ]

    def create_agent_for_capability(self, capability: str) -> BaseAgent | None:
        """Instantiate an executable agent by capability."""

        agent_class = self._agent_classes.get(capability)
        if agent_class is None:
            return None
        return agent_class()
