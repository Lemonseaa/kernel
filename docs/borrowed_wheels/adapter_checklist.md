# Adapter Compatibility Checklist

## Purpose

Decide whether an external Agent framework is worth adapting before writing adapter code.

This checklist is required for third-party frameworks such as TradingAgents and CrewAI.
First-party demos can be used to validate the contract, but third-party adapter code should not start before a compatibility report exists.

## Required Fields

| Area | Field | Required |
|---|---|---|
| Input/Output | Structured input | Yes |
| Input/Output | Structured output | Yes |
| Prompt Control | Prompt slots exposed | Preferred |
| Prompt Control | Prompt injection supported | Preferred |
| Execution | Shadow run supported | Preferred |
| Execution | Run trace available | Preferred |
| Metrics | Metrics capture supported | Yes |
| Metrics | Metric format compatible | Preferred |
| Integration Effort | Estimated days | Yes |
| Integration Effort | Dependencies | Yes |

## Decision Rules

- `no_go` if structured input is missing.
- `no_go` if structured output is missing.
- `no_go` if metrics capture is missing.
- `needs_spike` if estimated integration is more than 5 days.
- `needs_spike` if prompt slots, run trace, shadow run, or compatible metric format is unclear.
- `go` only when score is at least 0.75 and there are no blockers.

## Candidate Reports

### TradingAgents

Status: not evaluated.

### CrewAI

Status: not evaluated.
