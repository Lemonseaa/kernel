"""V5.1 console read model aggregation."""

from __future__ import annotations

from pathlib import Path

from checkpoint_ai.console.models import (
    ConsoleRunSummary,
    ConsoleScenarioSummary,
    ConsoleSnapshot,
)
from checkpoint_ai.isolation import ScenarioScope
from checkpoint_ai.logs import SummaryLogStore
from checkpoint_ai.reporting import ReportGenerator
from checkpoint_ai.scenario import Scenario, ScenarioStatus, ScenarioStore


class ConsoleReadModel:
    """Build scope-aware snapshots for CLI or UI surfaces."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.scenarios = ScenarioStore(self.db_path)
        self.summary_logs = SummaryLogStore(self.db_path)
        self.reports = ReportGenerator(self.db_path)

    def snapshot(
        self,
        scenario_id: str | None = None,
        allow_cross_scenario: bool = False,
        reason: str | None = None,
        limit: int = 10,
    ) -> ConsoleSnapshot:
        """Return one human-facing operator snapshot."""

        if scenario_id is None and allow_cross_scenario and not (reason or "").strip():
            raise ValueError("Cross-scenario access requires reason")
        scope = ScenarioScope(
            scenario_id=scenario_id,
            allow_cross_scenario=allow_cross_scenario,
            reason=reason,
        )
        scenarios = self._scenarios_for_scope(scope)
        scenario_ids = [scenario.id for scenario in scenarios]
        recent_runs = self._recent_runs(scenario_ids, limit=limit)
        pending_items = self.reports.pending_items(scenario_id=scenario_id)
        active = [scenario for scenario in scenarios if scenario.status == ScenarioStatus.ACTIVE]
        archived = [scenario for scenario in scenarios if scenario.status == ScenarioStatus.ARCHIVED]
        failed_runs = [run for run in recent_runs if run.status == "failed"]
        pending_count = len(pending_items)
        return ConsoleSnapshot(
            scope=scope,
            scenario_count=len(scenarios),
            active_scenario_count=len(active),
            archived_scenario_count=len(archived),
            recent_run_count=len(recent_runs),
            failed_run_count=len(failed_runs),
            pending_approval_count=pending_count,
            scenarios=[
                ConsoleScenarioSummary(
                    scenario_id=scenario.id,
                    name=scenario.name,
                    status=scenario.status.value,
                    adapter_type=scenario.adapter_type,
                    business_line_id=scenario.business_line_id,
                    domain_tags=self._domain_tags(scenario.metadata),
                )
                for scenario in scenarios
            ],
            latest_runs=recent_runs,
            pending_items=pending_items,
            operator_summary=self._operator_summary(
                pending_count=pending_count,
                failed_count=len(failed_runs),
                archived_count=len(archived),
            ),
        )

    def _scenarios_for_scope(self, scope: ScenarioScope) -> list[Scenario]:
        if scope.scenario_id is not None:
            scenario = self.scenarios.get(scope.scenario_id)
            return [] if scenario is None else [scenario]
        if scope.allow_cross_scenario:
            return list(self.scenarios.list())
        return []

    def _recent_runs(self, scenario_ids: list[str], limit: int) -> list[ConsoleRunSummary]:
        runs: list[ConsoleRunSummary] = []
        for scenario_id in scenario_ids:
            for row in self.summary_logs.query_by_scenario(scenario_id):
                runs.append(
                    ConsoleRunSummary(
                        run_id=str(row["run_id"]),
                        scenario_id=str(row["scenario_id"]),
                        task=str(row["task"]),
                        status=str(row["status"]),
                        value_summary=str(row.get("value_summary") or row.get("failed_summary") or ""),
                        metrics=dict(row.get("metrics", {})),
                        created_at=str(row["created_at"]),
                    )
                )
        return sorted(runs, key=lambda run: run.created_at, reverse=True)[:limit]

    @staticmethod
    def _domain_tags(metadata: dict[str, object]) -> list[str]:
        value = metadata.get("domain_tags")
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        return []

    @staticmethod
    def _operator_summary(pending_count: int, failed_count: int, archived_count: int) -> str:
        parts: list[str] = []
        if pending_count:
            parts.append(f"需要处理 {pending_count} 个审批项")
        if failed_count:
            parts.append(f"最近有 {failed_count} 个失败 run")
        if archived_count:
            parts.append(f"{archived_count} 个 scenario 已归档")
        if not parts:
            return "当前没有需要立即处理的事项。"
        return "；".join(parts) + "。"
