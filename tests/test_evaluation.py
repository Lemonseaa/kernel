"""Evaluation gate tests."""

from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from kernel import Kernel
from kernel.evaluation import EvaluationGate, EvaluationRunner, ReadabilityEvaluator
from kernel.models import Artifact, Task, TaskSpec, TaskState
from kernel.runtime import BaseAgent


class DraftAgent(BaseAgent):
    """Agent that returns a configured draft."""

    name = "draft"
    role = "Draft Agent"
    capabilities = {"content.write"}
    draft = "短"

    def execute(self, task: Task) -> Artifact:
        """Return the current draft."""

        return Artifact(task_id=task.id, run_id=task.run_id or "", kind="text", content=self.draft)


class EvaluationTest(unittest.TestCase):
    """Validate content quality evaluation."""

    def test_readability_evaluator_scores_structured_content(self) -> None:
        evaluator = ReadabilityEvaluator()
        content = "这是一个测试标题\n\n第一段内容长度适中，句子清晰，阅读起来比较顺畅。\n第二段继续补充观点，避免段落过长。"

        result = evaluator.evaluate(content, platform="public")

        self.assertEqual(result.name, "readability")
        self.assertGreaterEqual(result.score, 70.0)
        self.assertTrue(result.passed)

    def test_evaluation_gate_rejects_low_quality_content(self) -> None:
        runner = EvaluationRunner(evaluators=[ReadabilityEvaluator()])
        gate = EvaluationGate(runner)

        passed, results = gate.check("短", platform="public", min_score=70.0)

        self.assertFalse(passed)
        self.assertFalse(runner.passed_all(results, min_score=70.0))
        self.assertTrue(gate.get_suggestions(results))

    def test_workflow_marks_task_evaluation_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            DraftAgent.draft = "短"
            kernel = Kernel(sqlite_path=Path(tmp) / "kernel.db")
            kernel.agent_registry.register_agent_class(DraftAgent)

            async def run_kernel() -> object:
                return await kernel.run(
                    "质量门禁测试",
                    [
                        TaskSpec(
                            description="写一篇内容",
                            capability="content.write",
                            evaluation_required=True,
                            evaluation_platform="xiaohongshu",
                            min_score=70.0,
                        )
                    ],
                )

            run = asyncio.run(run_kernel())
            task = run.tasks[0]

            self.assertEqual(run.state.value, "failed")
            self.assertEqual(task.state, TaskState.EVALUATION_FAILED)
            self.assertTrue(task.result["evaluation_failed"])
            self.assertIn("suggestions", task.result)

    def test_evaluation_failure_feedback_is_saved_to_business_line_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            DraftAgent.draft = "短"
            kernel = Kernel(sqlite_path=Path(tmp) / "kernel.db")
            kernel.agent_registry.register_agent_class(DraftAgent)
            run = kernel.create_run("质量反馈测试", business_line_id="bl-a")
            task = kernel.create_task(run, "写一篇内容", "content.write")
            task.metadata.update(
                {
                    "evaluation_required": True,
                    "evaluation_platform": "xiaohongshu",
                    "min_score": 70.0,
                }
            )

            kernel.run(run)
            feedback_text = kernel.memory.build_business_line_prompt_context(
                "bl-a",
                kind="evaluation_feedback",
            )

            self.assertIn("evaluation_failed", feedback_text)
            self.assertIn(task.id, feedback_text)
            self.assertIn("suggestions", feedback_text)

    def test_workflow_allows_content_that_passes_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            DraftAgent.draft = (
                "AI内容质量检查实战\n\n"
                "第一部分说明为什么要在发布前检查内容质量，避免低质量草稿直接进入分发环节。"
                "这个流程可以帮助团队稳定输出，也能减少人工返工。\n\n"
                "第二部分给出具体做法：先检查标题，再检查正文结构，最后检查平台格式。"
                "每一步都有明确分数，低于阈值就要求改写。 #AI #内容"
                + "这个内容质量检查流程可以复用到选题、写作、审核和分发环节。" * 8
            )
            kernel = Kernel(sqlite_path=Path(tmp) / "kernel.db")
            kernel.agent_registry.register_agent_class(DraftAgent)

            async def run_kernel() -> object:
                return await kernel.run(
                    "质量门禁通过测试",
                    [
                        TaskSpec(
                            description="写一篇内容",
                            capability="content.write",
                            evaluation_required=True,
                            evaluation_platform="xiaohongshu",
                            min_score=55.0,
                        )
                    ],
                )

            run = asyncio.run(run_kernel())

            self.assertEqual(run.state.value, "succeeded")
            self.assertEqual(run.tasks[0].state, TaskState.SUCCEEDED)
            self.assertIn("evaluation", run.tasks[0].metadata)
