"""Built-in LLM provider implementations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from checkpoint_ai.llm.provider import LLMProvider, LLMRequest


class MiniMaxProvider(LLMProvider):
    """MiniMax provider adapter."""

    name = "minimax"

    def __init__(
        self,
        api_key: str = "",
        model: str = "MiniMax-M2.7-highspeed",
        base_url: str = "https://api.minimax.chat/v1",
        transport: Callable[[LLMRequest], str] | None = None,
        timeout_seconds: float | None = None,
        max_retries: int = 0,
        response_cache: Any | None = None,
        performance_monitor: Any | None = None,
    ) -> None:
        """Create a MiniMax provider."""

        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url,
            transport=transport,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            response_cache=response_cache,
            performance_monitor=performance_monitor,
        )

    def _fallback_output(self, request: LLMRequest) -> str:
        """Return deterministic framework output."""

        return f"[minimax:{self.model}] {request.prompt}"


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible provider adapter."""

    name = "openai"

    def __init__(
        self,
        api_key: str = "",
        model: str = "gpt-4.1-mini",
        base_url: str = "https://api.openai.com/v1",
        transport: Callable[[LLMRequest], str] | None = None,
        timeout_seconds: float | None = None,
        max_retries: int = 0,
        response_cache: Any | None = None,
        performance_monitor: Any | None = None,
    ) -> None:
        """Create an OpenAI provider."""

        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url,
            transport=transport,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            response_cache=response_cache,
            performance_monitor=performance_monitor,
        )

    def _fallback_output(self, request: LLMRequest) -> str:
        """Return deterministic framework output."""

        return f"[openai:{self.model}] {request.prompt}"
