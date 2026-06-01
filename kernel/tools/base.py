"""Base tool abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Executable tool interface."""

    name: str = "base"
    description: str = ""

    @abstractmethod
    def run(self, **kwargs: Any) -> Any:
        """Run this tool."""
