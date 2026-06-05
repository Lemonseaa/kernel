"""Proposal generation hive for V7."""

from __future__ import annotations

from checkpoint_ai.learning.models import Observation, ObservationType, ProposalCandidate


class PromptProposer:
    """Generate small prompt-slot patches from observations."""

    def propose(self, observation: Observation) -> list[ProposalCandidate]:
        """Generate prompt candidates without rewriting full prompts."""

        if observation.observation_type not in {ObservationType.METRIC_ANOMALY, ObservationType.DECISION_PATTERN}:
            return []
        metric = str(observation.metadata.get("metric", "primary_metric"))
        return [
            ProposalCandidate.for_prompt_slot(
                scenario_id=observation.scenario_id,
                business_line_id=observation.business_line_id,
                target_id="research_agent.constraints",
                before=f"Optimize for {metric}.",
                after=f"Optimize for {metric}; include one explicit risk caveat and metric evidence.",
                reason=f"Observation suggests {metric} needs clearer evidence handling.",
                expected_metric=metric,
                source_ids=[observation.id],
            )
        ]


class ParameterProposer:
    """Generate bounded parameter patches from observations."""

    def propose(self, observation: Observation) -> list[ProposalCandidate]:
        """Generate parameter candidates for metric anomalies."""

        if observation.observation_type != ObservationType.METRIC_ANOMALY:
            return []
        metric = str(observation.metadata.get("metric", "primary_metric"))
        target_id = str(observation.metadata.get("target_id", "strategy.fast_window"))
        return [
            ProposalCandidate.for_parameter(
                scenario_id=observation.scenario_id,
                business_line_id=observation.business_line_id,
                target_id=target_id,
                before=8,
                after=10,
                reason=f"Small parameter adjustment may improve {metric}.",
                expected_metric=metric,
                source_ids=[observation.id],
            )
        ]
