"""Cross-scenario insight preview."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field


class CrossScenarioInsightDecision(str, Enum):
    """Insight preview decision."""

    SUGGEST = "suggest"
    REJECT = "reject"


class ScenarioInsightInput(BaseModel):
    """Summarized scenario evidence used for preview-only insight."""

    scenario_id: str
    domain_tags: list[str]
    metric_names: list[str]
    run_count: int
    non_synthetic_recommendation_count: int


class CrossScenarioInsight(BaseModel):
    """Observation-only possible cross-scenario insight."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_scenario_id: str
    target_scenario_id: str
    decision: CrossScenarioInsightDecision
    similarity_score: float
    reason: str
    risk: str
    source_evidence_ids: list[str] = Field(default_factory=list)
    rejection_reasons: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CrossScenarioInsightGenerator:
    """Generate preview-only cross-scenario insights."""

    def compare(
        self,
        source: ScenarioInsightInput,
        target: ScenarioInsightInput,
    ) -> CrossScenarioInsight:
        """Compare two scenario summaries."""

        tag_similarity = self._overlap(source.domain_tags, target.domain_tags)
        metric_similarity = self._overlap(source.metric_names, target.metric_names)
        similarity = round((tag_similarity * 0.55) + (metric_similarity * 0.45), 4)
        rejections: list[str] = []
        if source.run_count < 20 or target.run_count < 20:
            rejections.append("run_count")
        if metric_similarity < 0.5:
            rejections.append("metric_comparability")
        if tag_similarity < 0.3:
            rejections.append("domain_similarity")
        if source.non_synthetic_recommendation_count == 0 or target.non_synthetic_recommendation_count == 0:
            rejections.append("non_synthetic_evidence")
        if rejections:
            return CrossScenarioInsight(
                source_scenario_id=source.scenario_id,
                target_scenario_id=target.scenario_id,
                decision=CrossScenarioInsightDecision.REJECT,
                similarity_score=similarity,
                reason="Cross-scenario insight rejected; evidence is not strong or comparable enough.",
                risk="high",
                rejection_reasons=rejections,
            )
        return CrossScenarioInsight(
            source_scenario_id=source.scenario_id,
            target_scenario_id=target.scenario_id,
            decision=CrossScenarioInsightDecision.SUGGEST,
            similarity_score=similarity,
            reason="Possible related pattern; observation only and does not migrate anything.",
            risk="medium",
        )

    @staticmethod
    def _overlap(left: list[str], right: list[str]) -> float:
        left_set = {item.strip().lower() for item in left if item.strip()}
        right_set = {item.strip().lower() for item in right if item.strip()}
        if not left_set or not right_set:
            return 0.0
        return len(left_set & right_set) / len(left_set | right_set)
