"""Kernel health checker."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from kernel.diagnostics.diagnostic_report import CheckResult, DiagnosticReport
from kernel.llm import LLMRequest, MiniMaxProvider
from kernel.models import RunState
from kernel.persistence import SQLiteStore


class HealthChecker:
    """Run cheap checks that help locate operational problems quickly."""

    def __init__(self, kernel: object | None = None) -> None:
        """Create a health checker for one kernel or standalone defaults."""

        self._tmp_dir: tempfile.TemporaryDirectory[str] | None = None
        if kernel is None:
            self._tmp_dir = tempfile.TemporaryDirectory()
            from kernel.kernel import Kernel

            kernel = Kernel(sqlite_path=Path(self._tmp_dir.name) / "kernel-health.db")
        self.kernel = kernel

    def generate_diagnostic_report(self) -> DiagnosticReport:
        """Run all checks and return an aggregated report."""

        checks = [
            self._check_database(),
            self._check_provider(),
            self._check_event_bus(),
            self._check_approval_queue(),
            self._check_cost_budget(),
            self._check_recent_runs(),
        ]
        recommendations = self._recommendations(checks)
        return DiagnosticReport(
            overall_status=self._overall_status(checks),
            checks=checks,
            recommendations=recommendations,
        )

    def _check_database(self) -> CheckResult:
        """Check whether SQLite can write and read state."""

        try:
            store = self._store()
            run_id = "__healthcheck__"
            with store._connection() as conn:  # noqa: SLF001 - health check probes concrete store.
                conn.execute(
                    """
                    INSERT INTO runs (id, business_line_id, user_request, state, metadata)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET state=excluded.state
                    """,
                    (run_id, "default", "health check", "pending", "{}"),
                )
                row = conn.execute("SELECT id FROM runs WHERE id = ?", (run_id,)).fetchone()
            if row is None:
                return CheckResult("database", "error", "SQLite read/write probe failed.")
            return CheckResult("database", "ok", "SQLite read/write probe succeeded.")
        except Exception as exc:
            return CheckResult("database", "error", f"Database unavailable: {exc}")

    def _check_provider(self) -> CheckResult:
        """Check whether the configured LLM provider responds."""

        provider = getattr(self.kernel, "llm_provider", None) or MiniMaxProvider()
        try:
            response = provider.generate(LLMRequest(prompt="health check"))
            return CheckResult(
                "provider",
                "ok",
                f"Provider {response.provider} responded.",
                {"model": response.model},
            )
        except Exception as exc:
            return CheckResult("provider", "error", f"Provider unavailable: {exc}")

    def _check_event_bus(self) -> CheckResult:
        """Check whether events have subscribers."""

        bus = getattr(self.kernel, "event_bus", None)
        if bus is None:
            return CheckResult("event_bus", "warning", "EventBus is not configured.")
        subscriber_count = len(bus._subscribers) + sum(  # noqa: SLF001 - diagnostics inspect runtime.
            len(handlers) for handlers in bus._typed_subscribers.values()  # noqa: SLF001
        )
        status = "ok" if subscriber_count else "warning"
        message = f"EventBus has {subscriber_count} subscriber(s)."
        return CheckResult("event_bus", status, message, {"subscriber_count": subscriber_count})

    def _check_approval_queue(self) -> CheckResult:
        """Check unresolved human approvals."""

        gate = getattr(self.kernel, "human_gate", None)
        pending = gate.pending_requests() if gate is not None else []
        if pending:
            return CheckResult(
                "approval_queue",
                "warning",
                f"{len(pending)} approval request(s) are pending.",
                {"pending": len(pending)},
            )
        return CheckResult("approval_queue", "ok", "No pending approval requests.", {"pending": 0})

    def _check_cost_budget(self) -> CheckResult:
        """Check cost budget events and configured budgets."""

        tracker = getattr(self.kernel, "cost_tracker", None)
        if tracker is None:
            return CheckResult("cost_budget", "warning", "CostTracker is not configured.")
        over_budget: list[dict[str, Any]] = []
        for (business_line_id, provider), budget in tracker._budgets.items():  # noqa: SLF001
            current = tracker._estimate_daily_cost(  # noqa: SLF001
                provider,
                business_line_id,
                tracker._today().isoformat(),  # noqa: SLF001
            )
            if current > budget:
                over_budget.append(
                    {
                        "business_line_id": business_line_id,
                        "provider": provider,
                        "budget": budget,
                        "current": current,
                    }
                )
        if over_budget:
            return CheckResult("cost_budget", "error", "One or more budgets are exceeded.", {"items": over_budget})
        return CheckResult("cost_budget", "ok", "No budget is exceeded.", {"budgets": len(tracker._budgets)})  # noqa: SLF001

    def _check_recent_runs(self) -> CheckResult:
        """Check whether recent persisted runs failed."""

        store = getattr(self.kernel, "store", None)
        if store is None:
            return CheckResult("recent_runs", "warning", "No store is configured for recent run checks.")
        runs = store.list_runs()[-10:]
        failed = [run for run in runs if run["state"] == RunState.FAILED.value]
        if failed:
            return CheckResult(
                "recent_runs",
                "warning",
                f"{len(failed)} recent run(s) failed.",
                {"failed_run_ids": [run["id"] for run in failed]},
            )
        return CheckResult("recent_runs", "ok", "No failed recent runs.", {"checked": len(runs)})

    def _store(self) -> SQLiteStore:
        """Return the kernel store or a temporary standalone store."""

        store = getattr(self.kernel, "store", None)
        if store is not None:
            return store
        self._tmp_dir = tempfile.TemporaryDirectory()
        return SQLiteStore(Path(self._tmp_dir.name) / "kernel-health.db")

    def _overall_status(self, checks: list[CheckResult]) -> str:
        """Compute healthy/degraded/unhealthy from check severities."""

        if any(check.status == "error" for check in checks):
            return "unhealthy"
        if any(check.status == "warning" for check in checks):
            return "degraded"
        return "healthy"

    def _recommendations(self, checks: list[CheckResult]) -> list[str]:
        """Build concise repair suggestions."""

        recommendations: list[str] = []
        for check in checks:
            if check.status == "ok":
                continue
            if check.component == "database":
                recommendations.append("检查 SQLite 路径、目录权限和数据库文件是否可写。")
            elif check.component == "provider":
                recommendations.append("检查 LLM Provider 配置、API Key、网络和超时设置。")
            elif check.component == "event_bus":
                recommendations.append("确认审计日志、指标、告警等订阅者已注册到 EventBus。")
            elif check.component == "approval_queue":
                recommendations.append("处理积压的 HumanGate 审批请求，或调整审批策略。")
            elif check.component == "cost_budget":
                recommendations.append("降低任务量、切换低成本模型，或提高对应 BusinessLine 预算。")
            elif check.component == "recent_runs":
                recommendations.append("查看失败 Run 的 Task 错误并使用 resume_run 从失败点继续。")
        return recommendations
