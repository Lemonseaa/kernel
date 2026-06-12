# Legacy Replacement Matrix

## Purpose

LoopHarness is now focused on the External Workflow Evidence Harness.

This matrix prevents destructive cleanup. Each old module is classified before deletion:

```text
replace  = use a mature external tool instead
rewrite  = keep the concept, rebuild a thin Evidence Harness version
keep     = core LoopHarness evidence capability
isolate  = support module; keep temporarily, do not expand
legacy   = historical compatibility only
```

Rule:

```text
Do not delete a module just because it is old.
Delete only when the Evidence Harness path no longer needs it and a replacement path is clear.
```

---

## Core Evidence Path

These modules are part of the new direction.

| Module | Decision | Reason |
|---|---|---|
| `loop_harness/evidence/` | keep | New external workflow evidence adapter, visualization data, reports |
| `loop_harness/metrics/` | keep | Metric direction/category/weight/threshold are core to evidence judgment |
| `loop_harness/evaluation/evidence.py` | keep | Evidence decision engine |
| `loop_harness/shadow/comparison.py` | keep | Baseline vs candidate comparison logic |
| `loop_harness/decision/` | keep | DecisionLog remains core for approve/reject/rollback audit |
| `loop_harness/experiment/` | keep | Experiment Ledger concepts remain useful, but future writes should be evidence-oriented |
| `loop_harness/policy/` | keep | Proposal/evidence policy remains useful |
| `loop_harness/control/` | isolate | Runtime policy legacy exists; avoid new evidence dependency unless needed |

---

## Direct Replacement Candidates

These are mature elsewhere. LoopHarness should not compete with them.

Strategic references such as Archon, ARIS, learn-harness-engineering, and Nexent
are documented separately in:

```text
docs/borrowed_wheels/reference_projects.md
```

This file is only for module cleanup and replacement decisions.

| Module | External Wheel | Decision | Cleanup Timing |
|---|---|---|---|
| `loop_harness/workflow/` | LangGraph / Temporal / Prefect / Archon | replace | frozen in Batch 2 |
| `loop_harness/runtime/` | CrewAI / LangGraph / external agent runtimes | replace | frozen in Batch 2 |
| `loop_harness/plugins/` | MCP / Dify plugins / external tool directories | replaced | deleted in Batch 1 |
| `loop_harness/scheduler/` | cron / APScheduler / external orchestrators | replaced | deleted in Batch 1 |
| `loop_harness/ha/` | deployment platform / Docker / cloud infra | replaced | deleted in Batch 1 |
| `loop_harness/templates/` | external workflow templates / examples | replaced | deleted in Batch 1 |
| `loop_harness/alerts/` | EventBus signals / external notification routing | replaced | deleted in Batch 1.5 |
| `loop_harness/tools/` | MCP / external tools / domain scripts | replace | keep only thin adapters used by evidence drills |

### Replacement Projects Checked

| Area | Candidate | What it replaces | Decision |
|---|---|---|---|
| Scheduling | [APScheduler](https://github.com/agronholm/apscheduler) | internal recurring jobs / cron-like scheduling | prefer external scheduler when recurring runs are needed |
| Durable workflow | [Temporal](https://github.com/temporalio/temporal) | HA workflow execution / durable retries / failover | do not rebuild; use only if LoopHarness needs durable orchestration |
| Python workflow orchestration | [Prefect](https://github.com/PrefectHQ/prefect) | data/workflow orchestration layer | reference or integrate later; do not clone |
| LLM provider platform | [LiteLLM](https://github.com/BerriAI/litellm) | broad provider routing, cost tracking, fallback, proxy | do not build a full model console unless evidence harness needs a thin adapter |
| Tool ecosystem | [Model Context Protocol servers](https://github.com/modelcontextprotocol/servers) | plugin marketplace / tool registry ecosystem | prefer guarded MCP integration over custom plugin platform |

Security note:

```text
External tool ecosystems are replacements for plumbing, not trusted by default.
MCP/plugin/tool connections need allowlists, credential boundaries, and explicit
human approval for sensitive side effects.
```

---

## Rewrite Candidates

The concepts are useful, but old implementations should not drive the new architecture.

| Module | New Shape | Decision |
|---|---|---|
| `loop_harness/adapter/` | `EvidenceAdapter` connectors that export run JSON | rewrite |
| `loop_harness/external_agents/` | External workflow source registry, not agent platform | freeze then rewrite as needed |
| `loop_harness/prompt/` | Candidate config/prompt patch evidence, not prompt platform | evidence_support |
| `loop_harness/recommendation/` | Evidence recommendation derived from reports | evidence_support |
| `loop_harness/optimization/` | Candidate suggestion after evidence review, not autonomous optimizer | isolate |
| `loop_harness/learning/` | ARIS-style review/audit loop, not autonomous self-improvement loop | rewrite |
| `loop_harness/autonomy/` | Conservative queue for approved evidence actions only | isolate |
| `loop_harness/logs/` | Workflow trace/event evidence logs | evidence_support |

---

## Temporary Support Modules

Keep these for now. They support the current package or CLI, but should not expand into platform work.

| Module | Decision | Boundary |
|---|---|---|
| `loop_harness/config.py` | isolate | env/config only |
| `loop_harness/auth/` | isolate | API auth only |
| `loop_harness/control/` | isolate | runtime approval compatibility only; proposal decisions belong in scenario policy and evidence review |
| `loop_harness/events/` | evidence_support | local audit/event plumbing only |
| `loop_harness/experiment/` | evidence_support | evidence ledger and baseline accounting; historical loop engine is compatibility only |
| `loop_harness/loop/` | evidence_support | bounded one-shot evidence loop only; no autonomous infinite loop |
| `loop_harness/observability/` | evidence_support | cost/performance signals for evidence reports |
| `loop_harness/llm/` | isolate | minimal provider abstraction; do not become LiteLLM clone |
| `loop_harness/console/` | evidence_support | human decision console only |
| `loop_harness/api.py` | isolate | only expose evidence/decision endpoints when needed |
| `loop_harness/persistence/` | evidence_support | storage utilities only |
| `loop_harness/notification/` | isolate | only notify human-actionable decisions |
| `loop_harness/diagnostics/` | evidence_support | actionable health checks |
| `loop_harness/tools/` | isolate | compatibility tools only; real integrations should use guarded external connectors |

---

## Domain Boundary Modules

These may survive if they help evidence scoping, but should be simplified.

| Module | Decision | Notes |
|---|---|---|
| `loop_harness/businessline/` | isolate | Useful as top-level business/domain boundary, but not platform tenant system |
| `loop_harness/scenario/` | evidence_support | Main evidence scope for runs, metrics, prompts, reports, decisions |
| `loop_harness/isolation/` | evidence_support | Keep only if it protects evidence scope |
| `loop_harness/user_profile/` | keep | Human methodology/profile boundaries are differentiating |
| `loop_harness/memory/` | isolate | Do not use as vague self-evolution memory |

---

## Historical / Legacy Tests

Many existing tests protect old platform features. Do not use full legacy test count as the product progress metric.

Current test split:

```text
tests/evidence/      mainline evidence harness tests
tests/business_lines/quant/
                    quant business-line validation tests
tests/legacy/        historical compatibility tests
tests/support/       shared support modules
```

Until that split happens:

```text
python -m unittest discover -s tests -v
```

still runs as regression safety, but the mainline acceptance is the evidence path.

---

## Cleanup Order

### Batch 1: Delete replaced platform plumbing

```text
plugins
templates
ha
scheduler
```

Action:

```text
Remove internal implementations that duplicate mature external tools.
Keep no package import compatibility for deleted modules.
```

Status:

```text
plugins / templates / ha / scheduler deleted.
alerts deleted; cost threshold events still flow through EventBus and HumanApprovalGate.
insights kept as evidence-support because reporting still uses it.
```

### Batch 2: Replace execution layer

```text
runtime
workflow
external_agents
adapter
```

Action:

```text
Move useful contracts into evidence connectors.
Retire old Run/Task execution as mainline.
```

Status:

```text
runtime        frozen: compatibility only
workflow       frozen: compatibility only
external_agents frozen: compatibility only
adapter        rewrite: still used by V2-V7 demos, but future mainline is EvidenceAdapter
```

Deletion condition:

```text
Do not delete runtime/workflow/external_agents until their legacy tests are
moved to tests/legacy or the compatibility surface is intentionally removed.

Do not delete adapter until the current demo/shadow paths are replaced by
workflow-run JSON ingestion through loop_harness/evidence.
```

### Batch 3: Rewrite old optimization layer

```text
learning
autonomy
recommendation
optimization
prompt
logs
```

Action:

```text
Convert into Evidence Review / Candidate / Report concepts or remove.
```

Status:

```text
prompt          evidence_support: patch-first candidate change contracts
logs            evidence_support: raw/summary evidence chain
recommendation  evidence_support: only evidence-derived recommendations
optimization    isolate: bounded suggestions only, never auto execution
autonomy        isolate: approved reversible action queue only
learning        rewrite: ARIS-style evidence review, not self-improvement platform
```

Deletion condition:

```text
Do not delete prompt/logs/recommendation while they produce evidence reports.
Do not expand optimization/autonomy without policy, rollback, and decision logs.
Rewrite learning only toward audit/review loops with stored evidence.
```

### Batch 4: Bound support modules

```text
auth
events
observability
llm
console
persistence
notification
diagnostics
```

Action:

```text
Keep support modules, but prevent platform expansion.
```

Status:

```text
auth          isolate: thin API auth
llm           isolate: thin provider adapter, not model console
notification  isolate: human-actionable notifications only
events        evidence_support: local audit/event plumbing
observability evidence_support: evidence cost/performance signals
console       evidence_support: human decision surface
persistence   evidence_support: local store utilities
diagnostics   evidence_support: actionable system health
```

### Batch 5: Bound domain modules

```text
businessline
scenario
isolation
user_profile
memory
```

Action:

```text
Keep domain boundaries, but prevent platform/tenant/memory expansion.
```

Status:

```text
businessline  isolate: coarse business/domain boundary, not tenant platform
scenario      evidence_support: primary evidence scope
isolation     evidence_support: scenario evidence boundary checks
user_profile  keep: human-owned methodology and preference profile
memory        isolate: legacy runtime context; prefer explicit evidence logs
```

---

## Import Boundary

`loop_harness/evidence/` must stay thin.

Allowed dependencies:

```text
loop_harness.metrics
loop_harness.evaluation.evidence
loop_harness.shadow.comparison
standard library
pydantic
sqlite3
```

Disallowed dependencies:

```text
runtime
workflow
plugins
scheduler
ha
learning
autonomy
insights
templates
agent_config
external_agents
```

This keeps the new direction from inheriting the old platform architecture.
