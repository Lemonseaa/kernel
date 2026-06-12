"""Human-facing console read models.

The console is the operator decision surface for evidence, approvals, reports,
and rollback. It should not become a code editor, workflow builder, or file
browser.
"""

from loop_harness.console.approval import ApprovalInbox, ApprovalItem
from loop_harness.console.backup import BackupManager, BackupRecord
from loop_harness.console.cost import CostEvent, CostEventStore, DailyCostSummary
from loop_harness.console.dashboard import ConsoleDashboard, ConsoleRunReport
from loop_harness.console.models import (
    ConsoleRunSummary,
    ConsoleScenarioSummary,
    ConsoleSnapshot,
)
from loop_harness.console.notification_routing import NotificationRouter
from loop_harness.console.read_model import ConsoleReadModel

CLEANUP_STATUS = "evidence_support"
REPLACEMENT_PATH = "human decision console"

__all__ = [
    "ApprovalInbox",
    "ApprovalItem",
    "BackupManager",
    "BackupRecord",
    "ConsoleReadModel",
    "ConsoleDashboard",
    "ConsoleRunReport",
    "ConsoleRunSummary",
    "ConsoleScenarioSummary",
    "ConsoleSnapshot",
    "CostEvent",
    "CostEventStore",
    "DailyCostSummary",
    "NotificationRouter",
]
