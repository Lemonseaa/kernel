"""V4.3 adapter compatibility contract tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.adapter import (
    AdapterCompatibilityDecision,
    AdapterCompatibilityEvaluator,
    AdapterCompatibilityInput,
    AdapterCompatibilityReportStore,
)


class V43AdapterCompatibilityTest(unittest.TestCase):
    """Validate adapter compatibility evaluation before integration code."""

    def test_compatibility_evaluator_returns_needs_spike_for_costly_partial_adapter(self) -> None:
        report = AdapterCompatibilityEvaluator().evaluate(
            AdapterCompatibilityInput(
                name="TradingAgents",
                structured_input=True,
                structured_output=True,
                prompt_slots=False,
                prompt_injection=False,
                shadow_run=False,
                run_trace=True,
                metrics_capture=True,
                metric_format_compatible=False,
                estimated_days=8,
                dependencies=["tradingagents"],
            )
        )

        self.assertEqual(report.decision, AdapterCompatibilityDecision.NEEDS_SPIKE)
        self.assertIn("estimated_days", report.warnings)
        self.assertIn("Adapter Compatibility Report", report.markdown)

    def test_compatibility_evaluator_blocks_unstructured_output(self) -> None:
        report = AdapterCompatibilityEvaluator().evaluate(
            AdapterCompatibilityInput(
                name="LooseAgent",
                structured_input=True,
                structured_output=False,
                prompt_slots=True,
                prompt_injection=True,
                shadow_run=True,
                run_trace=True,
                metrics_capture=True,
                metric_format_compatible=True,
                estimated_days=2,
            )
        )

        self.assertEqual(report.decision, AdapterCompatibilityDecision.NO_GO)
        self.assertIn("structured_output", report.blockers)

    def test_compatibility_report_store_persists_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = AdapterCompatibilityReportStore(Path(tmp) / "compat.db")
            report = AdapterCompatibilityEvaluator().evaluate(
                AdapterCompatibilityInput(
                    name="CrewAI",
                    structured_input=True,
                    structured_output=True,
                    prompt_slots=True,
                    prompt_injection=True,
                    shadow_run=True,
                    run_trace=True,
                    metrics_capture=True,
                    metric_format_compatible=True,
                    estimated_days=3,
                )
            )

            store.save(report)
            loaded = store.get(report.id)

            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.name, "CrewAI")
            self.assertEqual(loaded.decision, AdapterCompatibilityDecision.GO)

    def test_compatibility_cli_outputs_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "compat.db"

            result = _run_cli(
                db_path,
                "adapter",
                "compatibility",
                "--name",
                "TradingAgents",
                "--structured-input",
                "true",
                "--structured-output",
                "true",
                "--prompt-slots",
                "false",
                "--prompt-injection",
                "false",
                "--shadow-run",
                "false",
                "--run-trace",
                "true",
                "--metrics-capture",
                "true",
                "--metric-format-compatible",
                "false",
                "--estimated-days",
                "8",
            )

            self.assertIn("Adapter Compatibility Report", result.stdout)
            self.assertIn("decision: needs_spike", result.stdout)


def _run_cli(db_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["./checkpointai", "--db", str(db_path), *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result


if __name__ == "__main__":
    unittest.main()
