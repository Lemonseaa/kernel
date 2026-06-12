"""Core model tests."""

from __future__ import annotations

import unittest

from loop_harness.models import Agent, AgentState, Artifact, Run, RunState, Task, TaskState


class ModelTest(unittest.TestCase):
    """Validate model defaults and state transitions."""

    def test_task_state_machine_allows_expected_transitions(self) -> None:
        task = Task(name="write", agent_capability="content.write")

        task.transition_to(TaskState.RUNNING)
        task.transition_to(TaskState.WAITING_APPROVAL)
        task.transition_to(TaskState.RUNNING)
        task.transition_to(TaskState.SUCCEEDED)

        self.assertEqual(task.state, TaskState.SUCCEEDED)

    def test_task_state_machine_rejects_invalid_transition(self) -> None:
        task = Task(name="write", agent_capability="content.write")

        with self.assertRaises(ValueError):
            task.transition_to(TaskState.SUCCEEDED)

    def test_run_tracks_tasks_and_completion(self) -> None:
        run = Run(user_request="create content")
        task = Task(name="write", agent_capability="content.write")

        run.add_task(task)
        task.transition_to(TaskState.RUNNING)
        task.transition_to(TaskState.SUCCEEDED)
        run.mark_completed_if_done()

        self.assertEqual(run.state, RunState.SUCCEEDED)
        self.assertEqual(run.tasks[0].id, task.id)

    def test_agent_and_artifact_models(self) -> None:
        agent = Agent(name="writer", role="Writer", capabilities={"content.write"})
        artifact = Artifact(task_id="task-1", run_id="run-1", kind="text", content="done")

        self.assertEqual(agent.state, AgentState.IDLE)
        self.assertEqual(artifact.kind, "text")
