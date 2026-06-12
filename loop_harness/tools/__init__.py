"""Isolated tool layer exports.

LoopHarness does not build a general-purpose tool marketplace. Keep this
package limited to compatibility tools used by tests and local evidence drills.
Prefer guarded MCP/external connectors for real integrations.
"""

from loop_harness.tools.base import BaseTool
from loop_harness.tools.builtin import EchoTool, FileWriteTool
from loop_harness.tools.call import ToolCall
from loop_harness.tools.permission import ToolPermission
from loop_harness.tools.registry import ToolRegistry

CLEANUP_STATUS = "isolate"
REPLACEMENT_PATH = "guarded MCP / external workflow-specific tool connectors"

__all__ = [
    "BaseTool",
    "EchoTool",
    "FileWriteTool",
    "ToolCall",
    "ToolPermission",
    "ToolRegistry",
]
