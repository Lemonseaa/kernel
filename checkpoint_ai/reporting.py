"""Human-readable reports for V2 Agent optimization runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from checkpoint_ai.evaluation import EvidenceEvaluationEngine
from checkpoint_ai.insights import CrossScenarioInsightStore
from checkpoint_ai.logs import RawLogStore, SummaryLogStore
from checkpoint_ai.metrics import ComparisonResult
from checkpoint_ai.prompt import (
    PromptProposalStatus,
    PromptProposalStore,
    ProposalStatus,
    ProposalStore,
)
from checkpoint_ai.recommendation import VersionRecommendationStore
from checkpoint_ai.shadow import ShadowResultStore


class ReportGenerator:
    """Generate readable reports from V2 stores."""

    def __init__(self, db_path: str | Path) -> None:
        self.raw_logs = RawLogStore(db_path)
        self.summary_logs = SummaryLogStore(db_path)
        self.proposals = PromptProposalStore(db_path)
        self.generic_proposals = ProposalStore(db_path)
        self.shadow_results = ShadowResultStore(db_path)
        self.recommendations = VersionRecommendationStore(db_path)
        self.insights = CrossScenarioInsightStore(db_path)

    def latest(self, scenario_id: str | None = None) -> str:
        """Return the latest scoped run report when available."""

        logs = self._raw_logs_for_scope(scenario_id)
        if not logs:
            return "Run Report\n\n没有可报告的运行。"
        scenario_ids = {str(log["scenario_id"]) for log in logs}
        if scenario_id is None and len(scenario_ids) > 1:
            return (
                "Run Report\n\n"
                "需要指定 scenario_id。当前数据库包含多个 scenario，"
                "V5 控制台不允许隐式跨场景读取 latest run。"
            )
        return self.run(str(logs[-1]["run_id"]))

    def pending_items(self, scenario_id: str | None = None) -> list[dict[str, Any]]:
        """Return a unified pending inbox view for prompt and generic proposals."""

        items: list[dict[str, Any]] = []
        prompt_statuses = {
            PromptProposalStatus.PROPOSED,
            PromptProposalStatus.APPROVED,
        }
        for status in prompt_statuses:
            for proposal in self.proposals.list(status=status, scenario_id=scenario_id):
                if proposal.status == PromptProposalStatus.APPROVED and not proposal.metadata.get(
                    "awaiting_human_confirmation"
                ):
                    continue
                items.append(
                    {
                        "source_id": proposal.id,
                        "scenario_id": proposal.scenario_id,
                        "item_type": "prompt_proposal",
                        "status": proposal.status.value,
                        "title": f"Prompt patch: {proposal.agent_id}.{proposal.patch.slot.value}",
                        "summary": proposal.reason,
                        "expected_metric": proposal.expected_metric,
                        "created_at": proposal.created_at.isoformat(),
                    }
                )
        generic_statuses = {
            ProposalStatus.PROPOSED,
            ProposalStatus.APPROVED,
        }
        for generic_status in generic_statuses:
            for generic_proposal in self.generic_proposals.list(
                status=generic_status,
                scenario_id=scenario_id,
            ):
                items.append(
                    {
                        "source_id": generic_proposal.id,
                        "scenario_id": generic_proposal.scenario_id,
                        "item_type": f"{generic_proposal.proposal_kind.value}_proposal",
                        "status": generic_proposal.status.value,
                        "title": f"{generic_proposal.proposal_kind.value}: {generic_proposal.target_id}",
                        "summary": generic_proposal.reason,
                        "expected_metric": generic_proposal.expected_metric,
                        "created_at": generic_proposal.created_at.isoformat(),
                    }
                )
        return sorted(items, key=lambda item: str(item["created_at"]))

    def run(self, run_id: str) -> str:
        """Generate a report for one adapter run."""

        raw = self.raw_logs.get(run_id)
        if raw is None:
            return f"Run Report\n\nrun_id: {run_id}\n状态: not found"
        request = raw["request"]
        result = raw["result"]
        return "\n".join(
            [
                "Run Report",
                "",
                f"scenario_id: {raw['scenario_id']}",
                f"run_id: {run_id}",
                f"timestamp: {raw['created_at']}",
                f"任务类型: {request.get('task')}",
                "",
                "为什么运行:",
                "执行 adapter run，用于生成可评估的业务输出和 baseline 样本。",
                "",
                "发生了什么:",
                f"status: {result.get('status')}",
                f"value_summary: {result.get('value_summary')}",
                "",
                "输入摘要:",
                self._pretty(request.get("context", {})),
                "",
                "输出摘要:",
                str(result.get("answer", "")),
                "",
                "metrics:",
                self._pretty(result.get("metrics", {})),
                "",
                "改变了什么:",
                "本次 adapter run 只记录结果，不改变 prompt 或线上配置。",
                "",
                "比baseline好了还是差了:",
                "未关联 shadow/proposal 时不能判断，只能作为后续 baseline 样本。",
            ]
        )

    def proposal(self, proposal_id: str) -> str:
        """Generate a report for one prompt proposal."""

        proposal = self.proposals.get(proposal_id)
        if proposal is None:
            return f"Proposal Report\n\nproposal_id: {proposal_id}\n状态: not found"
        shadows = self.shadow_results.query_by_proposal(proposal_id)
        latest_shadow = shadows[-1] if shadows else None
        comparison = "尚无 shadow 结果，不能判断。"
        evidence_section = "证据判断:\n尚无 shadow 结果。"
        if latest_shadow is not None:
            comparison = f"metric_diff: {self._pretty(latest_shadow.metric_diff)}"
            evidence_section = self._evidence_section(latest_shadow.comparison_result)
        return "\n".join(
            [
                "Proposal Report",
                "",
                f"proposal_id: {proposal.id}",
                f"scenario_id: {proposal.scenario_id}",
                f"agent_id: {proposal.agent_id}",
                f"status: {proposal.status.value}",
                f"expected_metric: {proposal.expected_metric}",
                "",
                "proposal内容和建议:",
                f"slot: {proposal.patch.slot.value}",
                f"operation: {proposal.patch.operation}",
                f"before: {proposal.patch.before}",
                f"after: {proposal.patch.after}",
                f"reason: {proposal.reason}",
                "",
                "比baseline好了还是差了:",
                comparison,
                "",
                evidence_section,
            ]
        )

    def recommendation(self, recommendation_id: str) -> str:
        """Generate a report for one version recommendation."""

        recommendation = self.recommendations.get(recommendation_id)
        if recommendation is None:
            return f"Recommendation Report\n\nrecommendation_id: {recommendation_id}\n状态: not found"
        return "\n".join(
            [
                "Recommendation Report",
                "",
                f"recommendation_id: {recommendation.id}",
                f"scenario_id: {recommendation.scenario_id}",
                f"target_id: {recommendation.target_id}",
                f"proposal_id: {recommendation.proposal_id}",
                f"decision: {recommendation.decision.value}",
                f"status: {recommendation.status.value}",
                f"confidence: {recommendation.confidence}",
                f"objective_score: {recommendation.objective_score}",
                f"recommended_action: {recommendation.recommended_action}",
                "",
                "为什么推荐/拒绝:",
                recommendation.reason,
                "",
                "证据来源:",
                f"source_shadow_ids: {self._pretty(recommendation.source_shadow_ids)}",
                f"evidence: {self._pretty(recommendation.evidence)}",
            ]
        )

    def insight(self, insight_id: str) -> str:
        """Generate a report for one cross-scenario insight."""

        insight = self.insights.get(insight_id)
        if insight is None:
            return f"Cross-Scenario Insight Report\n\ninsight_id: {insight_id}\n状态: not found"
        return "\n".join(
            [
                "Cross-Scenario Insight Report",
                "",
                f"insight_id: {insight.id}",
                f"source_scenario_id: {insight.source_scenario_id}",
                f"target_scenario_id: {insight.target_scenario_id}",
                f"decision: {insight.decision.value}",
                f"similarity_score: {insight.similarity_score}",
                f"risk: {insight.risk}",
                f"reason: {insight.reason}",
                f"rejection_reasons: {self._pretty(insight.rejection_reasons)}",
                "",
                "This is an observation only. It does not migrate prompt, parameter, strategy, or policy.",
            ]
        )

    def _all_raw_logs(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        # RawLogStore intentionally scopes query by scenario; direct SQL keeps report simple.
        if self.raw_logs.path is None:
            return list(self.raw_logs._memory.values())
        import sqlite3

        with sqlite3.connect(self.raw_logs.path) as conn:
            conn.row_factory = sqlite3.Row
            for row in conn.execute("SELECT run_id FROM raw_logs ORDER BY created_at, rowid").fetchall():
                raw = self.raw_logs.get(row["run_id"])
                if raw is not None:
                    rows.append(raw)
        return rows

    def _raw_logs_for_scope(self, scenario_id: str | None) -> list[dict[str, Any]]:
        if scenario_id is not None:
            return self.raw_logs.query_by_scenario(scenario_id)
        return self._all_raw_logs()

    @staticmethod
    def _pretty(value: object) -> str:
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)

    @staticmethod
    def _evidence_section(comparison_result: dict[str, Any]) -> str:
        if not comparison_result:
            return "证据判断:\ncomparison_result 不存在。"
        comparison = ComparisonResult(**comparison_result)
        evaluation = EvidenceEvaluationEngine().evaluate(comparison)
        sample_count = evaluation.evidence.get("sample_count", 0)
        return "\n".join(
            [
                "证据判断:",
                f"evidence_decision: {evaluation.decision.value}",
                f"recommended_action: {evaluation.recommended_action.value}",
                f"confidence: {evaluation.confidence}",
                f"reason: {evaluation.reason}",
                f"run_kind: {comparison.run_kind}",
                f"sample_count: {sample_count}",
                f"guardrail_violations: {evaluation.guardrail_violations}",
            ]
        )
