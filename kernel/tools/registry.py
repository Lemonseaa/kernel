"""Tool registry."""

from __future__ import annotations

from typing import Any, Callable

from kernel.tools.permission import ToolPermission


class ToolRegistry:
    """Register and call external tools through permission checks."""

    def __init__(self, permission: ToolPermission | None = None) -> None:
        """Create a tool registry."""

        self.permission = permission or ToolPermission()
        self._tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, func: Callable[..., Any]) -> None:
        """Register a callable tool."""

        self._tools[name] = func

    def call(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a registered tool if permission allows it."""

        if name not in self._tools:
            raise PermissionError(f"Tool is not registered: {name}")
        if not self.permission.check(name):
            raise PermissionError(f"Tool is not allowed: {name}")
        return self._tools[name](**arguments)
