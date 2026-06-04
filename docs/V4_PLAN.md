# V4 Plan: Isolation and Adapter Architecture

## Position

V4 proves that CheckpointAI can support multiple scenarios and multiple adapters without data contamination or fake cross-scenario learning.

V4 does not implement TradingAgents or CrewAI adapters. Those require a compatibility report first.

## Hermes Decisions Adopted

1. Scenario has `archive`; physical delete remains a BusinessLine-level concern.
2. Cross-scenario insight uses human-provided tags first; automatic inference can come later.
3. Adapter compatibility reports are both Markdown review artifacts and SQLite records.
4. Adapter capabilities are structured in V4.2; dict compatibility is removed.
5. TradingAgents/CrewAI spike comes after V4.5.

## Versions

| Version | Scope |
|---|---|
| V4.1 | Scenario isolation hardening and audit |
| V4.2 | Structured adapter capabilities and explicit degradation |
| V4.3 | Adapter compatibility checklist and report store |
| V4.4 | Cross-scenario insight preview with rejection rules |
| V4.5 | Multi-scenario, multi-adapter stable verification |

## Real Data Rule

Cross-scenario insight cannot be suggested when either scenario has no non-synthetic recommendation evidence.

Synthetic data can validate the loop. It cannot justify cross-scenario transfer.
