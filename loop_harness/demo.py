"""Demo data seeders for operator-facing console validation."""

from __future__ import annotations

from pathlib import Path

from loop_harness.adapter import AdapterRegistry, DummyAdapter
from loop_harness.console import BackupManager, CostEvent, CostEventStore
from loop_harness.logs import RawLogStore, SummaryLogStore
from loop_harness.prompt import (
    PromptPatch,
    PromptProposal,
    PromptProposalStore,
    PromptSlot,
    PromptVersionStore,
)
from loop_harness.scenario import Scenario, ScenarioRegistry, ScenarioRunner, ScenarioStore


def seed_console_demo(db_path: str | Path, backup_dir: str | Path | None = None) -> dict[str, object]:
    """Seed one scenario, one run, one approval, one cost event, and one backup."""

    active_db_path = Path(db_path)
    active_backup_dir = Path(backup_dir or active_db_path.parent / "backups")
    scenario = Scenario(
        id="demo-quant",
        name="Demo Quant Scenario",
        description="Console demo scenario for validating operator workflows.",
        adapter_type="dummy_stock_signal",
        business_line_id="demo-trading",
        metadata={"domain_tags": ["quant", "demo"]},
    )
    ScenarioStore(active_db_path).save(scenario)
    PromptVersionStore(active_db_path).save_version(
        scenario_id=scenario.id,
        agent_id="researcher",
        slots={
            PromptSlot.ROLE: "You are a cautious quant research analyst.",
            PromptSlot.GOAL: "Generate evidence-backed signal analysis.",
            PromptSlot.CONSTRAINTS: "Do not recommend live deployment from demo data.",
            PromptSlot.OUTPUT_FORMAT: "Plain text with metrics summary.",
            PromptSlot.STYLE: "Concise, operational, evidence-first.",
            PromptSlot.EXAMPLES: "SPY: mildly bullish, confidence 0.76.",
            PromptSlot.TOOLS_POLICY: "Use only deterministic demo inputs.",
        },
        reason="Seed console demo prompt snapshot.",
    )
    proposal = PromptProposal(
        scenario_id=scenario.id,
        agent_id="researcher",
        patch=PromptPatch(
            slot=PromptSlot.OUTPUT_FORMAT,
            operation="replace",
            before="Plain text with metrics summary.",
            after="Structured JSON with answer, metrics, and value_summary.",
        ),
        reason="Make console approval detail easier to evaluate.",
        expected_metric="signal_quality",
        metadata={"awaiting_human_confirmation": True, "seeded": True},
    )
    PromptProposalStore(active_db_path).create(proposal)
    registry = ScenarioRegistry()
    registry.create(scenario)
    adapters = AdapterRegistry()
    adapters.register(DummyAdapter())
    result = ScenarioRunner(
        scenarios=registry,
        adapters=adapters,
        raw_logs=RawLogStore(active_db_path),
        summary_logs=SummaryLogStore(active_db_path),
    ).run_scenario(
        scenario_id=scenario.id,
        task="analyze_signal",
        context={"symbol": "SPY"},
        config={},
    )
    CostEventStore(active_db_path).record(
        CostEvent(
            scenario_id=scenario.id,
            business_line_id="demo-trading",
            provider="demo",
            input_tokens=120,
            output_tokens=80,
            estimated_cost=0.01,
        )
    )
    backup = BackupManager(active_db_path, active_backup_dir).create_backup(label="seed-console")
    return {
        "scenario_id": scenario.id,
        "run_id": result.run_id,
        "proposal_id": proposal.id,
        "backup_id": backup.id,
    }
