"""Human-facing console read models.

The console is the operator decision surface for evidence, approvals, reports,
and rollback. It should not become a code editor, workflow builder, or file
browser.
"""

from checkpoint_ai.console.approval import ApprovalInbox, ApprovalItem
from checkpoint_ai.console.backup import BackupManager, BackupRecord
from checkpoint_ai.console.cost import CostEvent, CostEventStore, DailyCostSummary
from checkpoint_ai.console.dashboard import ConsoleDashboard, ConsoleRunReport
from checkpoint_ai.console.models import (
    ConsoleRunSummary,
    ConsoleScenarioSummary,
    ConsoleSnapshot,
)
from checkpoint_ai.console.notification_routing import NotificationRouter
from checkpoint_ai.console.read_model import ConsoleReadModel

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
