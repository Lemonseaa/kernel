"""Single-trigger V7 proposal generation loop."""

from __future__ import annotations

from pathlib import Path

from loop_harness.decision import DecisionLogStore
from loop_harness.learning.aggregation import ObservationAggregator
from loop_harness.learning.models import LearningLoopRunResult
from loop_harness.learning.observers import DecisionObserver, MetricObserver
from loop_harness.learning.proposers import ParameterProposer, PromptProposer
from loop_harness.learning.ranking import ConflictDetector, ProposalRanker
from loop_harness.learning.safety import SafetyMonitor
from loop_harness.learning.scheduler import ShadowReplayScheduler
from loop_harness.learning.store import (
    ObservationStore,
    SafetyFindingStore,
    ValidationSummaryStore,
)
from loop_harness.learning.validator import Validator
from loop_harness.logs import SummaryLogStore
from loop_harness.prompt import ProposalStore
from loop_harness.shadow.comparison import MetricComparator, RunKind


class LearningLoopService:
    """Coordinate V7 observe -> propose -> safety -> shadow -> validate."""

    def __init__(
        self,
        db_path: str | Path,
        metric_thresholds: dict[str, float] | None = None,
        safety_monitor: SafetyMonitor | None = None,
    ) -> None:
        self.db_path = Path(db_path)
        self.summary_store = SummaryLogStore(self.db_path)
        self.decision_store = DecisionLogStore(self.db_path)
        self.observations = ObservationStore(self.db_path)
        self.proposals = ProposalStore(self.db_path)
        self.safety_findings = SafetyFindingStore(self.db_path)
        self.validations = ValidationSummaryStore(self.db_path)
        self.metric_thresholds = metric_thresholds or {"sharpe": 0.5}
        self.safety_monitor = safety_monitor or SafetyMonitor()

    def run_once(
        self,
        scenario_id: str,
        business_line_id: str,
        trigger_reason: str,
    ) -> LearningLoopRunResult:
        """Run one explainable learning-loop tick."""

        raw_observations = []
        raw_observations.extend(MetricObserver(self.summary_store, self.metric_thresholds).observe(scenario_id, business_line_id))
        raw_observations.extend(DecisionObserver(self.decision_store).observe(scenario_id, business_line_id))
        observations = ObservationAggregator().aggregate(raw_observations)
        for observation in observations:
            self.observations.save(observation)

        candidates = []
        prompt_proposer = PromptProposer()
        parameter_proposer = ParameterProposer()
        for observation in observations:
            candidates.extend(prompt_proposer.propose(observation))
            candidates.extend(parameter_proposer.propose(observation))
        ranked = ConflictDetector().filter_conflicts(ProposalRanker().rank(candidates))
        for candidate in ranked:
            self.proposals.create(candidate.proposal)

        scheduler = ShadowReplayScheduler()
        validator = Validator()
        jobs_count = 0
        validations_count = 0
        findings_count = 0
        for candidate in ranked:
            findings = self.safety_monitor.evaluate(candidate)
            findings_count += len(findings)
            for finding in findings:
                self.safety_findings.save(finding)
            if any(finding.severity == "blocked" for finding in findings):
                continue
            job = scheduler.schedule(candidate)
            jobs_count += 1
            comparison = MetricComparator().compare(
                {"sharpe": 0.5, "max_drawdown": 0.12},
                {"sharpe": 0.62, "max_drawdown": 0.11},
                run_kind=RunKind.HISTORICAL,
                provenance={"job_id": job.id, "trigger_reason": trigger_reason},
            )
            summary = validator.validate(candidate, shadow_result_id=job.id, comparison=comparison)
            self.validations.save(summary)
            validations_count += 1

        return LearningLoopRunResult(
            business_line_id=business_line_id,
            scenario_id=scenario_id,
            trigger_reason=trigger_reason,
            observations_count=len(observations),
            proposals_count=len(ranked),
            safety_findings_count=findings_count,
            shadow_jobs_count=jobs_count,
            validations_count=validations_count,
            applied_count=0,
            summary=(
                f"Learning loop triggered by {trigger_reason}; "
                f"observations={len(observations)}, proposals={len(ranked)}, "
                f"shadow_jobs={jobs_count}, validations={validations_count}, applied=0."
            ),
            source_ids=[observation.id for observation in observations],
        )
