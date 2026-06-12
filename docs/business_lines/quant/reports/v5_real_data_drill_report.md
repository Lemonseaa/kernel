# V2.9 Quant Demo Data Run Report

## Summary

- Runs: 30
- Raw logs: 30
- Summary logs: 30
- Proposals: 30
- Shadow results: 30
- SQLite DB: `.runtime/v5_quant_drill.db` (ignored by git)
- Scenario metric schema source: persisted scenario schema

## Aggregate Metrics

- Sharpe diff avg: 4.100566
- Total return diff avg: 0.052227
- Max drawdown diff avg: -0.017134
- Sharpe improved count: 20/30
- Drawdown worsened count: 10/30
- Policy actions: {'awaiting_human_confirmation': 30}
- V3.1 evidence decisions: {'inconclusive/collect_more_evidence': 30}
- V3.3 recommendation decision: insufficient_evidence
- V3.3 recommendation reason: synthetic evidence can validate the loop but cannot justify recommendation.

## What This Proves

- V2 can create repeatable quant scenario runs.
- V2 can capture objective metrics into logs.
- V2 can generate manual proposal records.
- V2 can run policy before shadow.
- V2 can compare shadow metrics against baseline metrics.
- Reports now have enough raw material for V3 MetricSchema design.
- V3.1 can classify synthetic results as evidence for the loop, not evidence for strategy approval.
- The report is explicitly marked as synthetic evidence, not a live-trading claim.

## Issues Exposed Before V3

- `PromptProposal` is being used to carry strategy parameter patches; V3 should introduce a generic `Proposal` or `StrategyProposal` abstraction.
- `ScenarioPolicy` treats `constraints` changes as approval-level, which is acceptable for now but too coarse for parameter tuning.
- Metric direction is now encoded for this run; V3 should persist scenario-specific schemas instead of using defaults.
- Synthetic data is useful for reproducibility, but real historical data will be needed before any strategy judgment.
- Evidence decisions are intentionally inconclusive until historical/paper/live runs provide stronger proof.

## V3.1 MetricSchema Draft

| Metric | Direction | Note |
|---|---|---|
| total_return | higher | strategy return over test period |
| annual_return | higher | annualized return |
| benchmark_return | reference | buy-and-hold baseline |
| excess_return | higher | strategy minus benchmark |
| max_drawdown | lower | risk guardrail |
| sharpe | higher | risk-adjusted return |
| win_rate | higher | trade quality, weak alone |
| trade_count | bounded | too low means unreliable, too high means churn |
| stability_score | higher | composite stability score |

## Sample Runs

### V2.9 data run 1: SPY/moving_average

- loop_id: `48d388a6-b379-4ae9-a103-8a91e81eb683`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `76ef1132-265d-4f28-860e-53ecf7961430`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': -0.035084, 'annual_return': -0.03404, 'benchmark_return': 0.0, 'excess_return': -0.035083, 'max_drawdown': 0.008466, 'sharpe': -1.933942, 'win_rate': -0.088799, 'trade_count': 0.0, 'stability_score': 0.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 2: SPY/moving_average

- loop_id: `93c00d27-0203-485d-bd07-1c4d5e0355a6`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `842497f4-182a-4b61-bd83-75ee0ef6ee3a`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': 0.064294, 'annual_return': 0.06236, 'benchmark_return': 0.0, 'excess_return': 0.064294, 'max_drawdown': -0.012798, 'sharpe': 3.715683, 'win_rate': 0.167266, 'trade_count': 0.0, 'stability_score': 0.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 3: SPY/rsi

- loop_id: `bda85445-b8a6-481d-8733-4912034a2e4e`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `005a634f-1b0c-422d-ac60-72431a381942`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': 0.155399, 'annual_return': 0.151147, 'benchmark_return': 0.0, 'excess_return': 0.1554, 'max_drawdown': -0.046183, 'sharpe': 11.547722, 'win_rate': 0.32986, 'trade_count': -1.0, 'stability_score': 1.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 4: SPY/rsi

- loop_id: `8a3d2509-3b58-4cc3-9e69-2e169259594f`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `bd2b906d-cd7f-4d11-b9cc-af90066517b1`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': 0.17415, 'annual_return': 0.169428, 'benchmark_return': 0.0, 'excess_return': 0.17415, 'max_drawdown': -0.063824, 'sharpe': 13.40559, 'win_rate': 0.416067, 'trade_count': -1.0, 'stability_score': 1.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 5: SPY/momentum

- loop_id: `52a2a5fb-5e8f-418f-8536-36bfebb348d8`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `c45a9dfa-7788-449a-9733-f50f85577e94`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': -0.034579, 'annual_return': -0.03355, 'benchmark_return': 0.0, 'excess_return': -0.034579, 'max_drawdown': 0.008466, 'sharpe': -1.898845, 'win_rate': -0.083933, 'trade_count': 0.0, 'stability_score': 0.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 6: SPY/momentum

- loop_id: `a1dd2aa4-623f-4e87-8ced-fa7f9237d3cd`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `40eaa88c-e325-4d20-98e7-c992b59781d8`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': 0.006849, 'annual_return': 0.006649, 'benchmark_return': 0.0, 'excess_return': 0.006849, 'max_drawdown': -0.009874, 'sharpe': 0.488206, 'win_rate': 0.011305, 'trade_count': 3.0, 'stability_score': 0.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 7: AAPL/moving_average

- loop_id: `e4a41d48-3a97-4980-8050-dbafa817fb83`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `8a62be2f-d886-49bf-ad49-337ffb868a2b`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': -0.042041, 'annual_return': -0.040786, 'benchmark_return': -0.035863, 'excess_return': -0.006176, 'max_drawdown': 0.008804, 'sharpe': -2.28714, 'win_rate': -0.11171, 'trade_count': -1.0, 'stability_score': 0.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 8: AAPL/moving_average

- loop_id: `270f048d-75ec-49a0-9ac6-18ff37cc6900`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `7198ab18-cc3f-4be4-9e3a-e54cfe7369cb`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': 0.067632, 'annual_return': 0.0656, 'benchmark_return': -0.035863, 'excess_return': 0.103496, 'max_drawdown': -0.009248, 'sharpe': 3.937838, 'win_rate': 0.132979, 'trade_count': -1.0, 'stability_score': 0.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 9: AAPL/rsi

- loop_id: `033064d2-e5ac-41aa-85cf-a52e40a33fd9`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `0e31f99b-0b85-43a0-92b7-f4c43f59ad8c`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': 0.143537, 'annual_return': 0.139587, 'benchmark_return': -0.035863, 'excess_return': 0.179401, 'max_drawdown': -0.035855, 'sharpe': 11.096933, 'win_rate': 0.312464, 'trade_count': -2.0, 'stability_score': 1.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 10: AAPL/rsi

- loop_id: `d6677240-fcb6-406e-a9fb-08283458b10d`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `2230ab3a-c2d2-466d-9c34-432846fa9cdd`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': 0.155739, 'annual_return': 0.151478, 'benchmark_return': -0.035863, 'excess_return': 0.191603, 'max_drawdown': -0.047568, 'sharpe': 12.363421, 'win_rate': 0.356544, 'trade_count': -2.0, 'stability_score': 1.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.
