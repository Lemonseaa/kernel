"""Tool registry."""

from __future__ import annotations

import inspect
from typing import Any, Callable

from checkpoint_ai.tools.base import BaseTool
from checkpoint_ai.tools.permission import ToolPermission


class ToolRegistry:
    """Register and call external tools through permission checks."""

    def __init__(self, permission: ToolPermission | None = None, dry_run: bool = False) -> None:
        """Create a tool registry."""

        self.permission = permission or ToolPermission()
        self.dry_run = dry_run
        self._tools: dict[str, Callable[..., Any] | BaseTool] = {}

    def register(
        self,
        tool_or_name: str | BaseTool,
        func: Callable[..., Any] | None = None,
    ) -> None:
        """Register a callable tool."""

        if isinstance(tool_or_name, BaseTool):
            self._tools[tool_or_name.name] = tool_or_name
            self.permission.allowed_tools.add(tool_or_name.name)
            return
        if func is None:
            raise ValueError("Callable tool registration requires func.")
        self._tools[tool_or_name] = func

    def call(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a registered tool if permission allows it."""

        if name not in self._tools:
            raise PermissionError(f"Tool is not registered: {name}")
        if not self.permission.check(name):
            raise PermissionError(f"Tool is not allowed: {name}")
        if self.dry_run:
            from checkpoint_ai.dryrun import DryRunTool

            return DryRunTool(name).run(**arguments)
        tool = self._tools[name]
        if isinstance(tool, BaseTool):
            return tool.run(**arguments)
        return tool(**arguments)

    async def acall(self, name: str, arguments: dict[str, Any]) -> Any:
        """Async wrapper for tool calls."""

        result = self.call(name, arguments)
        if inspect.isawaitable(result):
            return await result
        return result
