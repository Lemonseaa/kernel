"""Optional HTTP API surface for the checkpoint_ai."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from checkpoint_ai.adapter import (
    AdapterRegistry,
    DummyAdapter,
    OPCAgentAdapter,
    QuantResearchDemoAdapter,
)
from checkpoint_ai.auth import APIKeyManager, BearerTokenAuth
from checkpoint_ai.checkpoint_ai import CheckpointAI
from checkpoint_ai.console import ApprovalInbox, BackupManager, ConsoleDashboard, ConsoleReadModel
from checkpoint_ai.logs import RawLogStore, SummaryLogStore
from checkpoint_ai.optimization import ParameterSuggestionStore
from checkpoint_ai.prompt import PromptProposalStore, ProposalStore
from checkpoint_ai.recommendation import VersionRecommendationStore
from checkpoint_ai.scenario import ScenarioRegistry, ScenarioRunner, ScenarioStore

_uvicorn_server: Any

try:
    import uvicorn as _uvicorn
except ImportError:  # pragma: no cover - exercised only when optional server dependency is absent.
    class _MissingUvicorn:
        """Clear failure object for environments without uvicorn installed."""

        @staticmethod
        def run(*_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("uvicorn is required to serve the CheckpointAI API")

    _uvicorn_server = _MissingUvicorn()
else:
    _uvicorn_server = _uvicorn


@dataclass(slots=True)
class FallbackApp:
    """Small app object used when FastAPI is not installed."""

    checkpoint_ai: CheckpointAI
    auth: BearerTokenAuth
    routes: list[dict[str, str]] = field(default_factory=list)

    def authenticate(self, authorization: str | None) -> bool:
        """Validate a bearer token in fallback mode."""

        return self.auth.authenticate(authorization)


def create_app(
    checkpoint_ai: CheckpointAI | None = None,
    auth_manager: APIKeyManager | None = None,
    db_path: str | Path | None = None,
    backup_dir: str | Path | None = None,
    force_fallback: bool = False,
) -> Any:
    """Create a FastAPI app when available, otherwise return a fallback app."""

    active_checkpoint_ai = checkpoint_ai or CheckpointAI.from_env()
    active_auth = BearerTokenAuth(auth_manager or APIKeyManager(initial_tokens=_initial_tokens_from_env()))
    active_db_path = Path(db_path or active_checkpoint_ai.config.sqlite_path)
    active_backup_dir = Path(backup_dir or active_db_path.parent / "backups")
    if force_fallback:
        return _fallback_app(active_checkpoint_ai, active_auth)
    try:
        from fastapi import (  # type: ignore[import-not-found]
            Depends,
            FastAPI,
            Header,
            HTTPException,
        )
    except ImportError:
        return _fallback_app(active_checkpoint_ai, active_auth)

    app = FastAPI(title="CheckpointAI Control Console API")

    def require_auth(authorization: str | None = Header(default=None)) -> None:
        if not active_auth.authenticate(authorization):
            raise HTTPException(status_code=401, detail="Invalid or missing bearer token.")

    @app.get("/health")
    def health(_auth: None = Depends(require_auth)) -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/runs")
    def list_runs(_auth: None = Depends(require_auth)) -> list[dict[str, Any]]:
        return active_checkpoint_ai.store.list_runs()

    @app.get("/metrics")
    def metrics(_auth: None = Depends(require_auth)) -> dict[str, Any]:
        return active_checkpoint_ai.metrics.get_summary()

    @app.get("/api/health")
    def api_health(_auth: None = Depends(require_auth)) -> dict[str, Any]:
        try:
            return active_checkpoint_ai.health_checker.generate_diagnostic_report().to_dict()
        except Exception as exc:
            return {
                "overall_status": "unhealthy",
                "checks": [
                    {
                        "component": "health_checker",
                        "status": "error",
                        "message": str(exc),
                        "details": {},
                    }
                ],
                "recommendations": ["检查数据库是否由不完整备份恢复，必要时恢复到更新的备份。"],
            }

    @app.get("/api/console/snapshot")
    def console_snapshot(
        scenario_id: str | None = None,
        all_scenarios: bool = False,
        reason: str | None = None,
        _auth: None = Depends(require_auth),
    ) -> dict[str, Any]:
        return ConsoleReadModel(active_db_path).snapshot(
            scenario_id=scenario_id,
            allow_cross_scenario=all_scenarios,
            reason=reason,
        ).model_dump(mode="json")

    @app.get("/api/approvals")
    def list_approvals(
        scenario_id: str | None = None,
        _auth: None = Depends(require_auth),
    ) -> list[dict[str, Any]]:
        return [
            item.model_dump(mode="json")
            for item in ApprovalInbox(active_db_path).list_items(scenario_id=scenario_id)
        ]

    @app.get("/api/approvals/{approval_id}")
    def approval_detail(approval_id: str, _auth: None = Depends(require_auth)) -> dict[str, Any]:
        item = _approval_item(approval_id, active_db_path)
        if item is None:
            raise HTTPException(status_code=404, detail="Approval item not found.")
        return item

    @app.post("/api/approvals/{approval_id}/approve")
    def approve_item(
        approval_id: str,
        payload: dict[str, Any] | None = None,
        _auth: None = Depends(require_auth),
    ) -> dict[str, Any]:
        updated = ApprovalInbox(active_db_path).approve(
            approval_id,
            reason=str((payload or {}).get("comment", "")),
        )
        return {"id": approval_id, "updated": updated}

    @app.post("/api/approvals/{approval_id}/reject")
    def reject_item(
        approval_id: str,
        payload: dict[str, Any] | None = None,
        _auth: None = Depends(require_auth),
    ) -> dict[str, Any]:
        updated = ApprovalInbox(active_db_path).reject(
            approval_id,
            reason=str((payload or {}).get("comment", "")),
        )
        return {"id": approval_id, "updated": updated}

    @app.get("/api/runs")
    def api_runs(
        scenario_id: str | None = None,
        _auth: None = Depends(require_auth),
    ) -> list[dict[str, Any]]:
        scenarios = [scenario_id] if scenario_id else [scenario.id for scenario in ScenarioStore(active_db_path).list()]
        rows: list[dict[str, Any]] = []
        summaries = SummaryLogStore(active_db_path)
        for active_scenario_id in scenarios:
            rows.extend(summaries.query_by_scenario(active_scenario_id))
        return rows

    @app.get("/api/runs/{run_id}")
    def api_run_detail(run_id: str, _auth: None = Depends(require_auth)) -> dict[str, Any]:
        return ConsoleDashboard(active_db_path).run_report(run_id).model_dump(mode="json")

    @app.post("/api/runs")
    def api_trigger_run(
        payload: dict[str, Any],
        _auth: None = Depends(require_auth),
    ) -> dict[str, Any]:
        result = _scenario_runner(active_db_path).run_scenario(
            scenario_id=str(payload["scenario_id"]),
            task=str(payload["task"]),
            context=dict(payload.get("context", {})),
            config=dict(payload.get("config", {})),
        )
        return {
            "scenario_id": result.scenario_id,
            "run_id": result.run_id,
            "task": result.task,
            "status": result.status,
            "metrics": result.metrics,
            "value_summary": result.value_summary,
            "answer": result.answer,
        }

    @app.get("/api/backups")
    def list_backups(_auth: None = Depends(require_auth)) -> list[dict[str, Any]]:
        return [
            {**backup.model_dump(mode="json"), "path": str(backup.path)}
            for backup in BackupManager(active_db_path, active_backup_dir).list_backups()
        ]

    @app.post("/api/backups")
    def create_backup(
        payload: dict[str, Any] | None = None,
        _auth: None = Depends(require_auth),
    ) -> dict[str, Any]:
        backup = BackupManager(active_db_path, active_backup_dir).create_backup(
            label=str((payload or {}).get("label", "manual")),
        )
        return {**backup.model_dump(mode="json"), "path": str(backup.path)}

    @app.post("/api/backups/{backup_id}/restore")
    def restore_backup(backup_id: str, _auth: None = Depends(require_auth)) -> dict[str, Any]:
        return {"id": backup_id, "restored": BackupManager(active_db_path, active_backup_dir).restore(backup_id)}

    @app.get("/api/scenarios")
    def api_scenarios(_auth: None = Depends(require_auth)) -> list[dict[str, Any]]:
        return [scenario.model_dump(mode="json") for scenario in ScenarioStore(active_db_path).list()]

    @app.get("/api/scenarios/{scenario_id}")
    def api_scenario(scenario_id: str, _auth: None = Depends(require_auth)) -> dict[str, Any]:
        scenario = ScenarioStore(active_db_path).get(scenario_id)
        if scenario is None:
            raise HTTPException(status_code=404, detail="Scenario not found.")
        return scenario.model_dump(mode="json")

    @app.post("/api/scenarios/{scenario_id}/archive")
    def api_archive_scenario(
        scenario_id: str,
        payload: dict[str, Any] | None = None,
        _auth: None = Depends(require_auth),
    ) -> dict[str, Any]:
        archived = ScenarioStore(active_db_path).archive(
            scenario_id,
            reason=str((payload or {}).get("reason", "Archived from Web API.")),
        )
        return {"id": scenario_id, "archived": archived}

    @app.get("/api/adapters")
    def api_adapters(_auth: None = Depends(require_auth)) -> list[dict[str, Any]]:
        return [adapter.model_dump(mode="json") for adapter in _adapter_registry().describe()]

    setattr(app, "checkpoint_ai", active_checkpoint_ai)
    setattr(app, "auth", active_auth)
    return app


def serve_api(host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    """Serve the FastAPI control console API."""

    _uvicorn_server.run(
        "checkpoint_ai.api:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )


def _initial_tokens_from_env() -> list[str]:
    """Read comma-separated API tokens from environment."""

    raw = os.environ.get("CHECKPOINTAI_API_TOKENS") or os.environ.get("CHECKPOINTAI_API_TOKEN") or ""
    return [token.strip() for token in raw.split(",") if token.strip()]


def _fallback_app(checkpoint_ai: CheckpointAI, auth: BearerTokenAuth) -> FallbackApp:
    """Return a fallback route manifest when FastAPI is unavailable."""

    return FallbackApp(
        checkpoint_ai=checkpoint_ai,
        auth=auth,
        routes=[
            {"method": "GET", "path": "/health"},
            {"method": "GET", "path": "/runs"},
            {"method": "GET", "path": "/metrics"},
            {"method": "GET", "path": "/api/health"},
            {"method": "GET", "path": "/api/console/snapshot"},
            {"method": "GET", "path": "/api/approvals"},
            {"method": "GET", "path": "/api/runs"},
            {"method": "GET", "path": "/api/backups"},
            {"method": "GET", "path": "/api/scenarios"},
            {"method": "GET", "path": "/api/adapters"},
        ],
    )


def _adapter_registry() -> AdapterRegistry:
    """Return built-in adapters for API-triggered scenario runs."""

    registry = AdapterRegistry()
    registry.register(DummyAdapter())
    registry.register(OPCAgentAdapter())
    registry.register(QuantResearchDemoAdapter())
    return registry


def _scenario_registry(db_path: Path) -> ScenarioRegistry:
    """Load persisted scenarios into an in-memory registry."""

    registry = ScenarioRegistry()
    for scenario in ScenarioStore(db_path).list():
        registry.create(scenario)
    return registry


def _scenario_runner(db_path: Path) -> ScenarioRunner:
    """Build a scenario runner for Web API triggered runs."""

    return ScenarioRunner(
        scenarios=_scenario_registry(db_path),
        adapters=_adapter_registry(),
        raw_logs=RawLogStore(db_path),
        summary_logs=SummaryLogStore(db_path),
    )


def _approval_item(approval_id: str, db_path: Path) -> dict[str, Any] | None:
    """Return one approval item by id."""

    for item in ApprovalInbox(db_path).list_items():
        if item.source_id == approval_id:
            return {**item.model_dump(mode="json"), "detail": _approval_detail(approval_id, db_path)}
    return None


def _approval_detail(approval_id: str, db_path: Path) -> dict[str, Any] | None:
    """Return the full source object behind one approval item."""

    prompt_proposal = PromptProposalStore(db_path).get(approval_id)
    if prompt_proposal is not None:
        return prompt_proposal.model_dump(mode="json")

    generic_proposal = ProposalStore(db_path).get(approval_id)
    if generic_proposal is not None:
        return generic_proposal.model_dump(mode="json")

    recommendation = VersionRecommendationStore(db_path).get(approval_id)
    if recommendation is not None:
        return recommendation.model_dump(mode="json")

    parameter_suggestion = ParameterSuggestionStore(db_path).get(approval_id)
    if parameter_suggestion is not None:
        return parameter_suggestion.model_dump(mode="json")

    return None
