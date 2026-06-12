"""Evidence-based version recommender."""

from __future__ import annotations

from dataclasses import dataclass

from loop_harness.evaluation import (
    EvidenceDecision,
    EvidenceEvaluation,
    EvidenceEvaluationEngine,
)
from loop_harness.metrics import ComparisonResult
from loop_harness.recommendation.models import (
    RecommendationDecision,
    VersionRecommendation,
)
from loop_harness.recommendation.store import VersionRecommendationStore
from loop_harness.shadow import ShadowResult, ShadowResultStore


@dataclass(slots=True)
class _Candidate:
    shadow: ShadowResult
    evaluation: EvidenceEvaluation
    rank_score: float


class VersionRecommender:
    """Recommend from existing shadow evidence without creating new proposals."""

    def __init__(
        self,
        shadow_results: ShadowResultStore,
        recommendations: VersionRecommendationStore,
        evidence_engine: EvidenceEvaluationEngine | None = None,
        min_confidence: float = 0.6,
    ) -> None:
        self.shadow_results = shadow_results
        self.recommendations = recommendations
        self.evidence_engine = evidence_engine or EvidenceEvaluationEngine(min_confidence=min_confidence)
        self.min_confidence = min_confidence

    def recommend_for_scenario(self, scenario_id: str) -> VersionRecommendation:
        """Create and store the best recommendation for one scenario."""

        return self._recommend(self.shadow_results.query_by_scenario(scenario_id), scenario_id)

    def recommend_for_proposal(self, proposal_id: str) -> VersionRecommendation:
        """Create and store a recommendation for one proposal."""

        shadows = self.shadow_results.query_by_proposal(proposal_id)
        scenario_id = shadows[-1].scenario_id if shadows else "unknown"
        return self._recommend(shadows, scenario_id)

    def _recommend(
        self,
        shadows: list[ShadowResult],
        scenario_id: str,
    ) -> VersionRecommendation:
        candidates = [candidate for shadow in shadows if (candidate := self._candidate(shadow)) is not None]
        if not candidates:
            return self._save(
                VersionRecommendation(
                    scenario_id=scenario_id,
                    target_id="unknown",
                    proposal_id=None,
                    decision=RecommendationDecision.INSUFFICIENT_EVIDENCE,
                    confidence=0.0,
                    objective_score=0.0,
                    reason="No comparable shadow evidence is available.",
                    recommended_action="collect_more_evidence",
                    source_shadow_ids=[],
                    evidence={"shadow_count": len(shadows)},
                )
            )
        rejects = [
            candidate
            for candidate in candidates
            if candidate.evaluation.decision == EvidenceDecision.WORSE
        ]
        if rejects:
            worst = max(rejects, key=lambda candidate: candidate.evaluation.confidence)
            return self._save(self._build(worst, RecommendationDecision.REJECT))
        improved = [
            candidate
            for candidate in candidates
            if candidate.evaluation.decision == EvidenceDecision.IMPROVED
            and candidate.evaluation.confidence >= self.min_confidence
        ]
        if improved:
            best = max(
                improved,
                key=lambda candidate: (
                    candidate.rank_score,
                    candidate.evaluation.confidence,
                    candidate.evaluation.objective_score,
                    candidate.shadow.created_at,
                ),
            )
            return self._save(self._build(best, RecommendationDecision.RECOMMEND))
        best_inconclusive = max(
            candidates,
            key=lambda candidate: (
                candidate.rank_score,
                candidate.evaluation.confidence,
                candidate.shadow.created_at,
            ),
        )
        return self._save(self._build(best_inconclusive, RecommendationDecision.INSUFFICIENT_EVIDENCE))

    def _candidate(self, shadow: ShadowResult) -> _Candidate | None:
        if not shadow.comparison_result:
            return None
        comparison = ComparisonResult(**shadow.comparison_result)
        evaluation = self.evidence_engine.evaluate(comparison)
        sample_count = int(evaluation.evidence.get("sample_count", 0) or 0)
        rank_score = round(
            (evaluation.confidence * 0.5)
            + (max(0.0, evaluation.objective_score) * 0.3)
            + (min(1.0, sample_count / max(1, self.evidence_engine.min_sample_count)) * 0.2),
            6,
        )
        return _Candidate(shadow=shadow, evaluation=evaluation, rank_score=rank_score)

    def _build(
        self,
        candidate: _Candidate,
        decision: RecommendationDecision,
    ) -> VersionRecommendation:
        return VersionRecommendation(
            scenario_id=candidate.shadow.scenario_id,
            target_id=candidate.shadow.agent_id,
            proposal_id=candidate.shadow.proposal_id,
            decision=decision,
            confidence=candidate.evaluation.confidence,
            objective_score=candidate.evaluation.objective_score,
            reason=candidate.evaluation.reason,
            recommended_action=candidate.evaluation.recommended_action.value,
            source_shadow_ids=[candidate.shadow.id],
            evidence={
                **candidate.evaluation.evidence,
                "rank_score": candidate.rank_score,
                "guardrail_violations": candidate.evaluation.guardrail_violations,
            },
        )

    def _save(self, recommendation: VersionRecommendation) -> VersionRecommendation:
        self.recommendations.save(recommendation)
        return recommendation
