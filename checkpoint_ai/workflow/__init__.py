"""Frozen legacy workflow engine exports.

CheckpointAI no longer competes with workflow engines such as Temporal,
Prefect, LangGraph, or Archon-style harnesses. These exports stay available
for regression compatibility while the mainline moves to external workflow
evidence ingestion and comparison.
"""

from checkpoint_ai.workflow.engine import WorkflowEngine
from checkpoint_ai.workflow.executor import TaskExecutor
from checkpoint_ai.workflow.task_queue import TaskQueue

LEGACY_STATUS = "frozen"
REPLACEMENT_PATH = "Temporal / Prefect / LangGraph / external harness projects"

__all__ = ["TaskExecutor", "TaskQueue", "WorkflowEngine"]
