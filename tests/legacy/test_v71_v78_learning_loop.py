"""V7 learning loop acceptance tests."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from loop_harness.adapter import AgentRunResult
from loop_harness.agent_config import (
    AgentConfig,
    AgentConfigStore,
    AgentRole,
    AgentRuntimeContextBuilder,
)
from loop_harness.api import create_app
from loop_harness.config_version import ConfigBranchStore, ConfigVersionService, ConfigVersionStore
from loop_harness.decision import DecisionKind, DecisionLogStore, DecisionRecord
from loop_harness.external_agents import (
    DummyExternalAgentAdapter,
    ExternalAgentConnection,
    ExternalAgentConnectionStore,
)
from loop_harness.learning import (
    ConflictDetector,
    DecisionObserver,
    LearningLoopService,
    MetricObserver,
    Observation,
    ObservationAggregator,
    ObservationSeverity,
    ObservationStore,
    ObservationType,
    ParameterProposer,
    PromptProposer,
    ProposalCandidate,
    ProposalRanker,
    SafetyFindingStore,
    SafetyMonitor,
    ShadowReplayScheduler,
    ShadowReplayStatus,
    ValidationSummaryStore,
    Validator,
)
from loop_harness.logs import SummaryLogStore
from loop_harness.shadow.comparison import MetricComparator, RunKind
from loop_harness.user_profile import UserProfileStore


def _db(tmp: str) -> Path:
    return Path(tmp) / "loopharness.db"


def test_v71_blackboard_stores_require_scope_and_persist() -> None:
    """V7.1 stores persist scoped blackboard objects."""

    with TemporaryDirectory() as tmp:
        db = _db(tmp)
        observation = Observation(
            business_line_id="bl-1",
            scenario_id="scenario-1",
            observation_type=ObservationType.METRIC_ANOMALY,
            severity=ObservationSeverity.WARNING,
            title="Sharpe drift",
            summary="sharpe dropped below baseline",
            source_ids=["run-1"],
            metadata={"metric": "sharpe"},
        )
        observation_id = ObservationStore(db).save(observation)

        saved = ObservationStore(db).get(observation_id)
        assert saved is not None
        assert saved.business_line_id == "bl-1"
        assert saved.scenario_id == "scenario-1"
        assert ObservationStore(db).list(scenario_id="other") == []

        safety_id = SafetyFindingStore(db).save(
            scenario_id="scenario-1",
            business_line_id="bl-1",
            proposal_id="proposal-1",
            severity="blocked",
            reason="cooldown active",
            source_ids=["obs-1"],
        )
        assert SafetyFindingStore(db).get(safety_id) is not None

        validation_id = ValidationSummaryStore(db).save(
            scenario_id="scenario-1",
            business_line_id="bl-1",
            proposal_id="proposal-1",
            shadow_result_id="shadow-1",
            improved=True,
            summary="shadow improved sharpe",
            metric_diffs={"sharpe": 0.2},
            recommendation="send_to_approval",
            source_ids=["shadow-1"],
        )
        assert ValidationSummaryStore(db).get(validation_id) is not None


def test_v72_observer_hive_finds_metric_and_decision_observations() -> None:
    """V7.2 observers produce structured observations and aggregator filters noise."""

    with TemporaryDirectory() as tmp:
        db = _db(tmp)
        summaries = SummaryLogStore(db)
        summaries.save(
            AgentRunResult(
                scenario_id="scenario-1",
                run_id="run-1",
                task="research",
                answer="ok",
                metrics={"sharpe": 0.1, "latency_ms": 10},
                value_summary="low sharpe",
                status="success",
            )
        )
        decisions = DecisionLogStore(db)
        decisions.record(
            DecisionRecord(
                source_id="proposal-1",
                source_type="proposal",
                kind=DecisionKind.REJECT,
                scenario_id="scenario-1",
                action="reject",
                comment="expected metric unclear",
            )
        )

        metric_observations = MetricObserver(summaries, {"sharpe": 0.5}).observe("scenario-1")
        decision_observations = DecisionObserver(decisions).observe("scenario-1")
        aggregated = ObservationAggregator(max_items=2).aggregate(metric_observations + decision_observations)

        assert len(aggregated) == 2
        assert {item.observation_type for item in aggregated} == {
            ObservationType.METRIC_ANOMALY,
            ObservationType.DECISION_PATTERN,
        }


def test_v73_proposer_hive_ranks_small_non_conflicting_patches() -> None:
    """V7.3 proposers generate patch-first proposals and ranking removes conflicts."""

    observation = Observation(
        business_line_id="bl-1",
        scenario_id="scenario-1",
        observation_type=ObservationType.METRIC_ANOMALY,
        severity=ObservationSeverity.WARNING,
        title="Sharpe drift",
        summary="sharpe below target",
        source_ids=["run-1"],
        metadata={"metric": "sharpe", "target_id": "strategy.fast_window"},
    )
    candidates = PromptProposer().propose(observation) + ParameterProposer().propose(observation)

    assert candidates
    assert all(candidate.proposal.patch.operation == "replace" for candidate in candidates)
    assert all(candidate.proposal.patch.before != candidate.proposal.patch.after for candidate in candidates)

    ranked = ProposalRanker().rank(candidates)
    non_conflicting = ConflictDetector().filter_conflicts(ranked)

    assert non_conflicting[0].score >= non_conflicting[-1].score
    targets = [candidate.proposal.target_id for candidate in non_conflicting]
    assert len(targets) == len(set(targets))


def test_v74_shadow_replay_scheduler_and_validator_do_not_apply() -> None:
    """V7.4 schedules replay, validates comparison, and never applies changes."""

    candidate = ProposalCandidate.for_parameter(
        scenario_id="scenario-1",
        business_line_id="bl-1",
        target_id="strategy.fast_window",
        before=8,
        after=10,
        reason="sharpe improved in recent observations",
        expected_metric="sharpe",
        source_ids=["obs-1"],
    )
    scheduler = ShadowReplayScheduler()
    job = scheduler.schedule(candidate)
    assert job.status == ShadowReplayStatus.PENDING
    assert not job.apply_requested

    comparison = MetricComparator().compare(
        {"sharpe": 0.8, "max_drawdown": 0.1},
        {"sharpe": 0.95, "max_drawdown": 0.09},
        run_kind=RunKind.HISTORICAL,
    )
    summary = Validator().validate(
        candidate=candidate,
        shadow_result_id="shadow-1",
        comparison=comparison,
    )

    assert summary.improved is True
    assert summary.recommendation == "send_to_approval"
    assert "sharpe" in summary.metric_diffs


def test_v75_safety_monitor_blocks_cooldown_budget_and_regression() -> None:
    """V7.5 safety monitor creates explainable findings for unsafe proposals."""

    candidate = ProposalCandidate.for_parameter(
        scenario_id="scenario-1",
        business_line_id="bl-1",
        target_id="strategy.fast_window",
        before=8,
        after=20,
        reason="large move",
        expected_metric="sharpe",
        source_ids=["obs-1"],
    )
    monitor = SafetyMonitor(
        blocked_targets={"strategy.fast_window"},
        cooldown_targets={"strategy.fast_window"},
        remaining_budget=0,
    )
    findings = monitor.evaluate(candidate)

    assert any(finding.severity == "blocked" for finding in findings)
    assert any("budget" in finding.reason for finding in findings)
    assert any("cooldown" in finding.reason for finding in findings)


def test_v76_config_version_lock_branch_switch_and_rollback() -> None:
    """V7.6 config versions can be locked, branched, switched, and rolled back."""

    with TemporaryDirectory() as tmp:
        db = _db(tmp)
        service = ConfigVersionService(ConfigVersionStore(db), ConfigBranchStore(db))
        version = service.save_version(
            scenario_id="scenario-1",
            business_line_id="bl-1",
            config={"temperature": 0.2},
            reason="baseline",
        )
        locked = service.lock_version(version.id, reason="works well")
        branch = service.create_branch(
            scenario_id="scenario-1",
            business_line_id="bl-1",
            name="explore-low-temp",
            base_version_id=locked.id,
        )

        assert locked.locked is True
        assert service.get_active_branch("scenario-1").id == branch.id
        assert service.rollback_to_locked("scenario-1", locked.id).config["temperature"] == 0.2


def test_v77_agent_config_external_adapter_and_user_profile_boundaries() -> None:
    """V7.7 keeps formal profile human-controlled and adapters configurable."""

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        db = root / "loopharness.db"
        profile_store = UserProfileStore(root / "user", db)
        profile_store.save_formal_profile("偏好：保守、可解释、不要自动实盘。", actor="human", reason="initial")
        profile_store.save_suggested_notes("Hermes建议：更偏好低回撤。", actor="hermes")

        context = AgentRuntimeContextBuilder(profile_store).build()
        assert "保守" in context.formal_user_profile
        assert "低回撤" not in context.formal_user_profile
        assert "低回撤" in context.suggested_notes

        config = AgentConfig(
            business_line_id="bl-1",
            role=AgentRole.OBSERVER,
            config_version_id="version-1",
            skills=["metric_scan"],
            tools=["sqlite"],
            mcp_servers=[],
            triggers=["new_run"],
            constraints=["no live apply"],
            model="minimax",
        )
        assert AgentConfigStore(db).save(config) == config.id
        assert AgentConfigStore(db).list(business_line_id="bl-1")[0].role == AgentRole.OBSERVER

        connection = ExternalAgentConnection(
            business_line_id="bl-1",
            scenario_id="scenario-1",
            name="demo",
            adapter_type="dummy_external",
            config={"latency_ms": 1},
        )
        ExternalAgentConnectionStore(db).save(connection)
        result = DummyExternalAgentAdapter().run_task({"task": "analyze"}, connection)
        assert result.metrics["quality_score"] > 0


def test_v78_learning_loop_service_generates_validated_candidate_without_apply() -> None:
    """V7.8 end-to-end service observes, proposes, schedules shadow, validates, and records."""

    with TemporaryDirectory() as tmp:
        db = _db(tmp)
        summaries = SummaryLogStore(db)
        summaries.save(
            AgentRunResult(
                scenario_id="scenario-1",
                run_id="run-1",
                task="research",
                answer="ok",
                metrics={"sharpe": 0.2, "max_drawdown": 0.12},
                value_summary="weak baseline",
                status="success",
            )
        )

        service = LearningLoopService(db_path=db, metric_thresholds={"sharpe": 0.5})
        result = service.run_once(
            scenario_id="scenario-1",
            business_line_id="bl-1",
            trigger_reason="new historical run",
        )

        assert result.observations_count >= 1
        assert result.proposals_count >= 1
        assert result.shadow_jobs_count >= 1
        assert result.validations_count >= 1
        assert result.applied_count == 0
        assert "new historical run" in result.summary


def test_v7_control_console_routes_are_exposed() -> None:
    """V7 control routes are available without making Hermes the only entry."""

    with TemporaryDirectory() as tmp:
        app = create_app(db_path=_db(tmp), force_fallback=True)
        paths = {route["path"] for route in app.routes}
        assert "/api/learning/observations" in paths
        assert "/api/config/versions" in paths
        assert "/api/agent-configs" in paths
        assert "/api/external-agents" in paths
        assert "/api/user-profile" in paths


class TestV7LearningLoop(unittest.TestCase):
    """Unittest wrapper for V7 acceptance functions."""

    def test_v71_blackboard_stores_require_scope_and_persist(self) -> None:
        test_v71_blackboard_stores_require_scope_and_persist()

    def test_v72_observer_hive_finds_metric_and_decision_observations(self) -> None:
        test_v72_observer_hive_finds_metric_and_decision_observations()

    def test_v73_proposer_hive_ranks_small_non_conflicting_patches(self) -> None:
        test_v73_proposer_hive_ranks_small_non_conflicting_patches()

    def test_v74_shadow_replay_scheduler_and_validator_do_not_apply(self) -> None:
        test_v74_shadow_replay_scheduler_and_validator_do_not_apply()

    def test_v75_safety_monitor_blocks_cooldown_budget_and_regression(self) -> None:
        test_v75_safety_monitor_blocks_cooldown_budget_and_regression()

    def test_v76_config_version_lock_branch_switch_and_rollback(self) -> None:
        test_v76_config_version_lock_branch_switch_and_rollback()

    def test_v77_agent_config_external_adapter_and_user_profile_boundaries(self) -> None:
        test_v77_agent_config_external_adapter_and_user_profile_boundaries()

    def test_v78_learning_loop_service_generates_validated_candidate_without_apply(self) -> None:
        test_v78_learning_loop_service_generates_validated_candidate_without_apply()

    def test_v7_control_console_routes_are_exposed(self) -> None:
        test_v7_control_console_routes_are_exposed()
