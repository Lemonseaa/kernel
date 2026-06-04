"""Adapter registry for V2.1 scenario execution."""

from __future__ import annotations

from checkpoint_ai.adapter.base import AgentAdapter
from checkpoint_ai.adapter.capabilities import AdapterCapabilities, AdapterDescription


class AdapterRegistry:
    """Register and resolve Agent adapters by adapter name."""

    def __init__(self) -> None:
        self._adapters: dict[str, AgentAdapter] = {}

    def register(self, adapter: AgentAdapter) -> None:
        """Register one adapter."""

        self._adapters[adapter.name] = adapter

    def resolve(self, adapter_type: str) -> AgentAdapter:
        """Resolve an adapter or raise a clear error."""

        try:
            return self._adapters[adapter_type]
        except KeyError as exc:
            raise KeyError(f"Adapter not found: {adapter_type}") from exc

    def list_adapters(self) -> list[str]:
        """List registered adapter names in insertion order."""

        return list(self._adapters)

    def capabilities_for(self, adapter_type: str) -> AdapterCapabilities:
        """Return structured capabilities for one adapter."""

        return self.resolve(adapter_type).capabilities()

    def supports(self, adapter_type: str, capability: str) -> bool:
        """Return whether the adapter fully supports a capability."""

        return self.capabilities_for(adapter_type).supports(capability)

    def describe(self) -> list[AdapterDescription]:
        """Return human-readable descriptions for all adapters."""

        return [
            AdapterDescription(
                name=adapter.name,
                supported_task_types=adapter.supported_task_types,
                capabilities=adapter.capabilities(),
            )
            for adapter in self._adapters.values()
        ]
