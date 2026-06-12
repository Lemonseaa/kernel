"""Experiment Ledger data models."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ExperimentStatus(str, Enum):
    """实验状态。"""

    PROPOSED = "proposed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Experiment(BaseModel):
    """实验记录。"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    business_line_id: str | None = None
    hypothesis: str
    baseline_id: str | None = None
    action: str
    before_metrics: dict[str, Any] = Field(default_factory=dict)
    after_metrics: dict[str, Any] = Field(default_factory=dict)
    result_summary: str = ""
    status: ExperimentStatus = ExperimentStatus.PROPOSED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)
