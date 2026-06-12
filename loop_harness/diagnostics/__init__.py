"""Diagnostics exports.

Diagnostics support operator trust and troubleshooting for the evidence
harness. They should remain focused on actionable system health.
"""

from loop_harness.diagnostics.diagnostic_report import CheckResult, DiagnosticReport
from loop_harness.diagnostics.health_checker import HealthChecker

CLEANUP_STATUS = "evidence_support"
REPLACEMENT_PATH = "operator health checks for evidence harness"

__all__ = ["CheckResult", "DiagnosticReport", "HealthChecker"]
