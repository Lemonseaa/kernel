"""V2.10 Pre-V3 data contract hardening tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.metrics import (
    MetricCategory,
    MetricDirection,
    MetricSchema,
    MetricSchemaRegistry,
)
from checkpoint_ai.policy import PolicyLevel, ScenarioPolicy
from checkpoint_ai.prompt import (
    PromptPatch,
    PromptProposal,
    PromptSlot,
    Proposal,
    ProposalKind,
    ProposalPatch,
    ProposalStatus,
    ProposalStore,
    ProposalTargetType,
)
from checkpoint_ai.shadow import MetricComparator, RunKind


class V210PreV3HardeningTest(unittest.TestCase):
    """Validate the data contracts V3 needs before learning starts."""

    def test_metric_schema_filters_business_metrics_and_respects_direction(self) -> None:
        registry = MetricSchemaRegistry.default_quant()
        comparator = MetricComparator(registry)

        result = comparator.compare(
            baseline_metrics={
                "sharpe": 1.2,
                "max_drawdown": 0.18,
                "latency_ms": 12.0,
                "sample_count": 260.0,
            },
            candidate_metrics={
                "sharpe": 1.5,
                "max_drawdown": 0.14,
                "latency_ms": 20.0,
                "sample_count": 260.0,
            },
            run_kind=RunKind.SYNTHETIC,
            provenance={
                "data_source": "synthetic_prices",
                "generated_by": "quant_research_demo",
                "seed": "SPY",
                "sample_count": 260,
            },
        )

        self.assertEqual(result.run_kind, RunKind.SYNTHETIC)
        self.assertIn("sharpe", result.business_metric_diffs)
        self.assertIn("max_drawdown", result.business_metric_diffs)
        self.assertNotIn("latency_ms", result.business_metric_diffs)
        self.assertNotIn("sample_count", result.business_metric_diffs)
        self.assertGreater(result.metric_evaluations["sharpe"].normalized_change, 0)
        self.assertGreater(result.metric_evaluations["max_drawdown"].normalized_change, 0)
        self.assertTrue(result.improved)
        self.assertIn("synthetic", result.summary)
        self.assertEqual(result.provenance["data_source"], "synthetic_prices")

    def test_generic_strategy_proposal_persists_parameter_patch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ProposalStore(Path(tmp) / "v210.db")
            proposal = Proposal(
                scenario_id="quant-demo",
                proposal_kind=ProposalKind.STRATEGY,
                target_type=ProposalTargetType.STRATEGY_PARAM,
                target_id="moving_average.fast_window",
                patch=ProposalPatch(
                    operation="replace",
                    before={"fast_window": 8},
                    after={"fast_window": 10},
                ),
                reason="30次V2.9数据表明小幅参数调整需要独立于prompt提案表达。",
                expected_metric="sharpe",
                metadata={"magnitude": 0.08, "run_kind": "synthetic"},
            )

            proposal_id = store.create(proposal)
            loaded = store.get(proposal_id)
            by_status = store.list(status=ProposalStatus.PROPOSED)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.proposal_kind, ProposalKind.STRATEGY)
        self.assertEqual(loaded.target_type, ProposalTargetType.STRATEGY_PARAM)
        self.assertEqual(loaded.patch.after["fast_window"], 10)
        self.assertEqual([item.id for item in by_status], [proposal_id])

    def test_prompt_proposal_can_be_converted_to_generic_proposal(self) -> None:
        prompt_proposal = PromptProposal(
            scenario_id="content-demo",
            agent_id="writer",
            patch=PromptPatch(
                slot=PromptSlot.STYLE,
                operation="replace",
                before="正式",
                after="更口语",
            ),
            reason="提升小红书可读性。",
            expected_metric="readability",
        )

        generic = Proposal.from_prompt_proposal(prompt_proposal)

        self.assertEqual(generic.id, prompt_proposal.id)
        self.assertEqual(generic.proposal_kind, ProposalKind.PROMPT)
        self.assertEqual(generic.target_type, ProposalTargetType.PROMPT_SLOT)
        self.assertEqual(generic.target_id, "writer.style")
        self.assertEqual(generic.patch.after, "更口语")

    def test_policy_uses_proposal_type_run_kind_and_magnitude(self) -> None:
        policy = ScenarioPolicy()
        small_parameter = Proposal(
            scenario_id="quant-demo",
            proposal_kind=ProposalKind.STRATEGY,
            target_type=ProposalTargetType.STRATEGY_PARAM,
            target_id="moving_average.fast_window",
            patch=ProposalPatch(operation="replace", before=8, after=10),
            reason="小幅参数调整。",
            expected_metric="sharpe",
            metadata={"magnitude": 0.08, "run_kind": "synthetic"},
        )
        strategy_switch = Proposal(
            scenario_id="quant-demo",
            proposal_kind=ProposalKind.STRATEGY,
            target_type=ProposalTargetType.ADAPTER_CONFIG,
            target_id="strategy_type",
            patch=ProposalPatch(operation="replace", before="moving_average", after="rsi"),
            reason="切换策略类型。",
            expected_metric="sharpe",
            metadata={"magnitude": 0.45, "run_kind": "historical"},
        )
        live_deployment = Proposal(
            scenario_id="quant-demo",
            proposal_kind=ProposalKind.DEPLOYMENT,
            target_type=ProposalTargetType.DEPLOYMENT,
            target_id="live_strategy",
            patch=ProposalPatch(operation="replace", before="paper", after="live"),
            reason="准备实盘部署。",
            expected_metric="risk_adjusted_return",
            metadata={"run_kind": "live"},
        )

        self.assertEqual(policy.evaluate_proposal(small_parameter).level, PolicyLevel.AUTO)
        self.assertEqual(policy.evaluate_proposal(strategy_switch).level, PolicyLevel.APPROVAL)
        self.assertEqual(policy.evaluate_proposal(live_deployment).level, PolicyLevel.BLOCKED)

    def test_custom_metric_schema_can_mark_guardrail_violation(self) -> None:
        registry = MetricSchemaRegistry(
            [
                MetricSchema(
                    name="max_drawdown",
                    direction=MetricDirection.LOWER,
                    category=MetricCategory.GUARDRAIL,
                    weight=1.0,
                    threshold=0.2,
                    is_guardrail=True,
                )
            ]
        )
        result = MetricComparator(registry).compare(
            baseline_metrics={"max_drawdown": 0.18},
            candidate_metrics={"max_drawdown": 0.25},
            run_kind=RunKind.HISTORICAL,
            provenance={"data_source": "fixture"},
        )

        self.assertFalse(result.improved)
        self.assertEqual(result.guardrail_violations, ["max_drawdown"])


if __name__ == "__main__":
    unittest.main()
