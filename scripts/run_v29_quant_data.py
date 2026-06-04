"""Run V2.9 quant demo data collection and write a report."""

# ruff: noqa: E402

from __future__ import annotations

import argparse
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from checkpoint_ai.adapter import AdapterRegistry, QuantResearchDemoAdapter
from checkpoint_ai.evaluation import EvidenceEvaluation, EvidenceEvaluationEngine
from checkpoint_ai.logs import RawLogStore, SummaryLogStore
from checkpoint_ai.loop import AgentLoopEngine, AgentLoopStore, LoopRun
from checkpoint_ai.metrics import ComparisonResult, MetricSchemaRegistry, MetricSchemaStore
from checkpoint_ai.policy import ScenarioPolicy, ScenarioPolicyService
from checkpoint_ai.prompt import (
    PromptPatch,
    PromptProposal,
    PromptProposalStore,
    PromptSlot,
    PromptVersionStore,
)
from checkpoint_ai.recommendation import (
    VersionRecommendation,
    VersionRecommendationStore,
    VersionRecommender,
)
from checkpoint_ai.scenario import Scenario, ScenarioRegistry, ScenarioRunner, ScenarioStore
from checkpoint_ai.shadow import ShadowResult, ShadowResultStore, ShadowRunner


@dataclass(frozen=True)
class RunSpec:
    """One deterministic quant demo run."""

    symbol: str
    strategy_type: str
    baseline_config: dict[str, float | int | str]
    proposal_config: dict[str, float | int | str]
    before: str
    after: str
    reason: str


def main() -> int:
    """Run data collection from the command line."""

    parser = argparse.ArgumentParser(description="Run V2.9 quant demo data collection")
    parser.add_argument("--db", default=".runtime/v29_quant_demo.db")
    parser.add_argument("--report", default="docs/V2.9_DATA_RUN_REPORT.md")
    parser.add_argument("--runs", type=int, default=30)
    args = parser.parse_args()

    db_path = Path(args.db)
    report_path = Path(args.report)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    specs = _run_specs(args.runs)
    scenario_registry = ScenarioRegistry()
    scenario_store = ScenarioStore(db_path)
    raw_logs = RawLogStore(db_path)
    summary_logs = SummaryLogStore(db_path)
    versions = PromptVersionStore(db_path)
    proposals = PromptProposalStore(db_path)
    shadow_results = ShadowResultStore(db_path)
    loop_store = AgentLoopStore(db_path)
    metric_schemas = MetricSchemaStore(db_path)
    recommendations = VersionRecommendationStore(db_path)
    adapters = AdapterRegistry()
    adapters.register(QuantResearchDemoAdapter())

    scenario = Scenario(
        id="quant-demo",
        name="V2.9 Quant Demo",
        description="Pre-V3 deterministic quant data run.",
        adapter_type="quant_research_demo",
    )
    scenario_store.save(scenario)
    scenario_registry.create(scenario)
    metric_schemas.save_for_scenario(scenario.id, MetricSchemaRegistry.default_quant().list())
    versions.save_version(
        scenario_id=scenario.id,
        agent_id="strategy",
        slots={PromptSlot.CONSTRAINTS: "quant-demo baseline strategy parameters"},
        reason="V2.9 data run baseline",
    )

    runner = ScenarioRunner(
        scenarios=scenario_registry,
        adapters=adapters,
        raw_logs=raw_logs,
        summary_logs=summary_logs,
    )

    queue = list(specs)

    def proposal_factory(scenario_id: str, run_metrics: dict[str, float]) -> PromptProposal:
        spec = queue.pop(0)
        metadata: dict[str, Any] = {
            **spec.proposal_config,
            "baseline_metrics": run_metrics,
            "run_kind": "synthetic",
            "provenance": {
                "data_source": "synthetic_prices",
                "generated_by": "quant_research_demo",
                "seed": spec.symbol,
                "sample_count": 260,
            },
        }
        return PromptProposal(
            scenario_id=scenario_id,
            agent_id="strategy",
            patch=PromptPatch(
                slot=PromptSlot.CONSTRAINTS,
                operation="replace",
                before=spec.before,
                after=spec.after,
            ),
            reason=spec.reason,
            expected_metric="sharpe",
            metadata=metadata,
        )

    engine = AgentLoopEngine(
        scenario_runner=runner,
        proposals=proposals,
        policy_service=ScenarioPolicyService(
            policy=ScenarioPolicy(),
            proposals=proposals,
            versions=versions,
            shadow_runner=ShadowRunner(
                scenarios=scenario_registry,
                adapters=adapters,
                versions=versions,
                results=shadow_results,
                task="backtest_strategy",
                metric_schema_store=metric_schemas,
            ),
        ),
        shadow_results=shadow_results,
        loop_store=loop_store,
        proposal_factory=proposal_factory,
    )

    loop_runs: list[LoopRun] = []
    for index, spec in enumerate(specs, start=1):
        loop_runs.append(
            engine.trigger_manual(
                scenario_id=scenario.id,
                task="backtest_strategy",
                reason=f"V2.9 data run {index}: {spec.symbol}/{spec.strategy_type}",
                context={"symbol": spec.symbol, "strategy_type": spec.strategy_type},
                config={
                    **spec.baseline_config,
                    "run_kind": "synthetic",
                    "provenance": {
                        "data_source": "synthetic_prices",
                        "generated_by": "quant_research_demo",
                        "seed": spec.symbol,
                        "sample_count": 260,
                    },
                },
            )
        )

    shadow_items = shadow_results.query_by_scenario(scenario.id)
    recommendation = VersionRecommender(
        shadow_results=shadow_results,
        recommendations=recommendations,
    ).recommend_for_scenario(scenario.id)
    report_path.write_text(
        _render_report(
            loop_runs=loop_runs,
            shadow_items=shadow_items,
            recommendation=recommendation,
            raw_count=len(raw_logs.query_by_scenario(scenario.id)),
            summary_count=len(summary_logs.query_by_scenario(scenario.id)),
            proposal_count=len(proposals.list(scenario_id=scenario.id)),
            shadow_count=len(shadow_results.query_by_scenario(scenario.id)),
            db_path=db_path,
        ),
        encoding="utf-8",
    )
    print(f"V2.9 quant data run complete: {len(loop_runs)} runs")
    print(f"database: {db_path}")
    print(f"report: {report_path}")
    return 0


def _run_specs(limit: int) -> list[RunSpec]:
    symbols = ["SPY", "AAPL", "TSLA"]
    specs: list[RunSpec] = []
    for symbol in symbols:
        specs.extend(
            [
                RunSpec(
                    symbol=symbol,
                    strategy_type="moving_average",
                    baseline_config={"fast_window": 8, "slow_window": 24},
                    proposal_config={"fast_window": 10, "slow_window": 30},
                    before="fast_window=8, slow_window=24",
                    after="fast_window=10, slow_window=30",
                    reason="尝试放慢均线参数，减少短期噪声对策略的影响。",
                ),
                RunSpec(
                    symbol=symbol,
                    strategy_type="moving_average",
                    baseline_config={"fast_window": 10, "slow_window": 30},
                    proposal_config={"fast_window": 6, "slow_window": 18},
                    before="fast_window=10, slow_window=30",
                    after="fast_window=6, slow_window=18",
                    reason="尝试提高均线灵敏度，观察收益提升是否伴随回撤恶化。",
                ),
                RunSpec(
                    symbol=symbol,
                    strategy_type="rsi",
                    baseline_config={"rsi_period": 14, "rsi_buy": 35},
                    proposal_config={"rsi_period": 10, "rsi_buy": 32},
                    before="rsi_period=14, rsi_buy=35",
                    after="rsi_period=10, rsi_buy=32",
                    reason="调整RSI买入阈值，测试更严格入场是否提高稳定性。",
                ),
                RunSpec(
                    symbol=symbol,
                    strategy_type="rsi",
                    baseline_config={"rsi_period": 10, "rsi_buy": 32},
                    proposal_config={"rsi_period": 18, "rsi_buy": 40},
                    before="rsi_period=10, rsi_buy=32",
                    after="rsi_period=18, rsi_buy=40",
                    reason="放宽RSI入场条件，观察交易次数与收益的权衡。",
                ),
                RunSpec(
                    symbol=symbol,
                    strategy_type="momentum",
                    baseline_config={"lookback": 20},
                    proposal_config={"lookback": 30},
                    before="lookback=20",
                    after="lookback=30",
                    reason="延长动量窗口，测试趋势过滤是否降低回撤。",
                ),
                RunSpec(
                    symbol=symbol,
                    strategy_type="momentum",
                    baseline_config={"lookback": 30},
                    proposal_config={"lookback": 12},
                    before="lookback=30",
                    after="lookback=12",
                    reason="缩短动量窗口，测试更快响应是否提高超额收益。",
                ),
            ]
        )
    repeated: list[RunSpec] = []
    while len(repeated) < limit:
        repeated.extend(specs)
    return repeated[:limit]


def _render_report(
    loop_runs: list[LoopRun],
    shadow_items: list[ShadowResult],
    recommendation: VersionRecommendation,
    raw_count: int,
    summary_count: int,
    proposal_count: int,
    shadow_count: int,
    db_path: Path,
) -> str:
    comparisons = [run.baseline_comparison for run in loop_runs if run.baseline_comparison]
    sharpe_diffs = _metric_values(comparisons, "sharpe")
    return_diffs = _metric_values(comparisons, "total_return")
    drawdown_diffs = _metric_values(comparisons, "max_drawdown")
    improved_sharpe = len([value for value in sharpe_diffs if value > 0])
    worsened_drawdown = len([value for value in drawdown_diffs if value > 0])
    actions = _counts([run.policy_action or "unknown" for run in loop_runs])
    evidence_by_proposal = _evidence_by_proposal(shadow_items)
    evidence_counts = _counts(
        [
            f"{evaluation.decision.value}/{evaluation.recommended_action.value}"
            for evaluation in evidence_by_proposal.values()
        ]
    )
    rows = [
        "# V2.9 Quant Demo Data Run Report",
        "",
        "## Summary",
        "",
        f"- Runs: {len(loop_runs)}",
        f"- Raw logs: {raw_count}",
        f"- Summary logs: {summary_count}",
        f"- Proposals: {proposal_count}",
        f"- Shadow results: {shadow_count}",
        f"- SQLite DB: `{db_path}` (ignored by git)",
        "- Scenario metric schema source: persisted scenario schema",
        "",
        "## Aggregate Metrics",
        "",
        f"- Sharpe diff avg: {_avg(sharpe_diffs):.6f}",
        f"- Total return diff avg: {_avg(return_diffs):.6f}",
        f"- Max drawdown diff avg: {_avg(drawdown_diffs):.6f}",
        f"- Sharpe improved count: {improved_sharpe}/{len(sharpe_diffs)}",
        f"- Drawdown worsened count: {worsened_drawdown}/{len(drawdown_diffs)}",
        f"- Policy actions: {actions}",
        f"- V3.1 evidence decisions: {evidence_counts}",
        f"- V3.3 recommendation decision: {recommendation.decision.value}",
        f"- V3.3 recommendation reason: {recommendation.reason}",
        "",
        "## What This Proves",
        "",
        "- V2 can create repeatable quant scenario runs.",
        "- V2 can capture objective metrics into logs.",
        "- V2 can generate manual proposal records.",
        "- V2 can run policy before shadow.",
        "- V2 can compare shadow metrics against baseline metrics.",
        "- Reports now have enough raw material for V3 MetricSchema design.",
        "- V3.1 can classify synthetic results as evidence for the loop, not evidence for strategy approval.",
        "- The report is explicitly marked as synthetic evidence, not a live-trading claim.",
        "",
        "## Issues Exposed Before V3",
        "",
        "- `PromptProposal` is being used to carry strategy parameter patches; V3 should introduce a generic `Proposal` or `StrategyProposal` abstraction.",
        "- `ScenarioPolicy` treats `constraints` changes as approval-level, which is acceptable for now but too coarse for parameter tuning.",
        "- Metric direction is now encoded for this run; V3 should persist scenario-specific schemas instead of using defaults.",
        "- Synthetic data is useful for reproducibility, but real historical data will be needed before any strategy judgment.",
        "- Evidence decisions are intentionally inconclusive until historical/paper/live runs provide stronger proof.",
        "",
        "## V3.1 MetricSchema Draft",
        "",
        "| Metric | Direction | Note |",
        "|---|---|---|",
        "| total_return | higher | strategy return over test period |",
        "| annual_return | higher | annualized return |",
        "| benchmark_return | reference | buy-and-hold baseline |",
        "| excess_return | higher | strategy minus benchmark |",
        "| max_drawdown | lower | risk guardrail |",
        "| sharpe | higher | risk-adjusted return |",
        "| win_rate | higher | trade quality, weak alone |",
        "| trade_count | bounded | too low means unreliable, too high means churn |",
        "| stability_score | higher | composite stability score |",
        "",
        "## Sample Runs",
        "",
    ]
    for run in loop_runs[:10]:
        rows.extend(
            [
                f"### {run.reason}",
                "",
                f"- loop_id: `{run.id}`",
                f"- status: {run.status.value}",
                f"- policy_action: {run.policy_action}",
                f"- proposal_id: `{run.proposal_id}`",
                "- run_kind: synthetic",
                "- provenance: data_source=synthetic_prices, generated_by=quant_research_demo",
                f"- business_metric_diff: {run.baseline_comparison}",
                *_evidence_rows(evidence_by_proposal.get(run.proposal_id or "")),
                "",
            ]
        )
    return "\n".join(rows)


def _evidence_by_proposal(shadow_items: list[ShadowResult]) -> dict[str, EvidenceEvaluation]:
    engine = EvidenceEvaluationEngine()
    evaluations: dict[str, EvidenceEvaluation] = {}
    for item in shadow_items:
        if not item.comparison_result:
            continue
        comparison = ComparisonResult(**item.comparison_result)
        evaluations[item.proposal_id] = engine.evaluate(comparison)
    return evaluations


def _evidence_rows(evaluation: EvidenceEvaluation | None) -> list[str]:
    if evaluation is None:
        return ["- evidence_decision: unavailable"]
    return [
        f"- evidence_decision: {evaluation.decision.value}",
        f"- evidence_recommended_action: {evaluation.recommended_action.value}",
        f"- evidence_confidence: {evaluation.confidence:.4f}",
        f"- evidence_reason: {evaluation.reason}",
    ]


def _metric_values(comparisons: list[dict[str, Any]], metric: str) -> list[float]:
    values: list[float] = []
    for comparison in comparisons:
        value = comparison.get(metric)
        if isinstance(value, int | float):
            values.append(float(value))
    return values


def _avg(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0


def _counts(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


if __name__ == "__main__":
    raise SystemExit(main())
