"""Simple plugin registry."""

from __future__ import annotations

from typing import Any


class PluginRegistry:
    """Register and look up plugin classes.

    This registry stores already-imported classes. It does not perform dynamic
    loading, sandboxing, or hot unloading.
    """

    def __init__(self) -> None:
        """Create empty plugin registries."""

        self._agents: dict[str, type[Any]] = {}
        self._tools: dict[str, type[Any]] = {}
        self._evaluators: dict[str, type[Any]] = {}
        self._providers: dict[str, type[Any]] = {}

    def register_agent(self, name: str, agent_class: type[Any]) -> None:
        """Register an Agent plugin class."""

        self._agents[name] = agent_class

    def register_tool(self, name: str, tool_class: type[Any]) -> None:
        """Register a Tool plugin class."""

        self._tools[name] = tool_class

    def register_evaluator(self, name: str, evaluator_class: type[Any]) -> None:
        """Register an Evaluator plugin class."""

        self._evaluators[name] = evaluator_class

    def register_provider(self, name: str, provider_class: type[Any]) -> None:
        """Register an LLM Provider plugin class."""

        self._providers[name] = provider_class

    def get_agent(self, name: str) -> type[Any] | None:
        """Return an Agent plugin class by name."""

        return self._agents.get(name)

    def get_tool(self, name: str) -> type[Any] | None:
        """Return a Tool plugin class by name."""

        return self._tools.get(name)

    def get_evaluator(self, name: str) -> type[Any] | None:
        """Return an Evaluator plugin class by name."""

        return self._evaluators.get(name)

    def get_provider(self, name: str) -> type[Any] | None:
        """Return an LLM Provider plugin class by name."""

        return self._providers.get(name)

    def list_agents(self) -> list[str]:
        """List registered Agent plugin names."""

        return list(self._agents.keys())

    def list_tools(self) -> list[str]:
        """List registered Tool plugin names."""

        return list(self._tools.keys())

    def list_evaluators(self) -> list[str]:
        """List registered Evaluator plugin names."""

        return list(self._evaluators.keys())

    def list_providers(self) -> list[str]:
        """List registered Provider plugin names."""

        return list(self._providers.keys())
