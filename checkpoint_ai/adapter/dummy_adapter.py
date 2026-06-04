"""Dummy stock signal adapter used to validate the V2.1 contract."""

from __future__ import annotations

import time

from checkpoint_ai.adapter.base import (
    AgentAdapter,
    AgentRunRequest,
    AgentRunResult,
    latency_ms_since,
)
from checkpoint_ai.adapter.capabilities import AdapterCapabilities, CapabilitySupport


class DummyAdapter(AgentAdapter):
    """Deterministic stock signal analysis adapter."""

    @property
    def name(self) -> str:
        return "dummy_stock_signal"

    @property
    def supported_task_types(self) -> list[str]:
        return ["analyze_signal"]

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Return a deterministic, explainable stock signal result."""

        start = time.perf_counter()
        symbol = str(request.context.get("symbol", "UNKNOWN")).upper()
        if request.config.get("force_failure"):
            return AgentRunResult(
                scenario_id=request.scenario_id,
                task=request.task,
                answer=f"Dummy adapter failed while analyzing {symbol}.",
                metrics={"signal_quality": 0.0, "confidence": 0.0, "latency_ms": latency_ms_since(start)},
                value_summary=(
                    f"本次运行分析了{symbol}，adapter failed，"
                    "signal_quality=0.0，confidence=0.0，不能作为有效baseline样本。"
                ),
                status="failed",
                error_type="adapter_error",
            )

        signal_quality = 0.9 if request.config.get("shadow") else 0.82
        confidence = 0.79 if request.config.get("shadow") else 0.76
        latency_ms = latency_ms_since(start)
        answer = (
            f"{symbol} dummy signal is mildly bullish. Momentum and quality inputs are aligned, "
            "but confidence remains moderate because this is a deterministic demo adapter."
        )
        value_summary = (
            f"本次运行分析了{symbol}，输出温和看多的股票信号，"
            f"signal_quality={signal_quality}，confidence={confidence}，"
            "可作为后续prompt/version/shadow对比的baseline样本。"
        )
        return AgentRunResult(
            scenario_id=request.scenario_id,
            task=request.task,
            answer=answer,
            metrics={
                "signal_quality": signal_quality,
                "confidence": confidence,
                "latency_ms": latency_ms,
            },
            value_summary=value_summary,
            status="success",
        )

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            metrics_capture=CapabilitySupport.SUPPORTED,
            shadow_run=CapabilitySupport.SUPPORTED,
        )
