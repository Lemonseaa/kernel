# Kernel

Agent Workflow Kernel for building a general multi-agent operating system.

This repository starts with the core runtime skeleton and will grow around real workflow needs from OPC.

## V0.1 Scope

The first kernel version focuses on a small executable workflow core:

- Run model
- Task model and state machine
- Agent model and registry
- Workflow engine and executor
- Tool registry and permission checks
- Policy engine and human approval gate
- SQLite persistence for Run/Task state
- Event bus and audit log

## Validate Imports

```bash
python -c "from kernel.models import Run, Task, Agent; print('models OK')"
python -c "from kernel.runtime import AgentRegistry; print('runtime OK')"
python -c "from kernel.workflow import WorkflowEngine; print('workflow OK')"
python -c "from kernel.tools import ToolRegistry; print('tools OK')"
python -c "from kernel.control import PolicyEngine, HumanApprovalGate; print('control OK')"
python -c "from kernel.events import EventBus; print('events OK')"
python -c "from kernel import Kernel; print('kernel OK')"
```

## Run Tests

```bash
python -m unittest discover -s tests -v
```

## Evaluation Gate

Tasks can opt into generated-content quality checks:

```python
TaskSpec(
    description="生成小红书内容",
    evaluation_required=True,
    evaluation_platform="xiaohongshu",
    min_score=70.0,
)
```

The default gate runs readability, SEO, and platform-fit evaluators. A failing gate marks the task as
`evaluation_failed` and records suggestions in `task.result`.

## Notifications

The kernel includes a notification manager with console, webhook, and email channels. Human approval
requests can trigger notifications through the manager.

```bash
python -m kernel.cli notify --title "需要审批" --body "有任务等待处理"
```

## Dry Run

Dry run mode previews LLM and tool behavior without external API calls or side effects:

```bash
python -m kernel.cli dryrun --task "预演任务"
```

V0.2 now covers provider abstraction, memory/context, evaluation gate, notification, and dry run
simulation on top of the V0.1 workflow kernel.

## BusinessLine MVP

V0.3 introduces BusinessLine as a first-class runtime boundary. Runs, tasks, and agents carry a
`business_line_id`, SQLite can filter runs and tasks by business line, and `Kernel` exposes
`create_business_line()`, `get_business_line()`, and `list_business_lines()`.

The release also adds a simple plugin registry and a cost tracker that publishes `cost.updated` and
`cost.budget_exceeded` events so policy, approval, and notification layers can react to token usage.

## Templates And Policy

V0.4 adds built-in BusinessLine templates for `blank`, `content`, and `website`, plus
`Kernel.create_business_line_from_template()` for zero-configuration setup.

Policy now supports global rules and BusinessLine scoped overrides. Cost budget events can create
HumanGate approval requests, closing the loop from token usage to approval.

## Cross-Run Context And Daily Budget

V0.5 extends memory from run-scoped context to BusinessLine-scoped shared context. Evaluation failures
are saved as `evaluation_feedback`, and LLM agents include that feedback in later runs for the same
BusinessLine while keeping other BusinessLines isolated.

Cost tracking now uses daily counters as the budget signal, emits `cost.budget_warning` at 80% of a
daily budget, keeps `cost.budget_exceeded` for approval flows, and can report usage for a date range.

## Diagnostics And Alerts

V0.6 adds a health checker for fast failure triage. `HealthChecker.generate_diagnostic_report()`
checks SQLite, the LLM provider, EventBus subscriptions, approval queue backlog, cost budget status,
and recent failed runs, then returns repair recommendations.

The alert system turns runtime events into `warning` or `critical` notifications. It covers failed
tasks, failed runs, cost thresholds at 80% and 95%, exceeded budgets, approval timeouts, and provider
errors. `Kernel.resume_run(run_id, exclude_completed=True)` can continue from failed or pending tasks
while preserving completed task results.

## Auth, Webhooks, And CLI

V0.7 adds bearer-token API protection through `APIKeyManager` and `BearerTokenAuth`. API routes require
valid `Authorization: Bearer ...` headers when FastAPI is available, and fallback apps expose the same
authentication check for dependency-light environments.

Webhook support maps kernel events to external automation events: `run.completed`, `task.failed`,
`approval.required`, and `alert.triggered`. `WebhookReceiver` can trigger workflows from inbound
`workflow.trigger` payloads.

Operational commands are available through `./kernel-cli`: `status`, `run list`, `bl list`, and
`health`, with `--db` for pointing at a specific SQLite database.

## Risk Hardening

The current kernel verifies run-scoped context isolation, SQLite run recovery, high-risk tool blocking,
and provider retry/timeout behavior.

## Docker Deployment

V0.9 adds Docker Compose deployment and environment-driven configuration:

```bash
cp .env.example .env
docker-compose build
docker-compose up -d
docker-compose ps
```

Deployment docs live in [docs/deployment](docs/deployment/README.md).

## V1.0 Production Readiness

V1.0 adds lease-based HA primitives, multi-instance Compose configuration, benchmark/stress scripts,
and production readiness documentation.

```bash
python scripts/benchmark.py --runs 20
python scripts/stress_test.py --runs 50 --concurrency 5
python scripts/security_audit.py
```
