"""LLM provider abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class LLMRequest:
    """Request passed to an LLM provider."""

    prompt: str
    system: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LLMResponse:
    """Response returned by an LLM provider."""

    output: str
    provider: str
    model: str
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract base class for model providers."""

    name: str = "base"

    def __init__(
        self,
        api_key: str = "",
        model: str = "",
        base_url: str = "",
        transport: Callable[[LLMRequest], str] | None = None,
    ) -> None:
        """Create a provider."""

        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.transport = transport

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate text for a request."""

        output = self._generate_text(request)
        return LLMResponse(output=output, provider=self.name, model=self.model)

    def _generate_text(self, request: LLMRequest) -> str:
        """Generate text through an injected transport or framework fallback."""

        if self.transport is not None:
            return self.transport(request)
        return self._fallback_output(request)

    @abstractmethod
    def _fallback_output(self, request: LLMRequest) -> str:
        """Return deterministic fallback output when no transport is configured."""
