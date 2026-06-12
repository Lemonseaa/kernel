"""Service layer for external workflow evidence ingestion and reporting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loop_harness.evaluation import EvidenceDecision, EvidenceEvaluationEngine
from loop_harness.evidence.models import (
    DecisionRecommendation,
    EvidenceReport,
    ExternalWorkflowRun,
    IngestResult,
    WorkflowVisualization,
)
from loop_harness.evidence.quality import EvidenceQualityGate
from loop_harness.evidence.storage import EvidenceStore
from loop_harness.metrics import (
    MetricCategory,
    MetricDirection,
    MetricSchema,
    MetricSchemaRegistry,
)
from loop_harness.shadow import MetricComparator, RunKind


class EvidenceService:
    """Coordinate ingest, visualization, comparison, and reports."""

    def __init__(self, store: EvidenceStore) -> None:
        self.store = store

    def ingest_file(self, path: str | Path) -> IngestResult:
        """Load and ingest one external workflow run JSON file."""

        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return self.ingest_payload(payload)

    def ingest_payload(self, payload: dict[str, Any]) -> IngestResult:
        """Normalize one external workflow run payload and persist derived evidence."""

        run = ExternalWorkflowRun.model_validate(payload)
        visualization = self.build_visualization(run)
        report = self.build_report(run, visualization)
        self.store.save(run, visualization, report)
        return IngestResult(run=run, visualization=visualization, report=report)

    def build_visualization(self, run: ExternalWorkflowRun) -> WorkflowVisualization:
        """Build diagnostic workflow map data for one imported run."""

        node_ids = [node.id for node in run.nodes]
        total_nodes = len(node_ids)
        traced_node_ids = self._ordered_unique(event.node_id for event in run.trace if event.node_id in node_ids)
        metric_node_ids = self._ordered_unique(
            event.node_id for event in run.trace if event.node_id in node_ids and event.metrics
        )
        explicit_black_boxes = {
            node.id for node in run.nodes if bool(node.metadata.get("black_box") or node.metadata.get("opaque"))
        }
        black_box_node_ids = [
            node_id for node_id in node_ids if node_id not in traced_node_ids or node_id in explicit_black_boxes
        ]
        error_node_ids = self._ordered_unique(
            event.node_id for event in run.trace if event.node_id in node_ids and (event.error or event.status == "failed")
        )
        node_costs = {
            event.node_id: float(event.cost)
            for event in run.trace
            if event.node_id in node_ids and event.cost is not None
        }
        node_latencies = {
            event.node_id: float(event.duration_ms)
            for event in run.trace
            if event.node_id in node_ids and event.duration_ms is not None
        }
        return WorkflowVisualization(
            workflow_id=run.workflow_id,
            run_id=run.run_id,
            nodes=run.nodes,
            edges=run.edges,
            run_path=traced_node_ids,
            total_nodes=total_nodes,
            traced_node_ids=traced_node_ids,
            metric_node_ids=metric_node_ids,
            black_box_node_ids=black_box_node_ids,
            error_node_ids=error_node_ids,
            trace_coverage=self._coverage(len(traced_node_ids), total_nodes),
            metric_coverage=self._coverage(len(metric_node_ids), total_nodes),
            node_costs=node_costs,
            node_latencies_ms=node_latencies,
        )

    def build_report(
        self,
        run: ExternalWorkflowRun,
        visualization: WorkflowVisualization,
    ) -> EvidenceReport:
        """Build a run-level evidence report before baseline comparison."""

        buckets = self._bucket_metrics(run.metrics, self._registry_for(run))
        recommendation = self._run_recommendation(visualization, run)
        quality = EvidenceQualityGate().evaluate(run, visualization)
        return EvidenceReport(
            workflow_id=run.workflow_id,
            run_id=run.run_id,
            run_kind=run.run_kind.value,
            trace_coverage=visualization.trace_coverage,
            metric_coverage=visualization.metric_coverage,
            black_box_node_ids=visualization.black_box_node_ids,
            business_metrics=buckets[MetricCategory.BUSINESS],
            system_metrics=buckets[MetricCategory.SYSTEM],
            data_quality_metrics=buckets[MetricCategory.DATA_QUALITY],
            recommendation=recommendation,
            summary=self._run_summary(run, visualization, recommendation),
            evidence={
                "node_count": visualization.total_nodes,
                "trace_coverage": visualization.trace_coverage,
                "metric_coverage": visualization.metric_coverage,
                "black_box_node_count": len(visualization.black_box_node_ids),
                "quality": quality.model_dump(mode="json"),
            },
        )

    def compare(self, baseline_run_id: str, candidate_run_id: str) -> EvidenceReport:
        """Compare two stored external workflow runs."""

        baseline = self.store.get_run(baseline_run_id)
        candidate = self.store.get_run(candidate_run_id)
        if baseline is None:
            raise ValueError(f"Unknown baseline run: {baseline_run_id}")
        if candidate is None:
            raise ValueError(f"Unknown candidate run: {candidate_run_id}")
        registry = self._registry_for(candidate.run)
        comparator = MetricComparator(registry)
        comparison = comparator.compare(
            baseline.run.metrics,
            candidate.run.metrics,
            run_kind=RunKind(candidate.run.run_kind.value),
            provenance={
                "baseline_run_id": baseline_run_id,
                "candidate_run_id": candidate_run_id,
                "sample_count": candidate.run.metrics.get("sample_count", 0),
                "data_source": candidate.run.metadata.get("data_source"),
            },
        )
        evaluation = EvidenceEvaluationEngine().evaluate(comparison)
        recommendation = self._comparison_recommendation(evaluation.decision)
        report = EvidenceReport(
            workflow_id=candidate.run.workflow_id,
            baseline_run_id=baseline_run_id,
            candidate_run_id=candidate_run_id,
            run_kind=candidate.run.run_kind.value,
            trace_coverage=candidate.visualization.trace_coverage,
            metric_coverage=candidate.visualization.metric_coverage,
            black_box_node_ids=candidate.visualization.black_box_node_ids,
            business_metrics=candidate.report.business_metrics,
            system_metrics=candidate.report.system_metrics,
            data_quality_metrics=candidate.report.data_quality_metrics,
            comparison=comparison,
            recommendation=recommendation,
            summary=(
                f"Candidate {candidate_run_id} vs baseline {baseline_run_id}: "
                f"{comparison.summary} Evidence decision={evaluation.decision.value}; "
                f"recommendation={recommendation.value}."
            ),
            evidence={
                "evaluation": {
                    "decision": evaluation.decision.value,
                    "recommended_action": evaluation.recommended_action.value,
                    "confidence": evaluation.confidence,
                    "reason": evaluation.reason,
                },
                "quality": candidate.report.evidence.get("quality", {}),
                "baseline_run_id": baseline_run_id,
                "candidate_run_id": candidate_run_id,
            },
        )
        self.store.save_comparison_report(report)
        return report

    @staticmethod
    def _ordered_unique(values: Any) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return result

    @staticmethod
    def _coverage(count: int, total: int) -> float:
        if total <= 0:
            return 1.0
        return round(count / total, 4)

    @staticmethod
    def _registry_for(run: ExternalWorkflowRun) -> MetricSchemaRegistry:
        schemas: list[MetricSchema] = []
        for name, raw_schema in run.metric_schema.items():
            if not isinstance(raw_schema, dict):
                continue
            schemas.append(
                MetricSchema(
                    name=name,
                    direction=MetricDirection(raw_schema.get("direction", "higher")),
                    category=MetricCategory(raw_schema.get("category", "business")),
                    weight=float(raw_schema.get("weight", 1.0)),
                    threshold=raw_schema.get("threshold"),
                    is_guardrail=bool(raw_schema.get("is_guardrail", False)),
                )
            )
        return MetricSchemaRegistry(schemas) if schemas else MetricSchemaRegistry.default_quant()

    @staticmethod
    def _bucket_metrics(
        metrics: dict[str, float],
        registry: MetricSchemaRegistry,
    ) -> dict[MetricCategory, dict[str, float]]:
        buckets: dict[MetricCategory, dict[str, float]] = {
            MetricCategory.BUSINESS: {},
            MetricCategory.SYSTEM: {},
            MetricCategory.DATA_QUALITY: {},
        }
        for name, value in metrics.items():
            category = registry.schema_for(name).category
            if category == MetricCategory.SYSTEM:
                buckets[MetricCategory.SYSTEM][name] = value
            elif category == MetricCategory.DATA_QUALITY:
                buckets[MetricCategory.DATA_QUALITY][name] = value
            else:
                buckets[MetricCategory.BUSINESS][name] = value
        return buckets

    @staticmethod
    def _run_recommendation(
        visualization: WorkflowVisualization,
        run: ExternalWorkflowRun,
    ) -> DecisionRecommendation:
        if visualization.error_node_ids:
            return DecisionRecommendation.REJECT
        if visualization.black_box_node_ids or visualization.trace_coverage < 1.0:
            return DecisionRecommendation.CONTINUE_SHADOW
        if not run.metrics:
            return DecisionRecommendation.INCONCLUSIVE
        return DecisionRecommendation.CONTINUE_SHADOW

    @staticmethod
    def _comparison_recommendation(decision: EvidenceDecision) -> DecisionRecommendation:
        if decision == EvidenceDecision.IMPROVED:
            return DecisionRecommendation.APPROVE
        if decision == EvidenceDecision.WORSE:
            return DecisionRecommendation.REJECT
        return DecisionRecommendation.CONTINUE_SHADOW

    @staticmethod
    def _run_summary(
        run: ExternalWorkflowRun,
        visualization: WorkflowVisualization,
        recommendation: DecisionRecommendation,
    ) -> str:
        return (
            f"Run {run.run_id} imported for workflow {run.workflow_id}; "
            f"trace_coverage={visualization.trace_coverage:.2f}, "
            f"metric_coverage={visualization.metric_coverage:.2f}, "
            f"black_box_nodes={len(visualization.black_box_node_ids)}, "
            f"recommendation={recommendation.value}."
        )
