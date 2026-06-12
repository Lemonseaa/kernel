"""Frozen legacy workflow engine exports.

LoopHarness no longer competes with workflow engines such as Temporal,
Prefect, LangGraph, or Archon-style harnesses. These exports stay available
for regression compatibility while the mainline moves to external workflow
evidence ingestion and comparison.
"""

from loop_harness.workflow.engine import WorkflowEngine
from loop_harness.workflow.executor import TaskExecutor
from loop_harness.workflow.task_queue import TaskQueue

LEGACY_STATUS = "frozen"
REPLACEMENT_PATH = "Temporal / Prefect / LangGraph / external harness projects"

__all__ = ["TaskExecutor", "TaskQueue", "WorkflowEngine"]
