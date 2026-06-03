# CheckpointAI

[![Tests](https://img.shields.io/badge/tests-112%20passed-brightgreen)](https://github.com/Lemonseaa/checkpointAI)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-Non--Commercial-red)](LICENSE)

CheckpointAI is a code-first experiment and optimization system for Agent teams.

It is not a low-code workflow builder, Agent runtime replacement, or Dify clone. Its job is to make Agent behavior changes observable, comparable, reversible, and evidence-based.

## License

CheckpointAI is source-available for non-commercial use. Commercial use requires prior written authorization. See [LICENSE](LICENSE).

## Current Direction

```text
Dify = prototype tool / workflow reference / plugin ecosystem reference
TradingAgents = quant Agent team template / multi-role research workflow reference
CheckpointAI = experiment ledger / evaluation / baseline compare / shadow compare / patch / version / risk gate / approval console
```

The authoritative roadmap is [docs/BLUEPRINT.md](docs/BLUEPRINT.md).

## Core Question

```text
Can I know whether each Agent / workflow change actually made the system better?
```

If the answer is yes, CheckpointAI is useful.

## What CheckpointAI Does

- Records experiments with hypothesis, baseline, result, and conclusion.
- Captures Agent run traces, tool calls, parameters, outputs, and metrics.
- Compares prompt / strategy / workflow versions against baselines.
- Runs shadow or replay tests before applying changes.
- Generates patch proposals instead of uncontrolled prompt rewrites.
- Applies risk and evidence gates before approval or automatic low-risk changes.
- Provides an approval and experiment review console.

## What CheckpointAI Does Not Do

- It does not provide a drag-and-drop workflow builder.
- It does not replace Dify as a prototyping tool.
- It does not depend on Dify as the final execution layer.
- It does not blindly fork TradingAgents.
- It does not promise automatic profit, automatic followers, or fake learning from small samples.

## Main Concepts

| Concept | Meaning |
|---|---|
| Scenario | A bounded optimization domain, such as quant research or media growth. |
| Experiment | A recorded attempt to improve behavior, with hypothesis and result. |
| Run | One execution of an Agent team or business workflow. |
| Trace | Structured record of each Agent step, tool call, parameter, and output. |
| Baseline | The current version or benchmark used for comparison. |
| Patch | A bounded change to prompt, workflow, tool policy, strategy, or parameters. |
| Shadow / Replay | Test a candidate version before applying it. |
| Evidence Gate | Blocks recommendations when data is not strong enough. |
| Risk Gate | Decides whether a change is automatic, approval-required, or blocked. |

## Intended Business Teams

```text
Quant Team:
TradingAgents-style research roles + data/backtest/risk tools + CheckpointAI experiment control

Media Team:
trend/content/publishing/traffic-feedback agents + CheckpointAI experiment control
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
- [Architecture Overview](docs/ARCHITECTURE_OVERVIEW.md): historical architecture reference.
- [Business Line Architecture](docs/BUSINESS_LINE_ARCHITECTURE.md): historical isolation design reference.
- [Innovation Research](docs/INNOVATION_RESEARCH.md): historical research notes.
