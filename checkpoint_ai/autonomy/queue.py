"""Queue processor for low-risk autonomous actions."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from checkpoint_ai.autonomy.models import AutonomyActionLog, AutonomyActionStatus
from checkpoint_ai.autonomy.store import AutonomyActionStore, AutonomyQueueStateStore
from checkpoint_ai.decision import DecisionKind, DecisionLogStore, DecisionRecord


class AutoActionQueue:
    """Process pending autonomy actions with audit records."""

    def __init__(
        self,
        actions: AutonomyActionStore,
        decisions: DecisionLogStore,
        state: AutonomyQueueStateStore | None = None,
    ) -> None:
        self.actions = actions
        self.decisions = decisions
        self.state = state
        self._paused = False

    def pause(self) -> None:
        """Pause queue processing."""

        if self.state is not None:
            self.state.pause()
            return
        self._paused = True

    def resume(self) -> None:
        """Resume queue processing."""

        if self.state is not None:
            self.state.resume()
            return
        self._paused = False

    def is_paused(self) -> bool:
        """Return whether queue processing is paused."""

        if self.state is not None:
            return self.state.is_paused()
        return self._paused

    def process_next(
        self,
        handler: Callable[[AutonomyActionLog], dict[str, Any]],
    ) -> AutonomyActionLog | None:
        """Process the oldest pending action through a caller-provided handler."""

        if self.is_paused():
            return None
        action = self._next_pending()
        if action is None:
            return None
        return self.process(action.id, handler)

    def process(
        self,
        action_id: str,
        handler: Callable[[AutonomyActionLog], dict[str, Any]],
    ) -> AutonomyActionLog | None:
        """Process one pending action by id through a caller-provided handler."""

        if self.is_paused():
            return None
        action = self.actions.get(action_id)
        if action is None or action.status != AutonomyActionStatus.PENDING:
            return action
        self.actions.update_status(action.id, AutonomyActionStatus.RUNNING)
        running = self.actions.get(action.id)
        if running is None:
            return None
        try:
            result = handler(running)
        except Exception as exc:
            failure = {"error": str(exc), "error_type": type(exc).__name__}
            self.actions.update_status(running.id, AutonomyActionStatus.FAILED, result=failure)
            failed = self.actions.get(running.id)
            self._record(
                action=failed or running,
                kind=DecisionKind.ERROR,
                audit_action="auto_action_failed",
                comment=f"Auto action failed: {exc}",
                result=failure,
            )
            return failed or running
        self.actions.update_status(running.id, AutonomyActionStatus.SUCCEEDED, result=result)
        succeeded = self.actions.get(running.id)
        self._record(
            action=succeeded or running,
            kind=DecisionKind.SYSTEM,
            audit_action="auto_action_succeeded",
            comment="Auto action succeeded.",
            result=result,
        )
        return succeeded or running

    def _next_pending(self) -> AutonomyActionLog | None:
        pending = self.actions.list(status=AutonomyActionStatus.PENDING)
        return pending[0] if pending else None

    def _record(
        self,
        action: AutonomyActionLog,
        kind: DecisionKind,
        audit_action: str,
        comment: str,
        result: dict[str, Any],
    ) -> None:
        self.decisions.record(
            DecisionRecord(
                source_id=action.id,
                source_type="autonomy_action",
                kind=kind,
                scenario_id=action.scenario_id,
                action=audit_action,
                comment=comment,
                result=result,
                details={
                    "proposal_id": action.proposal_id,
                    "checkpoint_id": action.checkpoint_id,
                    "action_type": action.action_type,
                },
            )
        )
