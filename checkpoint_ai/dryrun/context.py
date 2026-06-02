"""Dry run context manager."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from checkpoint_ai.checkpoint_ai import CheckpointAI


class DryRunContext:
    """Temporarily enable dry run mode for a checkpoint_ai."""

    def __init__(self, checkpoint_ai: "CheckpointAI") -> None:
        """Create a context manager for a checkpoint_ai."""

        self.checkpoint_ai = checkpoint_ai
        self.previous_checkpoint_ai_state = False
        self.previous_tool_state = False

    def __enter__(self) -> "CheckpointAI":
        """Enable dry run mode."""

        self.previous_checkpoint_ai_state = self.checkpoint_ai.dry_run_enabled
        self.previous_tool_state = self.checkpoint_ai.tool_registry.dry_run
        self.checkpoint_ai.set_dry_run(True)
        return self.checkpoint_ai

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        """Restore the previous mode."""

        self.checkpoint_ai.set_dry_run(self.previous_checkpoint_ai_state)
        self.checkpoint_ai.tool_registry.dry_run = self.previous_tool_state
