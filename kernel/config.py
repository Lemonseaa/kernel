"""Kernel configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kernel.dryrun import DryRunProvider
from kernel.llm import LLMProvider, MiniMaxProvider, OpenAIProvider


@dataclass(slots=True)
class KernelConfig:
    """Configuration for kernel services."""

    providers: dict[str, dict[str, Any]] = field(default_factory=dict)
    default_provider: str = "minimax"
    dry_run: bool = False
    max_concurrency: int = 1
    llm_cache_enabled: bool = True
    llm_cache_max_size: int = 128
    llm_cache_ttl_seconds: float = 300.0
    slow_task_threshold_seconds: float = 5.0

    @property
    def llm_provider(self) -> LLMProvider:
        """Build the configured default LLM provider."""

        if self.dry_run:
            return DryRunProvider(model="dryrun")
        config = dict(self.providers.get(self.default_provider, {}))
        if self.default_provider == "minimax":
            return MiniMaxProvider(**config)
        if self.default_provider == "openai":
            return OpenAIProvider(**config)
        raise ValueError(f"Unsupported provider: {self.default_provider}")
