"""Dry run context manager."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loop_harness.loop_harness import LoopHarness


class DryRunContext:
    """Temporarily enable dry run mode for a loop_harness."""

    def __init__(self, loop_harness: "LoopHarness") -> None:
        """Create a context manager for a loop_harness."""

        self.loop_harness = loop_harness
        self.previous_loop_harness_state = False
        self.previous_tool_state = False

    def __enter__(self) -> "LoopHarness":
        """Enable dry run mode."""

        self.previous_loop_harness_state = self.loop_harness.dry_run_enabled
        self.previous_tool_state = self.loop_harness.tool_registry.dry_run
        self.loop_harness.set_dry_run(True)
        return self.loop_harness

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        """Restore the previous mode."""

        self.loop_harness.set_dry_run(self.previous_loop_harness_state)
        self.loop_harness.tool_registry.dry_run = self.previous_tool_state
