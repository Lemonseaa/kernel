# CheckpointAI

**External Workflow Evidence Harness**

[![Tests](https://img.shields.io/badge/tests-256%20passed-brightgreen)](https://github.com/Lemonseaa/checkpointAI)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-Non--Commercial-red)](LICENSE)

CheckpointAI is an evidence harness for external workflows.

It connects to external Agent teams, automation workflows, and business processes, then turns their runs and changes into observable, visualizable, comparable, reviewable, and reversible evidence.

It is not a low-code workflow builder, Agent runtime replacement, Dify clone, Nexent clone, or TradingAgents clone. Its job is to judge whether workflow changes actually improved outcomes.

## License

CheckpointAI is source-available for non-commercial use. Commercial use requires prior written authorization. See [LICENSE](LICENSE).

Commercial authorization contact: liminxi634@163.com

## Current Direction

```text
Dify = prototype tool / workflow reference / plugin ecosystem reference
TradingAgents = quant Agent team template / multi-role research workflow reference
CheckpointAI = evidence harness + workflow visualization + review layer + approval layer + rollback layer
```

The authoritative roadmap is [docs/BLUEPRINT.md](docs/BLUEPRINT.md).

## Core Question

```text
Can I prove whether an external workflow change made things better, worse, or inconclusive?
```

If the answer is yes, CheckpointAI is useful.

## What CheckpointAI Does

- Ingests external workflow runs through an Evidence Adapter.
- Normalizes workflow contracts, traces, configs, artifacts, and metrics.
- Visualizes imported workflow structure, run paths, black-box nodes, trace coverage, metric coverage, cost, latency, and errors.
- Records experiments with hypothesis, baseline, change, result, and conclusion.
- Compares prompt / strategy / workflow / model / tool-policy versions against baselines.
- Runs shadow or replay checks before humans accept changes.
- Applies evidence, risk, and methodology gates before approval.
- Produces evidence reports that support approve / reject / rollback decisions.

## What CheckpointAI Does Not Do

- It does not provide a drag-and-drop workflow builder.
- It does not replace Dify as a prototyping tool.
- It does not depend on Dify as the final execution layer.
- It does not blindly fork TradingAgents or any external framework.
- It does not optimize fully black-box workflows that expose no trace, metrics, or configurable surface.
- It does not automatically deploy live trading, publish content, delete history, or bypass human final control.
- It does not build a full plugin marketplace or full model provider platform.
- It does not promise automatic profit, automatic followers, or real learning from tiny samples.

## Main Concepts

| Concept | Meaning |
|---|---|
| BusinessLine | A top-level business/domain boundary for lifecycle, budgets, isolation, and reporting. |
| Scenario | A bounded optimization domain, such as quant research or media growth. |
| EvidenceAdapter | Ingests external workflow run JSON and normalizes it into CheckpointAI evidence. |
| WorkflowContract | The structured interface that exposes a workflow's nodes, edges, inputs, outputs, metrics, and configurable surfaces. |
| WorkflowVisualization | Diagnostic map of imported workflows: nodes, run paths, black boxes, coverage, risk, cost, latency, and errors. |
| Experiment | A recorded attempt to improve behavior, with hypothesis and result. |
| Run | One execution of an Agent team or business workflow. |
| Trace | Structured record of each Agent step, tool call, parameter, and output. |
| Baseline | The current version or benchmark used for comparison. |
| Candidate | A proposed workflow/config/strategy version compared against a baseline. |
| Shadow / Replay | Test a candidate version before humans accept it. |
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
external automation or Agent workflow + CheckpointAI evidence adapter + workflow visualization + report + decision log
```

## Quick Start

```bash
pip install -e .
checkpointai status
```

Evidence harness example:

```bash
checkpointai evidence ingest examples/evidence/quant_baseline_run.json
checkpointai evidence ingest examples/evidence/quant_candidate_run.json
checkpointai evidence visualize --run quant_candidate_001
checkpointai evidence compare --baseline quant_baseline_001 --candidate quant_candidate_001
checkpointai evidence report --run quant_candidate_001
```

Python API:

```python
from checkpoint_ai import EvidenceHarness

harness = EvidenceHarness(".runtime/evidence.db")
harness.ingest_file("examples/evidence/quant_baseline_run.json")
harness.ingest_file("examples/evidence/quant_candidate_run.json")
report = harness.compare("quant_baseline_001", "quant_candidate_001")
print(report.recommendation)
```

HTTP API:

```text
POST /api/evidence/runs
GET  /api/evidence/runs?workflow_id=...
GET  /api/evidence/runs/{run_id}/visualization
GET  /api/evidence/runs/{run_id}/report
POST /api/evidence/compare
```

Quant drill example:

```bash
checkpointai evidence quant-drill --candidates 30 --comparisons 5
```

This creates a deterministic semi-real historical drill: one baseline, thirty candidate
runs, five baseline/candidate comparisons, workflow visualization data, and a paper-trade
recommendation. It validates the evidence chain; it is not a live trading signal.

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

Repository structure:

```text
checkpoint_ai/evidence/        Mainline Evidence Harness code.
docs/core_innovation/          CheckpointAI-owned product ideas.
docs/borrowed_wheels/          External wheels and replacement strategy.
docs/business_lines/           Quant, content, and demo domain docs.
tests/evidence/                Mainline evidence tests.
tests/business_lines/quant/    Quant validation tests.
tests/support/                 Support module regression tests.
tests/legacy/                  Historical compatibility tests.
examples/evidence/             Evidence input examples.
examples/support/              Current support examples.
scripts/ops/                   Operational scripts.
scripts/business_lines/quant/  Quant business-line scripts.
```

## Documentation

- [Docs Index](docs/README.md): where each kind of document belongs.
- [Blueprint](docs/BLUEPRINT.md): current source of truth.
- [Strategic Reset Plan](docs/STRATEGIC_RESET_PLAN.md): current execution plan.
- [Core Innovation](docs/core_innovation/README.md): evidence harness, workflow visualization, metric schema, and human methodology.
- [Borrowed Wheels](docs/borrowed_wheels/README.md): external projects, replacement wheels, and adapter compatibility.
- [Business Lines](docs/business_lines/README.md): quant, content, and temporary demo applications.
- [Legacy Replacement Matrix](docs/borrowed_wheels/legacy_replacement_matrix.md): replacement, rewrite, keep, and isolation decisions for old modules.
- [System Boundaries](docs/SYSTEM_BOUNDARIES.md): policy and BusinessLine/Scenario boundaries.
- [Archive](docs/archive/README.md): historical architecture and research references.
