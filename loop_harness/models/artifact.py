"""Artifact model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class Artifact:
    """Intermediate or final product produced by an agent."""

    task_id: str
    run_id: str
    kind: str
    content: Any
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)
