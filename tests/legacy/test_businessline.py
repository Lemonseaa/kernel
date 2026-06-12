"""BusinessLine framework tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from loop_harness import LoopHarness
from loop_harness.businessline import BusinessLineConfig, BusinessLineStatus, ResourceLimits
from loop_harness.models import Agent, Task
from loop_harness.persistence import SQLiteStore
from loop_harness.runtime import AgentRegistry


class BusinessLineTest(unittest.TestCase):
    """Validate BusinessLine lifecycle and resource isolation."""

    def test_loop_harness_creates_persists_and_filters_business_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
            loop_harness = LoopHarness(sqlite_path=db_path)

            content = loop_harness.create_business_line(
                "内容业务",
                config=BusinessLineConfig(
                    evaluation_rules=["readability"],
                    resource_limits=ResourceLimits(max_concurrent_runs=3, max_agents=8),
                ),
            )
            ecommerce = loop_harness.create_business_line("电商业务")
            loop_harness.business_lines.update_status(ecommerce.id, BusinessLineStatus.PAUSED)

            reloaded = LoopHarness(sqlite_path=db_path)

            self.assertEqual(reloaded.get_business_line(content.id).name, "内容业务")
            self.assertEqual(reloaded.get_business_line(content.id).config.evaluation_rules, ["readability"])
            self.assertEqual(
                reloaded.get_business_line(content.id).config.resource_limits.max_concurrent_runs,
                3,
            )
            self.assertEqual([bl.id for bl in reloaded.list_business_lines(BusinessLineStatus.ACTIVE)], [content.id])
            self.assertEqual([bl.id for bl in reloaded.list_business_lines(BusinessLineStatus.PAUSED)], [ecommerce.id])

    def test_business_line_delete_is_lifecycle_state_not_physical_purge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop_harness = LoopHarness(sqlite_path=Path(tmp) / "loop_harness.db")
            business_line = loop_harness.create_business_line("待删除业务")

            loop_harness.business_lines.delete(business_line.id)

            deleted = loop_harness.get_business_line(business_line.id)
            self.assertEqual(deleted.status, BusinessLineStatus.DELETED)
            self.assertEqual(loop_harness.list_business_lines(BusinessLineStatus.DELETED), [deleted])

    def test_run_and_task_rows_are_filtered_by_business_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop_harness = LoopHarness(sqlite_path=Path(tmp) / "loop_harness.db")
            bl_a = loop_harness.create_business_line("A业务")
            bl_b = loop_harness.create_business_line("B业务")

            run_a = loop_harness.create_run("A请求", business_line_id=bl_a.id)
            task_a = loop_harness.create_task(run_a, "A任务", "simple.execute")
            run_b = loop_harness.create_run("B请求", business_line_id=bl_b.id)
            task_b = loop_harness.create_task(run_b, "B任务", "simple.execute")

            runs_a = loop_harness.store.list_runs(business_line_id=bl_a.id)
            tasks_a = loop_harness.store.list_tasks(business_line_id=bl_a.id)

            self.assertEqual([row["id"] for row in runs_a], [run_a.id])
            self.assertEqual([row["id"] for row in tasks_a], [task_a.id])
            self.assertEqual(loop_harness.store.load_task(task_b.id)["business_line_id"], bl_b.id)

    def test_agent_registry_filters_agents_by_business_line(self) -> None:
        registry = AgentRegistry()
        agent_a = Agent(
            name="writer",
            role="Writer",
            capabilities={"content.write"},
            business_line_id="bl-a",
        )
        agent_b = Agent(
            name="writer",
            role="Writer",
            capabilities={"content.write"},
            business_line_id="bl-b",
        )

        registry.register(agent_a)
        registry.register(agent_b)

        self.assertEqual(registry.get(agent_a.id, business_line_id="bl-a"), agent_a)
        self.assertIsNone(registry.get(agent_a.id, business_line_id="bl-b"))
        self.assertEqual(registry.list(business_line_id="bl-a"), [agent_a])
        self.assertEqual(registry.find_by_capability("content.write", business_line_id="bl-b"), [agent_b])

    def test_sqlite_store_migrates_business_line_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = SQLiteStore(Path(tmp) / "loop_harness.db")
            run = LoopHarness(sqlite_path=Path(tmp) / "loop_harness.db").create_run("默认业务")
            task = Task(name="默认任务", agent_capability="simple.execute")
            run.add_task(task)
            store.save_run(run)

            self.assertEqual(store.load_run(run.id)["business_line_id"], "default")
            self.assertEqual(store.load_task(task.id)["business_line_id"], "default")


if __name__ == "__main__":
    unittest.main()
