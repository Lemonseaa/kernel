# System Boundaries

This document records the boundaries that matter after V2.10. It exists to prevent old V0/V1 concepts from leaking into the V2/V3 learning-loop design.

## Policy Layers

CheckpointAI has two policy layers. They are intentionally separate.

| Layer | Module | Scope | Used By |
|---|---|---|---|
| Runtime action policy | `checkpoint_ai/control/` | Tool/action risk, human approval, cost alerts, workflow execution | `CheckpointAI`, `WorkflowEngine`, `HumanApprovalGate` |
| Proposal policy | `checkpoint_ai/policy/` | Prompt/strategy/deployment proposals before shadow execution | V2 `AgentLoopEngine`, V3 evidence-based recommendation |

`control.PolicyEngine` is keyword/action based. It answers: "Can this runtime action proceed, or does it need human approval?"

`policy.ScenarioPolicy` is proposal based. It answers: "Can this proposed behavior change run shadow, auto-apply, wait for approval, or be blocked?"

Do not merge these layers until there is a clear shared contract. For now, the correct integration is naming clarity and explicit wiring.

## BusinessLine And Scenario

BusinessLine and Scenario are not duplicates.

| Concept | Meaning |
|---|---|
| BusinessLine | A top-level business/domain boundary: quant, media growth, content ops. It owns budgets, high-level config, lifecycle, and isolation. |
| Scenario | A bounded optimization domain inside a BusinessLine: quant moving-average research, XHS title optimization, publisher selection. It binds an adapter, prompts, metrics, proposals, shadows, and logs. |

A BusinessLine can own many Scenarios. A Scenario may also exist without a BusinessLine during demos and tests.

The code contract is:

```text
BusinessLine 1 ──► Scenario N
Scenario 1 ──────► Adapter 1
Scenario 1 ──────► Prompt/Proposal/Shadow/Logs/Metrics
```

V3 learning should use `scenario_id` as the primary learning scope. `business_line_id` is the parent boundary for isolation, reporting, budgets, and lifecycle.

## Historical Documents

Old V0 prompt documents were removed because they were implementation prompts, not stable architecture references. Historical architecture documents remain only as idea references and are not source of truth.

Current source of truth:

- [BLUEPRINT.md](BLUEPRINT.md)
- [SYSTEM_BOUNDARIES.md](SYSTEM_BOUNDARIES.md)
