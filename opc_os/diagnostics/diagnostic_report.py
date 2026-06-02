"""Standard diagnostic report models."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CheckResult:
    """One component health check result."""

    component: str
    status: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DiagnosticReport:
    """Aggregated health report for the kernel."""

    overall_status: str
    checks: list[CheckResult]
    recommendations: list[str]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible report."""

        return {
            "timestamp": self.timestamp,
            "overall_status": self.overall_status,
            "checks": [
                {
                    "component": check.component,
                    "status": check.status,
                    "message": check.message,
                    "details": check.details,
                }
                for check in self.checks
            ],
            "recommendations": list(self.recommendations),
        }
