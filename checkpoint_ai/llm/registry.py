"""Provider registry."""

from __future__ import annotations

from checkpoint_ai.llm.provider import LLMProvider


class ProviderRegistry:
    """Register and resolve LLM providers."""

    def __init__(self) -> None:
        """Create an empty provider registry."""

        self._providers: dict[str, LLMProvider] = {}
        self._default_name: str | None = None

    def register(self, provider: LLMProvider, default: bool = False) -> None:
        """Register a provider."""

        self._providers[provider.name] = provider
        if default or self._default_name is None:
            self._default_name = provider.name

    def get(self, name: str) -> LLMProvider:
        """Get a provider by name."""

        try:
            return self._providers[name]
        except KeyError as exc:
            raise KeyError(f"Provider not registered: {name}") from exc

    def default(self) -> LLMProvider:
        """Return the default provider."""

        if self._default_name is None:
            raise RuntimeError("No default provider registered.")
        return self.get(self._default_name)

    def list_names(self) -> list[str]:
        """List provider names."""

        return list(self._providers)
