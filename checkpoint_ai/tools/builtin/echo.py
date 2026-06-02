"""Echo tool."""

from __future__ import annotations

from typing import Any

from checkpoint_ai.tools.base import BaseTool


class EchoTool(BaseTool):
    """Return input text unchanged."""

    name = "echo"
    description = "Return text unchanged."

    def run(self, **kwargs: Any) -> str:
        """Return the provided text."""

        return str(kwargs.get("text", kwargs.get("input", "")))
