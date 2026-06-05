"""External Agent adapter wrappers."""

from __future__ import annotations

from typing import Protocol

from checkpoint_ai.adapter import AdapterCapabilities, CapabilitySupport
from checkpoint_ai.external_agents.models import ExternalAgentConnection, ExternalRunResult


class ExternalAgentAdapter(Protocol):
    """Minimal external adapter contract used by V7."""

    @property
    def name(self) -> str:
        """Stable adapter name."""

    def run_task(self, payload: dict[str, object], connection: ExternalAgentConnection) -> ExternalRunResult:
        """Run a task against the external system."""


class DummyExternalAgentAdapter:
    """Deterministic adapter used for V7 integration drills."""

    @property
    def name(self) -> str:
        return "dummy_external"

    def capabilities(self) -> AdapterCapabilities:
        """Return fully structured demo capabilities."""

        return AdapterCapabilities(
            metrics_capture=CapabilitySupport.SUPPORTED,
            shadow_run=CapabilitySupport.SUPPORTED,
            run_trace=CapabilitySupport.SUPPORTED,
            notes={"purpose": "deterministic V7 drill adapter"},
        )

    def run_task(self, payload: dict[str, object], connection: ExternalAgentConnection) -> ExternalRunResult:
        """Return a deterministic external run result."""

        task = str(payload.get("task", "unknown"))
        quality = 0.88 if task != "unknown" else 0.5
        return ExternalRunResult(
            connection_id=connection.id,
            answer=f"Dummy external adapter handled task={task}.",
            metrics={
                "quality_score": quality,
                "latency_ms": int(connection.config.get("latency_ms", 5)),
            },
            trace=[{"step": "run_task", "task": task}],
            value_summary=f"External adapter demo completed task={task}, quality_score={quality}.",
        )
