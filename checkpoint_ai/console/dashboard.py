"""Human-facing V5 dashboard reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from checkpoint_ai.console.approval import ApprovalInbox
from checkpoint_ai.console.backup import BackupManager
from checkpoint_ai.console.cost import CostEventStore
from checkpoint_ai.console.read_model import ConsoleReadModel
from checkpoint_ai.logs import RawLogStore


class ConsoleRunReport(BaseModel):
    """One run detail report for the control console."""

    run_id: str
    scenario_id: str
    task: str
    status: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    value_summary: str
    core_questions: dict[str, str]


class ConsoleDashboard:
    """Build control-panel reports from existing stores."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.raw_logs = RawLogStore(self.db_path)

    def run_report(self, run_id: str) -> ConsoleRunReport:
        """Return a human-actionable run detail report."""

        raw = self.raw_logs.get(run_id)
        if raw is None:
            raise KeyError(f"Run not found: {run_id}")
        request = raw["request"]
        result = raw["result"]
        metrics = dict(result.get("metrics", {}))
        value_summary = str(result.get("value_summary") or result.get("failed_summary") or "")
        return ConsoleRunReport(
            run_id=run_id,
            scenario_id=str(raw["scenario_id"]),
            task=str(request.get("task", "")),
            status=str(result.get("status", "")),
            metrics=metrics,
            value_summary=value_summary,
            core_questions={
                "为什么运行": "执行 scenario adapter，生成可评估的业务结果。",
                "发生了什么": value_summary,
                "改变了什么": "单次 run 只记录结果，不直接改变线上配置。",
                "有没有变好": "没有关联 shadow/baseline 时只能作为样本，不能断言变好。",
            },
        )

    def stable_summary(self, scenario_id: str, backup_dir: str | Path) -> dict[str, Any]:
        """Return a compact V5 stable readiness summary."""

        snapshot = ConsoleReadModel(self.db_path).snapshot(scenario_id=scenario_id)
        backup = BackupManager(self.db_path, backup_dir).create_backup(label="v5-stable")
        cost = CostEventStore(self.db_path).daily_summary(provider="minimax", business_line_id="trading")
        return {
            "scenario_id": scenario_id,
            "pending_approval_count": len(ApprovalInbox(self.db_path).list_items(scenario_id=scenario_id)),
            "failed_run_count": snapshot.failed_run_count,
            "operator_summary": snapshot.operator_summary,
            "cost": {
                "provider": cost.provider,
                "business_line_id": cost.business_line_id,
                "total_tokens": cost.total_tokens,
                "estimated_cost": cost.estimated_cost,
            },
            "backup_id": backup.id,
        }
