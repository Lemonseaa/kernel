"""V2 CLI commands for scenarios, adapters, prompts, proposals, shadows, and reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from checkpoint_ai.adapter import (
    AdapterRegistry,
    DummyAdapter,
    OPCAgentAdapter,
    QuantResearchDemoAdapter,
)
from checkpoint_ai.logs import RawLogStore, SummaryLogStore
from checkpoint_ai.prompt import (
    PromptPatch,
    PromptProposal,
    PromptProposalStatus,
    PromptProposalStore,
    PromptSlot,
    PromptVersionStore,
)
from checkpoint_ai.reporting import ReportGenerator
from checkpoint_ai.scenario import Scenario, ScenarioRegistry, ScenarioRunner, ScenarioStore
from checkpoint_ai.shadow import ShadowResultStore, ShadowRunner


def register_v2_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register V2 human-facing command groups."""

    scenario = subparsers.add_parser("scenario")
    scenario_sub = scenario.add_subparsers(dest="scenario_command")
    scenario_create = scenario_sub.add_parser("create")
    scenario_create.add_argument("--id", required=True)
    scenario_create.add_argument("--name", required=True)
    scenario_create.add_argument("--description", required=True)
    scenario_create.add_argument("--adapter", required=True)
    scenario_create.add_argument("--adapter-config-json", default="{}")
    scenario_sub.add_parser("list")
    scenario_show = scenario_sub.add_parser("show")
    scenario_show.add_argument("scenario_id")

    adapter = subparsers.add_parser("adapter")
    adapter_sub = adapter.add_subparsers(dest="adapter_command")
    adapter_run = adapter_sub.add_parser("run")
    adapter_run.add_argument("--scenario-id", required=True)
    adapter_run.add_argument("--task", required=True)
    adapter_run.add_argument("--context-json", default="{}")
    adapter_run.add_argument("--config-json", default="{}")

    prompt = subparsers.add_parser("prompt")
    prompt_sub = prompt.add_subparsers(dest="prompt_command")
    prompt_history = prompt_sub.add_parser("history")
    prompt_history.add_argument("--scenario-id", required=True)
    prompt_history.add_argument("--agent-id", required=True)
    prompt_rollback = prompt_sub.add_parser("rollback")
    prompt_rollback.add_argument("--scenario-id", required=True)
    prompt_rollback.add_argument("--agent-id", required=True)
    prompt_rollback.add_argument("--reason", required=True)

    proposal = subparsers.add_parser("proposal")
    proposal_sub = proposal.add_subparsers(dest="proposal_command")
    proposal_sub.add_parser("list").add_argument("--status", default=None)
    proposal_create = proposal_sub.add_parser("create")
    proposal_create.add_argument("--scenario-id", required=True)
    proposal_create.add_argument("--agent-id", required=True)
    proposal_create.add_argument("--slot", required=True)
    proposal_create.add_argument("--operation", required=True)
    proposal_create.add_argument("--before", required=True)
    proposal_create.add_argument("--after", required=True)
    proposal_create.add_argument("--reason", required=True)
    proposal_create.add_argument("--expected-metric", required=True)
    proposal_approve = proposal_sub.add_parser("approve")
    proposal_approve.add_argument("proposal_id")
    proposal_reject = proposal_sub.add_parser("reject")
    proposal_reject.add_argument("proposal_id")

    shadow = subparsers.add_parser("shadow")
    shadow_sub = shadow.add_subparsers(dest="shadow_command")
    shadow_run = shadow_sub.add_parser("run")
    shadow_run.add_argument("proposal_id")
    shadow_run.add_argument("--task", required=True)
    shadow_run.add_argument("--context-json", default="{}")
    shadow_status = shadow_sub.add_parser("status")
    shadow_status.add_argument("proposal_id")

    report = subparsers.add_parser("report")
    report_sub = report.add_subparsers(dest="report_command")
    report_sub.add_parser("latest")
    report_run = report_sub.add_parser("run")
    report_run.add_argument("run_id")
    report_proposal = report_sub.add_parser("proposal")
    report_proposal.add_argument("proposal_id")


def handle_v2_command(args: argparse.Namespace, db_path: str | Path) -> int:
    """Handle V2 command groups."""

    if args.command == "scenario":
        return _handle_scenario(args, db_path)
    if args.command == "adapter":
        return _handle_adapter(args, db_path)
    if args.command == "prompt":
        return _handle_prompt(args, db_path)
    if args.command == "proposal":
        return _handle_proposal(args, db_path)
    if args.command == "shadow":
        return _handle_shadow(args, db_path)
    if args.command == "report":
        return _handle_report(args, db_path)
    return 1


def _handle_scenario(args: argparse.Namespace, db_path: str | Path) -> int:
    store = ScenarioStore(db_path)
    if args.scenario_command == "create":
        new_scenario = Scenario(
            id=args.id,
            name=args.name,
            description=args.description,
            adapter_type=args.adapter,
            adapter_config=_loads_json(args.adapter_config_json),
        )
        store.save(new_scenario)
        print(f"Scenario created: {new_scenario.id}")
        print(f"name: {new_scenario.name}")
        print(f"adapter: {new_scenario.adapter_type}")
        return 0
    if args.scenario_command == "list":
        scenarios = store.list()
        if not scenarios:
            print("No scenarios")
            return 0
        print("Scenarios")
        for scenario in scenarios:
            print(f"{scenario.id}\t{scenario.adapter_type}\t{scenario.name}")
        return 0
    if args.scenario_command == "show":
        found_scenario = store.get(args.scenario_id)
        if found_scenario is None:
            print(f"Scenario not found: {args.scenario_id}")
            return 1
        print("Scenario Detail")
        print(f"id: {found_scenario.id}")
        print(f"name: {found_scenario.name}")
        print(f"description: {found_scenario.description}")
        print(f"adapter: {found_scenario.adapter_type}")
        print(f"adapter_config: {_pretty(found_scenario.adapter_config)}")
        return 0
    return 1


def _handle_adapter(args: argparse.Namespace, db_path: str | Path) -> int:
    runner = _scenario_runner(db_path)
    result = runner.run_scenario(
        scenario_id=args.scenario_id,
        task=args.task,
        context=_loads_json(args.context_json),
        config=_loads_json(args.config_json),
    )
    print("Adapter Run Report")
    print(f"scenario_id: {result.scenario_id}")
    print(f"run_id: {result.run_id}")
    print(f"任务类型: {result.task}")
    print(f"status: {result.status}")
    print(f"metrics: {_pretty(result.metrics)}")
    print(f"value_summary: {result.value_summary}")
    print(f"answer: {result.answer}")
    return 0


def _handle_prompt(args: argparse.Namespace, db_path: str | Path) -> int:
    versions = PromptVersionStore(db_path)
    if args.prompt_command == "history":
        history = versions.history(args.scenario_id, args.agent_id)
        print("Prompt History")
        if not history:
            print("No prompt versions")
            return 0
        for version in history:
            print(f"{version.id}\t{version.created_at.isoformat()}\t{version.reason}")
            print(f"slots: {_pretty({slot.value: value for slot, value in version.slots.items()})}")
        return 0
    if args.prompt_command == "rollback":
        version = versions.rollback(args.scenario_id, args.agent_id, args.reason)
        print(f"Rolled back: {version.id}")
        print(f"reason: {version.reason}")
        return 0
    return 1


def _handle_proposal(args: argparse.Namespace, db_path: str | Path) -> int:
    proposals = PromptProposalStore(db_path)
    if args.proposal_command == "create":
        proposal = PromptProposal(
            scenario_id=args.scenario_id,
            agent_id=args.agent_id,
            patch=PromptPatch(
                slot=PromptSlot(args.slot),
                operation=args.operation,
                before=args.before,
                after=args.after,
            ),
            reason=args.reason,
            expected_metric=args.expected_metric,
        )
        proposals.create(proposal)
        print(f"Proposal created: {proposal.id}")
        return 0
    if args.proposal_command == "list":
        status = PromptProposalStatus(args.status) if args.status else None
        items = proposals.list(status=status)
        print("Proposals")
        if not items:
            print("No proposals")
            return 0
        for proposal in items:
            print(
                f"{proposal.id}\t{proposal.status.value}\t{proposal.scenario_id}\t"
                f"{proposal.patch.slot.value}\t{proposal.reason}"
            )
        return 0
    if args.proposal_command == "approve":
        proposals.update_status(args.proposal_id, PromptProposalStatus.APPROVED)
        print(f"Proposal {args.proposal_id} approved")
        return 0
    if args.proposal_command == "reject":
        proposals.update_status(args.proposal_id, PromptProposalStatus.REJECTED)
        print(f"Proposal {args.proposal_id} rejected")
        return 0
    return 1


def _handle_shadow(args: argparse.Namespace, db_path: str | Path) -> int:
    proposals = PromptProposalStore(db_path)
    results = ShadowResultStore(db_path)
    if args.shadow_command == "run":
        proposal = proposals.get(args.proposal_id)
        if proposal is None:
            print(f"Proposal not found: {args.proposal_id}")
            return 1
        runner = ShadowRunner(
            scenarios=_scenario_registry(db_path),
            adapters=_adapter_registry(),
            versions=PromptVersionStore(db_path),
            results=results,
            task=args.task,
            context=_loads_json(args.context_json),
        )
        result = runner.run(proposal)
        print("Shadow Result")
        print(f"id: {result.id}")
        print(f"proposal_id: {result.proposal_id}")
        print(f"status: {result.status}")
        print(f"passed: {result.passed}")
        print(f"value_summary: {result.value_summary}")
        print(f"metric_diff: {_pretty(result.metric_diff)}")
        return 0
    if args.shadow_command == "status":
        shadows = results.query_by_proposal(args.proposal_id)
        print("Shadow Status")
        if not shadows:
            print("No shadow results")
            return 0
        for result in shadows:
            print(f"{result.id}\t{result.status}\tpassed={result.passed}")
            print(f"metric_diff: {_pretty(result.metric_diff)}")
        return 0
    return 1


def _handle_report(args: argparse.Namespace, db_path: str | Path) -> int:
    reporter = ReportGenerator(db_path)
    if args.report_command == "latest":
        print(reporter.latest())
        return 0
    if args.report_command == "run":
        print(reporter.run(args.run_id))
        return 0
    if args.report_command == "proposal":
        print(reporter.proposal(args.proposal_id))
        return 0
    return 1


def _scenario_runner(db_path: str | Path) -> ScenarioRunner:
    return ScenarioRunner(
        scenarios=_scenario_registry(db_path),
        adapters=_adapter_registry(),
        raw_logs=RawLogStore(db_path),
        summary_logs=SummaryLogStore(db_path),
    )


def _scenario_registry(db_path: str | Path) -> ScenarioRegistry:
    registry = ScenarioRegistry()
    for scenario in ScenarioStore(db_path).list():
        registry.create(scenario)
    return registry


def _adapter_registry() -> AdapterRegistry:
    registry = AdapterRegistry()
    registry.register(DummyAdapter())
    registry.register(OPCAgentAdapter())
    registry.register(QuantResearchDemoAdapter())
    return registry


def _loads_json(raw: str) -> dict[str, Any]:
    loaded = json.loads(raw)
    if not isinstance(loaded, dict):
        raise ValueError("Expected a JSON object")
    return loaded


def _pretty(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)
