"""V7 blackboard and learning-loop contracts."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

from loop_harness.metrics import ComparisonResult
from loop_harness.prompt import Proposal, ProposalKind, ProposalPatch, ProposalTargetType


class ObservationType(str, Enum):
    """Kinds of facts the observer hive can place on the blackboard."""

    METRIC_ANOMALY = "metric_anomaly"
    DECISION_PATTERN = "decision_pattern"
    COST_PRESSURE = "cost_pressure"
    DATA_QUALITY = "data_quality"
    OPPORTUNITY = "opportunity"


class ObservationSeverity(str, Enum):
    """Observation priority."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Observation(BaseModel):
    """Structured fact discovered by an observer."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    business_line_id: str
    scenario_id: str
    observation_type: ObservationType
    severity: ObservationSeverity = ObservationSeverity.INFO
    title: str
    summary: str
    source_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("business_line_id", "scenario_id", "title", "summary")
    @classmethod
    def required_text(cls, value: str) -> str:
        """Reject unscoped or empty observations."""

        if not value.strip():
            raise ValueError("observation scope and summary fields are required")
        return value


class SafetyFinding(BaseModel):
    """Safety finding generated before validation or execution."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    business_line_id: str
    scenario_id: str
    proposal_id: str
    severity: str
    reason: str
    source_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class ValidationSummary(BaseModel):
    """Human-readable validation summary for one shadow or replay result."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    business_line_id: str
    scenario_id: str
    proposal_id: str
    shadow_result_id: str
    improved: bool
    summary: str
    metric_diffs: dict[str, float] = Field(default_factory=dict)
    recommendation: str
    source_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProposalCandidate(BaseModel):
    """Rankable proposal candidate emitted by a proposer agent."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    business_line_id: str
    scenario_id: str
    proposal: Proposal
    proposer: str
    rationale: str
    score: float = 0.0
    risk_hint: float = 0.0
    source_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def for_parameter(
        cls,
        scenario_id: str,
        business_line_id: str,
        target_id: str,
        before: Any,
        after: Any,
        reason: str,
        expected_metric: str,
        source_ids: list[str],
        proposer: str = "parameter_proposer",
    ) -> "ProposalCandidate":
        """Create a small strategy-parameter patch candidate."""

        proposal = Proposal(
            scenario_id=scenario_id,
            proposal_kind=ProposalKind.PARAMETER,
            target_type=ProposalTargetType.STRATEGY_PARAM,
            target_id=target_id,
            patch=ProposalPatch(operation="replace", before=before, after=after),
            reason=reason,
            expected_metric=expected_metric,
            metadata={"business_line_id": business_line_id},
        )
        return cls(
            business_line_id=business_line_id,
            scenario_id=scenario_id,
            proposal=proposal,
            proposer=proposer,
            rationale=reason,
            source_ids=source_ids,
        )

    @classmethod
    def for_prompt_slot(
        cls,
        scenario_id: str,
        business_line_id: str,
        target_id: str,
        before: str,
        after: str,
        reason: str,
        expected_metric: str,
        source_ids: list[str],
        proposer: str = "prompt_proposer",
    ) -> "ProposalCandidate":
        """Create a bounded prompt-slot patch candidate."""

        proposal = Proposal(
            scenario_id=scenario_id,
            proposal_kind=ProposalKind.PROMPT,
            target_type=ProposalTargetType.PROMPT_SLOT,
            target_id=target_id,
            patch=ProposalPatch(operation="replace", before=before, after=after),
            reason=reason,
            expected_metric=expected_metric,
            metadata={"business_line_id": business_line_id},
        )
        return cls(
            business_line_id=business_line_id,
            scenario_id=scenario_id,
            proposal=proposal,
            proposer=proposer,
            rationale=reason,
            source_ids=source_ids,
        )


class ShadowReplayStatus(str, Enum):
    """Shadow/replay job lifecycle."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ShadowReplayJob(BaseModel):
    """A scheduled shadow or replay validation job."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    business_line_id: str
    scenario_id: str
    proposal_id: str
    candidate_id: str
    status: ShadowReplayStatus = ShadowReplayStatus.PENDING
    apply_requested: bool = False
    source_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class LearningLoopRunResult(BaseModel):
    """Single-trigger learning loop summary."""

    business_line_id: str
    scenario_id: str
    trigger_reason: str
    observations_count: int
    proposals_count: int
    safety_findings_count: int
    shadow_jobs_count: int
    validations_count: int
    applied_count: int = 0
    summary: str
    source_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


def validation_from_comparison(
    candidate: ProposalCandidate,
    shadow_result_id: str,
    comparison: ComparisonResult,
) -> ValidationSummary:
    """Build a validation summary from a schema-aware comparison result."""

    recommendation = "send_to_approval" if comparison.improved else "hold"
    return ValidationSummary(
        business_line_id=candidate.business_line_id,
        scenario_id=candidate.scenario_id,
        proposal_id=candidate.proposal.id,
        shadow_result_id=shadow_result_id,
        improved=comparison.improved,
        summary=comparison.summary,
        metric_diffs=comparison.business_metric_diffs,
        recommendation=recommendation,
        source_ids=[candidate.id, shadow_result_id],
        metadata={"objective_score": comparison.objective_score, "run_kind": comparison.run_kind},
    )
