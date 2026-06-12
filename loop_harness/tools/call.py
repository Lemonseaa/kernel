"""Tool call models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class ToolCall:
    """A tool call request."""

    tool_name: str
    arguments: dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
