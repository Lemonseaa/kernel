"""V2.1 Scenario + Adapter + Logs contract tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from loop_harness.adapter import AdapterRegistry, DummyAdapter
from loop_harness.logs import RawLogStore, SummaryLogStore
from loop_harness.scenario import Scenario, ScenarioRegistry, ScenarioRunner


class V21ScenarioAdapterLogsTest(unittest.TestCase):
    """Validate the V2.1 minimal closed loop."""

    def test_scenario_crud(self) -> None:
        registry = ScenarioRegistry()
        scenario = registry.create(
            Scenario(
                name="Quant demo",
                description="Dummy stock signal scenario.",
                adapter_type="dummy_stock_signal",
            )
        )

        self.assertEqual(registry.get(scenario.id), scenario)
        self.assertEqual(registry.list(), [scenario])
        with self.assertRaisesRegex(KeyError, f"Scenario not found: {scenario.id}-missing"):
            registry.get(f"{scenario.id}-missing")

    def test_adapter_registry_register_resolve(self) -> None:
        registry = AdapterRegistry()
        adapter = DummyAdapter()

        registry.register(adapter)

        self.assertEqual(registry.resolve("dummy_stock_signal"), adapter)
        self.assertEqual(registry.list_adapters(), ["dummy_stock_signal"])
        with self.assertRaisesRegex(KeyError, "Adapter not found: missing"):
            registry.resolve("missing")

    def test_dummy_adapter_success(self) -> None:
        adapter = DummyAdapter()
        request = adapter.build_request(
            scenario_id="scenario-1",
            task="analyze_signal",
            context={"symbol": "AAPL"},
        )

        result = adapter.run(request)

        self.assertEqual(result.status, "success")
        self.assertEqual(result.scenario_id, "scenario-1")
        self.assertEqual(result.task, "analyze_signal")
        self.assertIn("AAPL", result.answer)
        self.assertIn("signal_quality", result.metrics)
        self.assertIn("confidence", result.metrics)
        self.assertIn("latency_ms", result.metrics)
        self.assertIn("本次运行分析了AAPL", result.value_summary)

    def test_dummy_adapter_failure(self) -> None:
        adapter = DummyAdapter()
        request = adapter.build_request(
            scenario_id="scenario-1",
            task="analyze_signal",
            context={"symbol": "AAPL"},
            config={"force_failure": True},
        )

        result = adapter.run(request)

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.error_type, "adapter_error")
        self.assertIn("failed", result.value_summary.lower())

    def test_raw_log_save_and_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw_store = RawLogStore(Path(tmp) / "v21.db")
            adapter = DummyAdapter()
            request = adapter.build_request("scenario-1", "analyze_signal", {"symbol": "AAPL"})
            result = adapter.run(request)

            raw_store.save(result.run_id, request, result)

            loaded = raw_store.get(result.run_id)
            queried = raw_store.query_by_scenario("scenario-1")

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["request"]["context"]["symbol"], "AAPL")
        self.assertEqual(loaded["result"]["metrics"]["signal_quality"], result.metrics["signal_quality"])
        self.assertEqual(len(queried), 1)

    def test_summary_log_save_and_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary_store = SummaryLogStore(Path(tmp) / "v21.db")
            adapter = DummyAdapter()
            request = adapter.build_request("scenario-1", "analyze_signal", {"symbol": "AAPL"})
            result = adapter.run(request)

            summary_store.save(result)

            loaded = summary_store.get(result.run_id)
            queried = summary_store.query_by_scenario("scenario-1")

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["metrics"]["confidence"], result.metrics["confidence"])
        self.assertEqual(loaded["value_summary"], result.value_summary)
        self.assertEqual(len(queried), 1)

    def test_run_scenario_flow_and_failure_logging(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runner = self._build_runner(Path(tmp) / "v21.db")
            scenario = runner.scenarios.create(
                Scenario(
                    name="Quant demo",
                    description="Dummy stock signal scenario.",
                    adapter_type="dummy_stock_signal",
                )
            )

            success = runner.run_scenario(
                scenario.id,
                task="analyze_signal",
                context={"symbol": "AAPL"},
            )
            failed = runner.run_scenario(
                scenario.id,
                task="analyze_signal",
                context={"symbol": "AAPL"},
                config={"force_failure": True},
            )
            raw_logs = runner.raw_logs.query_by_scenario(scenario.id)
            summary_logs = runner.summary_logs.query_by_scenario(scenario.id)

        self.assertEqual(success.status, "success")
        self.assertEqual(failed.status, "failed")
        self.assertEqual(failed.error_type, "adapter_error")
        self.assertEqual(len(raw_logs), 2)
        self.assertEqual(len(summary_logs), 2)
        self.assertIn("AAPL", success.value_summary)
        self.assertIn("signal_quality", success.value_summary)
        self.assertIn("confidence", success.value_summary)
        self.assertIn("failed_summary", summary_logs[1])
        self.assertIn("AAPL", summary_logs[0]["value_summary"])

    def test_run_scenario_missing_scenario_raises_clear_error(self) -> None:
        runner = self._build_runner()

        with self.assertRaisesRegex(KeyError, "Scenario not found: missing-scenario"):
            runner.run_scenario("missing-scenario", "analyze_signal", {"symbol": "AAPL"})

    def test_run_scenario_missing_adapter_raises_clear_error_without_logs(self) -> None:
        runner = self._build_runner()
        scenario = runner.scenarios.create(
            Scenario(
                name="Missing adapter demo",
                description="Scenario points to a missing adapter.",
                adapter_type="missing_adapter",
            )
        )

        with self.assertRaisesRegex(KeyError, "Adapter not found: missing_adapter"):
            runner.run_scenario(scenario.id, "analyze_signal", {"symbol": "AAPL"})

        self.assertEqual(runner.raw_logs.query_by_scenario(scenario.id), [])
        self.assertEqual(runner.summary_logs.query_by_scenario(scenario.id), [])

    @staticmethod
    def _build_runner(db_path: Path | None = None) -> ScenarioRunner:
        adapters = AdapterRegistry()
        adapters.register(DummyAdapter())
        return ScenarioRunner(
            scenarios=ScenarioRegistry(),
            adapters=adapters,
            raw_logs=RawLogStore(db_path),
            summary_logs=SummaryLogStore(db_path),
        )


if __name__ == "__main__":
    unittest.main()
