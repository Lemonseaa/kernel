# CheckpointAI

**Workflow Optimization Console**

[![Tests](https://img.shields.io/badge/tests-173%20passed-brightgreen)](https://github.com/Lemonseaa/checkpointAI)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-Non--Commercial-red)](LICENSE)

CheckpointAI is a workflow optimization framework.

It connects to external Agent teams, automation workflows, and business processes, then makes their behavior observable, comparable, reversible, and evidence-based.

It is not a low-code workflow builder, Agent runtime replacement, or Dify clone. Its job is to turn workflow changes from black-box guesses into traceable experiments.

## License

CheckpointAI is source-available for non-commercial use. Commercial use requires prior written authorization. See [LICENSE](LICENSE).

Commercial authorization contact: liminxi634@163.com

## Current Direction

```text
Dify = prototype tool / workflow reference / plugin ecosystem reference
TradingAgents = quant Agent team template / multi-role research workflow reference
CheckpointAI = workflow observation layer + optimization layer + evidence layer + approval layer
```

The authoritative roadmap is [docs/BLUEPRINT.md](docs/BLUEPRINT.md).

## Core Question

```text
Can I know why a workflow should change, what changed, whether it improved, and whether it violates my risk boundary or methodology?
```

If the answer is yes, CheckpointAI is useful.

## What CheckpointAI Does

- Converts external workflows into observable workflow contracts and maps.
- Captures run traces, tool calls, parameters, outputs, costs, errors, and metrics.
- Records experiments with hypothesis, baseline, change, result, and conclusion.
- Compares prompt / strategy / workflow / model / tool-policy versions against baselines.
- Runs shadow or replay tests before applying changes.
- Generates bounded patch proposals instead of uncontrolled rewrites.
- Applies evidence, risk, and methodology gates before approval or low-risk automation.
- Visualizes workflow structure, black-box nodes, metric trends, and before/after impact.
- Provides a governance console for approvals, reports, backups, rollback, and provider health.

## What CheckpointAI Does Not Do

- It does not provide a drag-and-drop workflow builder.
- It does not replace Dify as a prototyping tool.
- It does not depend on Dify as the final execution layer.
- It does not blindly fork TradingAgents or any external framework.
- It does not optimize fully black-box workflows that expose no trace, metrics, or configurable surface.
- It does not automatically deploy live trading, publish content, delete history, or bypass human final control.
- It does not promise automatic profit, automatic followers, or real learning from tiny samples.

## Main Concepts

| Concept | Meaning |
|---|---|
| BusinessLine | A top-level business/domain boundary for lifecycle, budgets, isolation, and reporting. |
| Scenario | A bounded optimization domain, such as quant research or media growth. |
| WorkflowContract | The structured interface that exposes a workflow's nodes, edges, inputs, outputs, metrics, and configurable surfaces. |
| WorkflowMap | A visual map of stages, nodes, run traces, black-box areas, and optimization candidates. |
| Experiment | A recorded attempt to improve behavior, with hypothesis and result. |
| Run | One execution of an Agent team or business workflow. |
| Trace | Structured record of each Agent step, tool call, parameter, and output. |
| Baseline | The current version or benchmark used for comparison. |
| Patch | A bounded change to prompt, workflow, tool policy, strategy, or parameters. |
| Shadow / Replay | Test a candidate version before applying it. |
| Evidence Gate | Blocks recommendations when data is not strong enough. |
| Risk Gate | Decides whether a change is automatic, approval-required, or blocked. |
| Methodology Profile | Human-owned preferences, standards, risk boundaries, style, and decision rules. |

## Intended Business Teams

```text
Quant Team:
TradingAgents-style research roles + data/backtest/risk tools + CheckpointAI experiment control

Media Team:
trend/content/publishing/traffic-feedback agents + CheckpointAI experiment control

Workflow Team:
external automation or Agent workflow + CheckpointAI workflow map + trace + impact visualization
```

## Quick Start

```bash
pip install -e .
checkpointai status
```

Docker:

```bash
cp .env.example .env
docker compose up -d
docker compose ps
```

## Development

```bash
python -m unittest discover -s tests -v
python -m ruff check checkpoint_ai tests scripts
python -m mypy checkpoint_ai --show-error-codes --no-incremental
```

## Documentation

- [Blueprint](docs/BLUEPRINT.md): current source of truth.
- [System Boundaries](docs/SYSTEM_BOUNDARIES.md): policy and BusinessLine/Scenario boundaries.
- [Architecture Overview](docs/ARCHITECTURE_OVERVIEW.md): historical architecture reference.
- [Business Line Architecture](docs/BUSINESS_LINE_ARCHITECTURE.md): historical isolation design reference.
- [Innovation Research](docs/INNOVATION_RESEARCH.md): historical research notes.
