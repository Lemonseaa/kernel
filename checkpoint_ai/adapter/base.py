"""Base contracts for Agent adapters."""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel, Field

from checkpoint_ai.adapter.capabilities import AdapterCapabilities


class AgentRunRequest(BaseModel):
    """Structured request passed into an Agent adapter."""

    scenario_id: str
    task: str
    context: dict[str, Any] = Field(default_factory=dict)
    config: dict[str, Any] = Field(default_factory=dict)


class AgentRunResult(BaseModel):
    """Structured result returned by an Agent adapter."""

    scenario_id: str
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task: str
    answer: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    value_summary: str
    status: Literal["success", "failed"]
    error_type: str | None = None


class AgentAdapter(ABC):
    """Abstract interface every external or first-party Agent adapter must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stable adapter name used by scenarios."""

    @property
    @abstractmethod
    def supported_task_types(self) -> list[str]:
        """Task types this adapter can run."""

    @abstractmethod
    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Run the adapter and return a structured result."""

    @abstractmethod
    def capabilities(self) -> AdapterCapabilities:
        """Declare adapter capabilities."""

    def build_request(
        self,
        scenario_id: str,
        task: str,
        context: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
    ) -> AgentRunRequest:
        """Convenience helper used by tests and simple callers."""

        return AgentRunRequest(
            scenario_id=scenario_id,
            task=task,
            context=context or {},
            config=config or {},
        )


def latency_ms_since(start_time: float) -> int:
    """Return elapsed milliseconds from a monotonic start time."""

    return int((time.perf_counter() - start_time) * 1000)
