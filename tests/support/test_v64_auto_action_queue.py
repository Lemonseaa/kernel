"""V6.4 Auto Action Queue tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from loop_harness.autonomy import (
    AutoActionQueue,
    AutonomyActionStatus,
    AutonomyActionStore,
)
from loop_harness.decision import DecisionKind, DecisionLogStore


class V64AutoActionQueueTest(unittest.TestCase):
    """Validate low-risk autonomous action queue processing."""

    def test_queue_processes_next_pending_action_and_records_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "queue.db"
            store = AutonomyActionStore(db_path)
            decisions = DecisionLogStore(db_path)
            action = store.create(
                scenario_id="demo-quant",
                proposal_id="proposal-1",
                action_type="prompt_patch",
                checkpoint_id="checkpoint-1",
                reason="Low-risk historical shadow passed.",
            )
            queue = AutoActionQueue(actions=store, decisions=decisions)

            processed = queue.process_next(lambda item: {"applied": item.proposal_id})
            loaded = store.get(action.id)
            records = decisions.list(source_id=action.id)

        self.assertIsNotNone(processed)
        assert processed is not None
        self.assertEqual(processed.id, action.id)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.status, AutonomyActionStatus.SUCCEEDED)
        self.assertEqual(loaded.result["applied"], "proposal-1")
        self.assertEqual([record.kind for record in records], [DecisionKind.SYSTEM])
        self.assertEqual(records[0].action, "auto_action_succeeded")

    def test_queue_records_failure_without_processing_other_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "queue.db"
            store = AutonomyActionStore(db_path)
            decisions = DecisionLogStore(db_path)
            first = store.create(
                scenario_id="demo-quant",
                proposal_id="proposal-1",
                action_type="prompt_patch",
                checkpoint_id="checkpoint-1",
                reason="First action should fail.",
            )
            second = store.create(
                scenario_id="demo-quant",
                proposal_id="proposal-2",
                action_type="prompt_patch",
                checkpoint_id="checkpoint-2",
                reason="Second action should remain pending.",
            )
            queue = AutoActionQueue(actions=store, decisions=decisions)

            processed = queue.process_next(lambda _item: (_ for _ in ()).throw(RuntimeError("apply failed")))
            failed = store.get(first.id)
            untouched = store.get(second.id)
            records = decisions.list(source_id=first.id)

        self.assertIsNotNone(processed)
        self.assertIsNotNone(failed)
        self.assertIsNotNone(untouched)
        assert failed is not None
        assert untouched is not None
        self.assertEqual(failed.status, AutonomyActionStatus.FAILED)
        self.assertEqual(failed.result["error"], "apply failed")
        self.assertEqual(untouched.status, AutonomyActionStatus.PENDING)
        self.assertEqual([record.kind for record in records], [DecisionKind.ERROR])

    def test_queue_pause_prevents_processing_until_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "queue.db"
            store = AutonomyActionStore(db_path)
            decisions = DecisionLogStore(db_path)
            action = store.create(
                scenario_id="demo-quant",
                proposal_id="proposal-1",
                action_type="prompt_patch",
                checkpoint_id="checkpoint-1",
                reason="Low-risk historical shadow passed.",
            )
            queue = AutoActionQueue(actions=store, decisions=decisions)

            queue.pause()
            paused = queue.process_next(lambda item: {"applied": item.proposal_id})
            still_pending = store.get(action.id)
            queue.resume()
            processed = queue.process_next(lambda item: {"applied": item.proposal_id})

        self.assertTrue(queue.is_paused() is False)
        self.assertIsNone(paused)
        self.assertIsNotNone(still_pending)
        assert still_pending is not None
        self.assertEqual(still_pending.status, AutonomyActionStatus.PENDING)
        self.assertIsNotNone(processed)


if __name__ == "__main__":
    unittest.main()
