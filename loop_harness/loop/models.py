"""Models for one-shot Agent optimization loops."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LoopStatus(str, Enum):
    """Lifecycle status for one Agent loop run."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class LoopStep(str, Enum):
    """Required V2.5 loop steps."""

    TRIGGER = "trigger"
    RUN = "run"
    RECORD = "record"
    EVALUATE = "evaluate"
    PROPOSAL = "proposal"
    POLICY = "policy"
    SHADOW = "shadow"
    COMPARE = "compare"
    APPLY_NOTIFY = "apply_notify"
    END = "end"


class LoopStepLog(BaseModel):
    """Human-readable record for one loop step."""

    step: LoopStep
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class LoopRun(BaseModel):
    """One complete, explainable Agent optimization loop."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str
    trigger_type: str
    reason: str
    trigger: dict[str, Any] = Field(default_factory=dict)
    task: str
    status: LoopStatus = LoopStatus.RUNNING
    steps: list[LoopStepLog] = Field(default_factory=list)
    adapter_run_id: str | None = None
    adapter_status: str | None = None
    adapter_value_summary: str | None = None
    proposal_id: str | None = None
    policy_level: str | None = None
    policy_action: str | None = None
    shadow_result_id: str | None = None
    baseline_comparison: dict[str, Any] = Field(default_factory=dict)
    changed_summary: str = "尚未改变。"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def add_step(
        self,
        step: LoopStep,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Append one step log and refresh update time."""

        self.steps.append(LoopStepLog(step=step, message=message, data=data or {}))
        self.updated_at = datetime.now(UTC)
