"""Optional HTTP API surface for the kernel."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kernel.kernel import Kernel


@dataclass(slots=True)
class FallbackApp:
    """Small app object used when FastAPI is not installed."""

    kernel: Kernel
    routes: list[dict[str, str]] = field(default_factory=list)


def create_app(kernel: Kernel | None = None) -> Any:
    """Create a FastAPI app when available, otherwise return a fallback app."""

    active_kernel = kernel or Kernel()
    try:
        from fastapi import FastAPI
    except ImportError:
        return FallbackApp(
            kernel=active_kernel,
            routes=[
                {"method": "GET", "path": "/health"},
                {"method": "GET", "path": "/runs"},
                {"method": "GET", "path": "/metrics"},
            ],
        )

    app = FastAPI(title="Agent Workflow Kernel")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/runs")
    def list_runs() -> list[dict[str, Any]]:
        return active_kernel.store.list_runs()

    @app.get("/metrics")
    def metrics() -> dict[str, Any]:
        return active_kernel.metrics.get_summary()

    app.kernel = active_kernel
    return app
