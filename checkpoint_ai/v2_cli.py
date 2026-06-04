"""V2 CLI commands for scenarios, adapters, prompts, proposals, shadows, and reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from checkpoint_ai.adapter import (
    AdapterCompatibilityEvaluator,
    AdapterCompatibilityInput,
    AdapterCompatibilityReportStore,
    AdapterRegistry,
    DummyAdapter,
    OPCAgentAdapter,
    QuantResearchDemoAdapter,
)
from checkpoint_ai.console import ApprovalInbox, BackupManager, ConsoleReadModel, CostEventStore
from checkpoint_ai.insights import (
    CrossScenarioInsightGenerator,
    CrossScenarioInsightStore,
    ScenarioInsightInput,
)
from checkpoint_ai.isolation import ScenarioIsolationAuditor
from checkpoint_ai.logs import RawLogStore, SummaryLogStore
from checkpoint_ai.metrics import (
    MetricCategory,
    MetricDirection,
    MetricSchema,
    MetricSchemaRegistry,
    MetricSchemaStore,
)
from checkpoint_ai.optimization import (
    OptimizationDirection,
    ParameterBounds,
    ParameterObservation,
    ParameterSuggestionStatus,
    ParameterSuggestionStore,
    SimpleBayesianOptimizer,
)
from checkpoint_ai.prompt import (
    PromptPatch,
    PromptProposal,
    PromptProposalStatus,
    PromptProposalStore,
    PromptSlot,
    PromptVersionStore,
)
from checkpoint_ai.recommendation import (
    RecommendationStatus,
    VersionRecommendationStore,
    VersionRecommender,
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
    scenario_create.add_argument("--business-line-id", default=None)
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
    adapter_compat = adapter_sub.add_parser("compatibility")
    adapter_compat.add_argument("--name", required=True)
    adapter_compat.add_argument("--structured-input", required=True)
    adapter_compat.add_argument("--structured-output", required=True)
    adapter_compat.add_argument("--prompt-slots", required=True)
    adapter_compat.add_argument("--prompt-injection", required=True)
    adapter_compat.add_argument("--shadow-run", required=True)
    adapter_compat.add_argument("--run-trace", required=True)
    adapter_compat.add_argument("--metrics-capture", required=True)
    adapter_compat.add_argument("--metric-format-compatible", required=True)
    adapter_compat.add_argument("--estimated-days", type=int, required=True)

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
    report_recommendation = report_sub.add_parser("recommendation")
    report_recommendation.add_argument("recommendation_id")
    report_insight = report_sub.add_parser("insight")
    report_insight.add_argument("insight_id")

    metric_schema = subparsers.add_parser("metric-schema")
    metric_schema_sub = metric_schema.add_subparsers(dest="metric_schema_command")
    metric_schema_set = metric_schema_sub.add_parser("set")
    metric_schema_set.add_argument("--scenario-id", required=True)
    metric_schema_set.add_argument("--name", required=True)
    metric_schema_set.add_argument("--direction", required=True)
    metric_schema_set.add_argument("--category", default=MetricCategory.BUSINESS.value)
    metric_schema_set.add_argument("--weight", type=float, default=1.0)
    metric_schema_set.add_argument("--threshold", type=float, default=None)
    metric_schema_set.add_argument("--guardrail", action="store_true")
    metric_schema_list = metric_schema_sub.add_parser("list")
    metric_schema_list.add_argument("--scenario-id", required=True)
    metric_schema_delete = metric_schema_sub.add_parser("delete")
    metric_schema_delete.add_argument("--scenario-id", required=True)
    metric_schema_delete.add_argument("--name", default=None)
    metric_schema_default = metric_schema_sub.add_parser("load-default-quant")
    metric_schema_default.add_argument("--scenario-id", required=True)

    recommendation = subparsers.add_parser("recommendation")
    recommendation_sub = recommendation.add_subparsers(dest="recommendation_command")
    recommendation_run = recommendation_sub.add_parser("run")
    recommendation_run.add_argument("--scenario-id", required=True)
    recommendation_list = recommendation_sub.add_parser("list")
    recommendation_list.add_argument("--scenario-id", default=None)
    recommendation_show = recommendation_sub.add_parser("show")
    recommendation_show.add_argument("recommendation_id")
    recommendation_accept = recommendation_sub.add_parser("accept")
    recommendation_accept.add_argument("recommendation_id")
    recommendation_reject = recommendation_sub.add_parser("reject")
    recommendation_reject.add_argument("recommendation_id")

    optimization = subparsers.add_parser("optimization")
    optimization_sub = optimization.add_subparsers(dest="optimization_command")
    optimization_suggest = optimization_sub.add_parser("suggest")
    optimization_suggest.add_argument("--scenario-id", required=True)
    optimization_suggest.add_argument("--target-id", required=True)
    optimization_suggest.add_argument("--parameter-name", required=True)
    optimization_suggest.add_argument("--min", type=float, required=True)
    optimization_suggest.add_argument("--max", type=float, required=True)
    optimization_suggest.add_argument("--step", type=float, default=None)
    optimization_suggest.add_argument("--direction", default=OptimizationDirection.MAXIMIZE.value)
    optimization_suggest.add_argument("--observations-json", default="[]")
    optimization_list = optimization_sub.add_parser("list")
    optimization_list.add_argument("--scenario-id", default=None)
    optimization_accept = optimization_sub.add_parser("accept")
    optimization_accept.add_argument("suggestion_id")
    optimization_reject = optimization_sub.add_parser("reject")
    optimization_reject.add_argument("suggestion_id")

    isolation = subparsers.add_parser("isolation")
    isolation_sub = isolation.add_subparsers(dest="isolation_command")
    isolation_sub.add_parser("audit")

    insight = subparsers.add_parser("insight")
    insight_sub = insight.add_subparsers(dest="insight_command")
    insight_compare = insight_sub.add_parser("compare")
    insight_compare.add_argument("--source", required=True)
    insight_compare.add_argument("--target", required=True)
    insight_compare.add_argument("--source-tags", required=True)
    insight_compare.add_argument("--target-tags", required=True)
    insight_compare.add_argument("--source-metrics", required=True)
    insight_compare.add_argument("--target-metrics", required=True)
    insight_compare.add_argument("--source-runs", type=int, required=True)
    insight_compare.add_argument("--target-runs", type=int, required=True)
    insight_compare.add_argument("--source-non-synthetic-recommendations", type=int, required=True)
    insight_compare.add_argument("--target-non-synthetic-recommendations", type=int, required=True)
    insight_sub.add_parser("list")

    console = subparsers.add_parser("console")
    console_sub = console.add_subparsers(dest="console_command")
    console_snapshot = console_sub.add_parser("snapshot")
    console_snapshot.add_argument("--scenario-id", default=None)
    console_snapshot.add_argument("--all-scenarios", action="store_true")
    console_snapshot.add_argument("--reason", default=None)
    console_approvals = console_sub.add_parser("approvals")
    console_approvals.add_argument("--scenario-id", default=None)
    console_cost = console_sub.add_parser("cost")
    console_cost.add_argument("--provider", required=True)
    console_cost.add_argument("--business-line-id", required=True)
    console_backup = console_sub.add_parser("backup")
    console_backup_sub = console_backup.add_subparsers(dest="backup_command")
    console_backup_create = console_backup_sub.add_parser("create")
    console_backup_create.add_argument("--backup-dir", required=True)
    console_backup_create.add_argument("--label", required=True)
    console_backup_list = console_backup_sub.add_parser("list")
    console_backup_list.add_argument("--backup-dir", required=True)
    console_backup_restore = console_backup_sub.add_parser("restore")
    console_backup_restore.add_argument("--backup-dir", required=True)
    console_backup_restore.add_argument("backup_id")


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
    if args.command == "metric-schema":
        return _handle_metric_schema(args, db_path)
    if args.command == "recommendation":
        return _handle_recommendation(args, db_path)
    if args.command == "optimization":
        return _handle_optimization(args, db_path)
    if args.command == "isolation":
        return _handle_isolation(args, db_path)
    if args.command == "insight":
        return _handle_insight(args, db_path)
    if args.command == "console":
        return _handle_console(args, db_path)
    return 1


def _handle_scenario(args: argparse.Namespace, db_path: str | Path) -> int:
    store = ScenarioStore(db_path)
    if args.scenario_command == "create":
        new_scenario = Scenario(
            id=args.id,
            name=args.name,
            description=args.description,
            adapter_type=args.adapter,
            business_line_id=args.business_line_id,
            adapter_config=_loads_json(args.adapter_config_json),
        )
        store.save(new_scenario)
        print(f"Scenario created: {new_scenario.id}")
        print(f"name: {new_scenario.name}")
        print(f"business_line_id: {new_scenario.business_line_id or 'default'}")
        print(f"adapter: {new_scenario.adapter_type}")
        return 0
    if args.scenario_command == "list":
        scenarios = store.list()
        if not scenarios:
            print("No scenarios")
            return 0
        print("Scenarios")
        for scenario in scenarios:
            print(
                f"{scenario.id}\t{scenario.business_line_id or 'default'}\t"
                f"{scenario.adapter_type}\t{scenario.name}"
            )
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
        print(f"business_line_id: {found_scenario.business_line_id or 'default'}")
        print(f"adapter: {found_scenario.adapter_type}")
        print(f"adapter_config: {_pretty(found_scenario.adapter_config)}")
        return 0
    return 1


def _handle_adapter(args: argparse.Namespace, db_path: str | Path) -> int:
    if args.adapter_command == "compatibility":
        report = AdapterCompatibilityEvaluator().evaluate(
            AdapterCompatibilityInput(
                name=args.name,
                structured_input=_bool_arg(args.structured_input),
                structured_output=_bool_arg(args.structured_output),
                prompt_slots=_bool_arg(args.prompt_slots),
                prompt_injection=_bool_arg(args.prompt_injection),
                shadow_run=_bool_arg(args.shadow_run),
                run_trace=_bool_arg(args.run_trace),
                metrics_capture=_bool_arg(args.metrics_capture),
                metric_format_compatible=_bool_arg(args.metric_format_compatible),
                estimated_days=args.estimated_days,
            )
        )
        AdapterCompatibilityReportStore(db_path).save(report)
        print("Adapter Compatibility Report")
        print(f"id: {report.id}")
        print(f"name: {report.name}")
        print(f"score: {report.score}")
        print(f"decision: {report.decision.value}")
        print(f"blockers: {report.blockers}")
        print(f"warnings: {report.warnings}")
        return 0
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
    if args.report_command == "recommendation":
        print(reporter.recommendation(args.recommendation_id))
        return 0
    if args.report_command == "insight":
        print(reporter.insight(args.insight_id))
        return 0
    return 1


def _handle_metric_schema(args: argparse.Namespace, db_path: str | Path) -> int:
    store = MetricSchemaStore(db_path)
    if args.metric_schema_command == "set":
        existing = {
            schema.name: schema
            for schema in store.list_for_scenario(args.scenario_id)
        }
        existing[args.name] = MetricSchema(
            name=args.name,
            direction=MetricDirection(args.direction),
            category=MetricCategory(args.category),
            weight=args.weight,
            threshold=args.threshold,
            is_guardrail=args.guardrail,
        )
        store.save_for_scenario(args.scenario_id, list(existing.values()))
        print("Metric schema saved")
        print(f"scenario_id: {args.scenario_id}")
        print(f"name: {args.name}")
        print(f"direction: {args.direction}")
        print(f"category: {args.category}")
        print(f"weight: {args.weight}")
        return 0
    if args.metric_schema_command == "list":
        schemas = store.list_for_scenario(args.scenario_id)
        print("Metric Schemas")
        if not schemas:
            print("No metric schemas")
            return 0
        for schema in schemas:
            print(
                f"{schema.name}\t{schema.direction.value}\t{schema.category.value}\t"
                f"weight={schema.weight}\tthreshold={schema.threshold}\tguardrail={schema.is_guardrail}"
            )
        return 0
    if args.metric_schema_command == "delete":
        count = store.delete_for_scenario(args.scenario_id, args.name)
        print(f"Deleted metric schemas: {count}")
        return 0
    if args.metric_schema_command == "load-default-quant":
        store.save_for_scenario(args.scenario_id, MetricSchemaRegistry.default_quant().list())
        print(f"Default quant metric schemas loaded: {args.scenario_id}")
        return 0
    return 1


def _handle_recommendation(args: argparse.Namespace, db_path: str | Path) -> int:
    store = VersionRecommendationStore(db_path)
    if args.recommendation_command == "run":
        recommendation = VersionRecommender(
            shadow_results=ShadowResultStore(db_path),
            recommendations=store,
        ).recommend_for_scenario(args.scenario_id)
        print(f"Recommendation created: {recommendation.id}")
        print(f"decision: {recommendation.decision.value}")
        print(f"confidence: {recommendation.confidence}")
        print(f"reason: {recommendation.reason}")
        return 0
    if args.recommendation_command == "list":
        recommendations = store.list(scenario_id=args.scenario_id)
        print("Recommendations")
        if not recommendations:
            print("No recommendations")
            return 0
        for recommendation in recommendations:
            print(
                f"{recommendation.id}\t{recommendation.scenario_id}\t"
                f"{recommendation.decision.value}\t{recommendation.status.value}\t"
                f"confidence={recommendation.confidence}"
            )
        return 0
    if args.recommendation_command == "show":
        print(ReportGenerator(db_path).recommendation(args.recommendation_id))
        return 0
    if args.recommendation_command == "accept":
        store.update_status(args.recommendation_id, RecommendationStatus.ACCEPTED)
        print(f"Recommendation {args.recommendation_id} accepted")
        return 0
    if args.recommendation_command == "reject":
        store.update_status(args.recommendation_id, RecommendationStatus.REJECTED)
        print(f"Recommendation {args.recommendation_id} rejected")
        return 0
    return 1


def _handle_optimization(args: argparse.Namespace, db_path: str | Path) -> int:
    store = ParameterSuggestionStore(db_path)
    if args.optimization_command == "suggest":
        observations = _parameter_observations(args.parameter_name, args.observations_json)
        suggestion = SimpleBayesianOptimizer().suggest(
            scenario_id=args.scenario_id,
            target_id=args.target_id,
            bounds=ParameterBounds(
                parameter_name=args.parameter_name,
                minimum=args.min,
                maximum=args.max,
                step=args.step,
            ),
            observations=observations,
            direction=OptimizationDirection(args.direction),
        )
        store.save(suggestion)
        print(f"Parameter suggestion created: {suggestion.id}")
        print(f"scenario_id: {suggestion.scenario_id}")
        print(f"target_id: {suggestion.target_id}")
        print(f"parameter_name: {suggestion.parameter_name}")
        print(f"suggested_value: {suggestion.suggested_value}")
        print(f"expected_score: {suggestion.expected_score}")
        print(f"confidence: {suggestion.confidence}")
        print(f"reason: {suggestion.reason}")
        return 0
    if args.optimization_command == "list":
        suggestions = store.list(scenario_id=args.scenario_id)
        print("Parameter Suggestions")
        if not suggestions:
            print("No parameter suggestions")
            return 0
        for suggestion in suggestions:
            print(
                f"{suggestion.id}\t{suggestion.scenario_id}\t{suggestion.target_id}\t"
                f"{suggestion.parameter_name}={suggestion.suggested_value}\t"
                f"confidence={suggestion.confidence}\t{suggestion.status.value}"
            )
        return 0
    if args.optimization_command == "accept":
        store.update_status(args.suggestion_id, ParameterSuggestionStatus.ACCEPTED)
        print(f"Parameter suggestion {args.suggestion_id} accepted")
        return 0
    if args.optimization_command == "reject":
        store.update_status(args.suggestion_id, ParameterSuggestionStatus.REJECTED)
        print(f"Parameter suggestion {args.suggestion_id} rejected")
        return 0
    return 1


def _handle_isolation(args: argparse.Namespace, db_path: str | Path) -> int:
    if args.isolation_command == "audit":
        print("Scenario Isolation Audit")
        for result in ScenarioIsolationAuditor().audit_sqlite(db_path):
            scenarios = ",".join(result.scenario_ids) if result.scenario_ids else "-"
            print(
                f"{result.store_name}\t{result.status}\t"
                f"scenarios={scenarios}\tmissing={result.missing_scenario_id_count}"
            )
        return 0
    return 1


def _handle_insight(args: argparse.Namespace, db_path: str | Path) -> int:
    store = CrossScenarioInsightStore(db_path)
    if args.insight_command == "compare":
        insight = CrossScenarioInsightGenerator().compare(
            ScenarioInsightInput(
                scenario_id=args.source,
                domain_tags=_csv(args.source_tags),
                metric_names=_csv(args.source_metrics),
                run_count=args.source_runs,
                non_synthetic_recommendation_count=args.source_non_synthetic_recommendations,
            ),
            ScenarioInsightInput(
                scenario_id=args.target,
                domain_tags=_csv(args.target_tags),
                metric_names=_csv(args.target_metrics),
                run_count=args.target_runs,
                non_synthetic_recommendation_count=args.target_non_synthetic_recommendations,
            ),
        )
        store.save(insight)
        print(f"Cross-scenario insight created: {insight.id}")
        print(f"decision: {insight.decision.value}")
        print(f"source: {insight.source_scenario_id}")
        print(f"target: {insight.target_scenario_id}")
        print(f"reason: {insight.reason}")
        return 0
    if args.insight_command == "list":
        print("Cross-Scenario Insights")
        for insight in store.list():
            print(
                f"{insight.id}\t{insight.decision.value}\t"
                f"{insight.source_scenario_id}->{insight.target_scenario_id}\t"
                f"similarity={insight.similarity_score}"
            )
        return 0
    return 1


def _handle_console(args: argparse.Namespace, db_path: str | Path) -> int:
    if args.console_command == "snapshot":
        snapshot = ConsoleReadModel(db_path).snapshot(
            scenario_id=args.scenario_id,
            allow_cross_scenario=args.all_scenarios,
            reason=args.reason,
        )
        print("Console Snapshot")
        print(f"scope: {snapshot.scope.scenario_id or 'all'}")
        print(f"scenario_count: {snapshot.scenario_count}")
        print(f"active_scenario_count: {snapshot.active_scenario_count}")
        print(f"archived_scenario_count: {snapshot.archived_scenario_count}")
        print(f"recent_run_count: {snapshot.recent_run_count}")
        print(f"failed_run_count: {snapshot.failed_run_count}")
        print(f"pending_approval_count: {snapshot.pending_approval_count}")
        print(f"operator_summary: {snapshot.operator_summary}")
        if snapshot.latest_runs:
            print("latest_runs:")
            for run in snapshot.latest_runs:
                print(f"- {run.run_id}\t{run.scenario_id}\t{run.status}\t{run.task}\t{run.value_summary}")
        if snapshot.pending_items:
            print("pending_items:")
            for item in snapshot.pending_items:
                print(f"- {item['source_id']}\t{item['item_type']}\t{item['summary']}")
        return 0
    if args.console_command == "approvals":
        print("Approval Inbox")
        items = ApprovalInbox(db_path).list_items(scenario_id=args.scenario_id)
        if not items:
            print("No approval items")
            return 0
        for approval_item in items:
            print(
                f"{approval_item.source_id}\t{approval_item.scenario_id}\t"
                f"{approval_item.item_type}\t{approval_item.summary}"
            )
        return 0
    if args.console_command == "cost":
        summary = CostEventStore(db_path).daily_summary(
            provider=args.provider,
            business_line_id=args.business_line_id,
        )
        print("Cost Summary")
        print(f"provider: {summary.provider}")
        print(f"business_line_id: {summary.business_line_id}")
        print(f"input_tokens: {summary.input_tokens}")
        print(f"output_tokens: {summary.output_tokens}")
        print(f"total_tokens: {summary.total_tokens}")
        print(f"estimated_cost: {summary.estimated_cost}")
        return 0
    if args.console_command == "backup":
        manager = BackupManager(db_path, args.backup_dir)
        if args.backup_command == "create":
            backup = manager.create_backup(label=args.label)
            print("Backup created")
            print(f"id: {backup.id}")
            print(f"label: {backup.label}")
            print(f"path: {backup.path}")
            return 0
        if args.backup_command == "list":
            print("Backups")
            backups = manager.list_backups()
            if not backups:
                print("No backups")
                return 0
            for backup in backups:
                print(f"{backup.id}\t{backup.label}\t{backup.path}")
            return 0
        if args.backup_command == "restore":
            restored = manager.restore(args.backup_id)
            print(f"Backup restored: {restored}")
            return 0 if restored else 1
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


def _bool_arg(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "y"}


def _csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def _parameter_observations(parameter_name: str, raw: str) -> list[ParameterObservation]:
    loaded = json.loads(raw)
    if not isinstance(loaded, list):
        raise ValueError("Expected observations JSON array")
    observations: list[ParameterObservation] = []
    for item in loaded:
        if not isinstance(item, dict):
            raise ValueError("Each observation must be an object")
        observations.append(
            ParameterObservation(
                parameter_name=parameter_name,
                value=float(item["value"]),
                score=float(item["score"]),
                run_id=str(item["run_id"]) if "run_id" in item else None,
                evidence_id=str(item["evidence_id"]) if "evidence_id" in item else None,
            )
        )
    return observations


def _pretty(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)
