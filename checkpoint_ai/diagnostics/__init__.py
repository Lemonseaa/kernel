"""Diagnostics exports.

Diagnostics support operator trust and troubleshooting for the evidence
harness. They should remain focused on actionable system health.
"""

from checkpoint_ai.diagnostics.diagnostic_report import CheckResult, DiagnosticReport
from checkpoint_ai.diagnostics.health_checker import HealthChecker

CLEANUP_STATUS = "evidence_support"
REPLACEMENT_PATH = "operator health checks for evidence harness"

__all__ = ["CheckResult", "DiagnosticReport", "HealthChecker"]
