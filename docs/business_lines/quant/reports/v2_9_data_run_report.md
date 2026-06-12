# V2.9 Quant Demo Data Run Report

## Summary

- Runs: 30
- Raw logs: 30
- Summary logs: 30
- Proposals: 30
- Shadow results: 30
- SQLite DB: `.runtime/v29_quant_demo.db` (ignored by git)
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

- loop_id: `4deb3a9d-93e2-4b59-bb93-6c0b196f4b8a`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `8d0f225f-7194-4ab2-83e6-e0e11d3de87a`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': -0.035084, 'annual_return': -0.03404, 'benchmark_return': 0.0, 'excess_return': -0.035083, 'max_drawdown': 0.008466, 'sharpe': -1.933942, 'win_rate': -0.088799, 'trade_count': 0.0, 'stability_score': 0.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 2: SPY/moving_average

- loop_id: `cedc024e-2a8c-442f-8930-6280d85f36c2`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `6af9c2d2-38f4-493b-b6aa-f635472d09bf`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': 0.064294, 'annual_return': 0.06236, 'benchmark_return': 0.0, 'excess_return': 0.064294, 'max_drawdown': -0.012798, 'sharpe': 3.715683, 'win_rate': 0.167266, 'trade_count': 0.0, 'stability_score': 0.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 3: SPY/rsi

- loop_id: `cd4e7fdd-cd9a-45d4-936b-589ef55c34cc`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `9dee70e4-254a-41a4-a503-096564994057`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': 0.155399, 'annual_return': 0.151147, 'benchmark_return': 0.0, 'excess_return': 0.1554, 'max_drawdown': -0.046183, 'sharpe': 11.547722, 'win_rate': 0.32986, 'trade_count': -1.0, 'stability_score': 1.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 4: SPY/rsi

- loop_id: `f6f4f525-7f98-43bc-b668-591d52cbac6b`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `481e62e5-cd23-4682-8aad-a4fc56dec034`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': 0.17415, 'annual_return': 0.169428, 'benchmark_return': 0.0, 'excess_return': 0.17415, 'max_drawdown': -0.063824, 'sharpe': 13.40559, 'win_rate': 0.416067, 'trade_count': -1.0, 'stability_score': 1.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 5: SPY/momentum

- loop_id: `13b48470-ef24-44dc-b352-0b3207c2f0c3`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `6cecd995-5f81-454f-b468-0c7f7a8274d3`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': -0.034579, 'annual_return': -0.03355, 'benchmark_return': 0.0, 'excess_return': -0.034579, 'max_drawdown': 0.008466, 'sharpe': -1.898845, 'win_rate': -0.083933, 'trade_count': 0.0, 'stability_score': 0.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 6: SPY/momentum

- loop_id: `c7e8f74a-d429-4399-bb0f-24946fbb920d`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `521bca8e-ea73-45c1-9a1f-60fc184d554c`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': 0.006849, 'annual_return': 0.006649, 'benchmark_return': 0.0, 'excess_return': 0.006849, 'max_drawdown': -0.009874, 'sharpe': 0.488206, 'win_rate': 0.011305, 'trade_count': 3.0, 'stability_score': 0.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 7: AAPL/moving_average

- loop_id: `70cd7827-835e-4ae7-ba36-753ce33b138a`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `2fb2838a-2657-4b8c-bb67-6fb9f67db66c`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': -0.042041, 'annual_return': -0.040786, 'benchmark_return': -0.035863, 'excess_return': -0.006176, 'max_drawdown': 0.008804, 'sharpe': -2.28714, 'win_rate': -0.11171, 'trade_count': -1.0, 'stability_score': 0.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 8: AAPL/moving_average

- loop_id: `98e0b0e8-2a1e-49d4-a989-235e024aa22a`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `fc6c05c0-e493-4b9e-9747-7ecbcc91c2f9`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': 0.067632, 'annual_return': 0.0656, 'benchmark_return': -0.035863, 'excess_return': 0.103496, 'max_drawdown': -0.009248, 'sharpe': 3.937838, 'win_rate': 0.132979, 'trade_count': -1.0, 'stability_score': 0.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 9: AAPL/rsi

- loop_id: `46aedb5f-3bd5-45b0-a721-eeb313524b75`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `950d6318-c407-4183-8a49-17a0677ac542`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': 0.143537, 'annual_return': 0.139587, 'benchmark_return': -0.035863, 'excess_return': 0.179401, 'max_drawdown': -0.035855, 'sharpe': 11.096933, 'win_rate': 0.312464, 'trade_count': -2.0, 'stability_score': 1.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.

### V2.9 data run 10: AAPL/rsi

- loop_id: `a0215a88-2b04-4c8a-84a6-cc797284dd68`
- status: completed
- policy_action: awaiting_human_confirmation
- proposal_id: `f1d62647-98c8-473f-95dd-14ca6159d964`
- run_kind: synthetic
- provenance: data_source=synthetic_prices, generated_by=quant_research_demo
- business_metric_diff: {'total_return': 0.155739, 'annual_return': 0.151478, 'benchmark_return': -0.035863, 'excess_return': 0.191603, 'max_drawdown': -0.047568, 'sharpe': 12.363421, 'win_rate': 0.356544, 'trade_count': -2.0, 'stability_score': 1.0}
- evidence_decision: inconclusive
- evidence_recommended_action: collect_more_evidence
- evidence_confidence: 0.6625
- evidence_reason: synthetic evidence can validate the loop but cannot justify recommendation.
