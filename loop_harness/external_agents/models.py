"""External Agent connection contracts."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from loop_harness.adapter import AdapterCapabilities


class ExternalAgentConnection(BaseModel):
    """One external Agent system attached to a business line."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    business_line_id: str
    scenario_id: str
    name: str
    adapter_type: str
    config: dict[str, Any] = Field(default_factory=dict)
    capabilities: AdapterCapabilities = Field(default_factory=AdapterCapabilities)
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExternalRunResult(BaseModel):
    """Structured result returned by an external adapter wrapper."""

    connection_id: str
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    answer: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    trace: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "success"
    value_summary: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
