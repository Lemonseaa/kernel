"""Run a deterministic V7 learning-loop drill."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from checkpoint_ai.adapter import AgentRunResult
from checkpoint_ai.learning import LearningLoopService
from checkpoint_ai.logs import SummaryLogStore


def main() -> None:
    """Seed semi-real run data and execute one V7 learning-loop tick."""

    with TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "checkpointai.db"
        summaries = SummaryLogStore(db_path)
        for index, sharpe in enumerate([0.24, 0.31, 0.19, 0.27, 0.22], start=1):
            summaries.save(
                AgentRunResult(
                    scenario_id="quant-demo",
                    run_id=f"historical-run-{index}",
                    task="quant_backtest",
                    answer="historical backtest completed",
                    metrics={
                        "sharpe": sharpe,
                        "max_drawdown": 0.12,
                        "sample_count": 250,
                        "latency_ms": 12,
                    },
                    value_summary=f"Historical backtest sample {index}; sharpe={sharpe}.",
                    status="success",
                )
            )

        result = LearningLoopService(
            db_path=db_path,
            metric_thresholds={"sharpe": 0.5},
        ).run_once(
            scenario_id="quant-demo",
            business_line_id="quant",
            trigger_reason="v7 deterministic historical-data drill",
        )
        print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
