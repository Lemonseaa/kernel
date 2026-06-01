"""LLM provider abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
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
        timeout_seconds: float | None = None,
        max_retries: int = 0,
    ) -> None:
        """Create a provider."""

        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.transport = transport
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate text for a request."""

        output = self._generate_with_retries(request)
        return LLMResponse(output=output, provider=self.name, model=self.model)

    def _generate_with_retries(self, request: LLMRequest) -> str:
        """Generate text with retry and timeout handling."""

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return self._generate_text(request)
            except TimeoutError:
                raise
            except Exception as exc:
                last_error = exc
                if attempt >= self.max_retries:
                    raise
        if last_error is not None:
            raise last_error
        raise RuntimeError("Provider failed without an exception.")

    def _generate_text(self, request: LLMRequest) -> str:
        """Generate text through an injected transport or framework fallback."""

        if self.transport is not None:
            if self.timeout_seconds is None:
                return self.transport(request)
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(self.transport, request)
            try:
                return future.result(timeout=self.timeout_seconds)
            except FutureTimeoutError as exc:
                future.cancel()
                raise TimeoutError(f"Provider timed out after {self.timeout_seconds} seconds.") from exc
            finally:
                executor.shutdown(wait=False, cancel_futures=True)
        return self._fallback_output(request)

    @abstractmethod
    def _fallback_output(self, request: LLMRequest) -> str:
        """Return deterministic fallback output when no transport is configured."""
