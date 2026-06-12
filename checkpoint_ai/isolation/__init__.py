"""Scenario isolation contracts and audits.

Isolation exists to protect evidence boundaries between scenarios. It should
not become a broad security or tenancy subsystem.
"""

from checkpoint_ai.isolation.auditor import IsolationCheckResult, ScenarioIsolationAuditor
from checkpoint_ai.isolation.scope import ScenarioScope

CLEANUP_STATUS = "evidence_support"
REPLACEMENT_PATH = "scenario evidence boundary checks"

__all__ = ["IsolationCheckResult", "ScenarioIsolationAuditor", "ScenarioScope"]
