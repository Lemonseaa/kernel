"""Built-in LLM provider implementations."""

from __future__ import annotations

from kernel.llm.provider import LLMProvider, LLMRequest


class MiniMaxProvider(LLMProvider):
    """MiniMax provider adapter."""

    name = "minimax"

    def __init__(self, api_key: str = "", model: str = "MiniMax-M2.7-highspeed", **kwargs: object) -> None:
        """Create a MiniMax provider."""

        super().__init__(
            api_key=api_key,
            model=model,
            base_url=str(kwargs.pop("base_url", "https://api.minimax.chat/v1")),
            **kwargs,
        )

    def _fallback_output(self, request: LLMRequest) -> str:
        """Return deterministic framework output."""

        return f"[minimax:{self.model}] {request.prompt}"


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible provider adapter."""

    name = "openai"

    def __init__(self, api_key: str = "", model: str = "gpt-4.1-mini", **kwargs: object) -> None:
        """Create an OpenAI provider."""

        super().__init__(
            api_key=api_key,
            model=model,
            base_url=str(kwargs.pop("base_url", "https://api.openai.com/v1")),
            **kwargs,
        )

    def _fallback_output(self, request: LLMRequest) -> str:
        """Return deterministic framework output."""

        return f"[openai:{self.model}] {request.prompt}"
