"""First-party OPC demo adapter implemented through subprocess boundaries."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Literal

from loop_harness.adapter.base import (
    AgentAdapter,
    AgentRunRequest,
    AgentRunResult,
    latency_ms_since,
)
from loop_harness.adapter.capabilities import AdapterCapabilities, CapabilitySupport

DEFAULT_OPC_AGENT_DIR = Path("/Users/lemonsea/Desktop/mas/opc_agent")


class OPCAgentAdapter(AgentAdapter):
    """Run the current OPC demo through subprocess without importing its package."""

    @property
    def name(self) -> str:
        return "opc_agent_demo"

    @property
    def supported_task_types(self) -> list[str]:
        return ["content_pipeline", "generate_content", "run_demo"]

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Execute the demo process and normalize stdout into AgentRunResult."""

        start = time.perf_counter()
        command = self._resolve_command(request.config)
        cwd = Path(str(request.config.get("cwd", DEFAULT_OPC_AGENT_DIR)))
        payload = json.dumps(request.model_dump(mode="json"), ensure_ascii=False)
        env = os.environ.copy()
        env["LOOP_HARNESS_REQUEST_JSON"] = payload
        try:
            completed = subprocess.run(
                command,
                input=payload,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=float(request.config.get("timeout_seconds", 120.0)),
                check=False,
            )
        except subprocess.TimeoutExpired:
            return AgentRunResult(
                scenario_id=request.scenario_id,
                task=request.task,
                answer="OPC demo subprocess timed out.",
                metrics={"latency_ms": latency_ms_since(start)},
                value_summary="OPC demo子进程超时，不能作为有效样本。",
                status="failed",
                error_type="timeout",
            )

        latency_ms = latency_ms_since(start)
        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            return AgentRunResult(
                scenario_id=request.scenario_id,
                task=request.task,
                answer=completed.stdout.strip() or stderr or "OPC demo subprocess failed.",
                metrics={
                    "latency_ms": latency_ms,
                    "returncode": float(completed.returncode),
                    "stdout_chars": float(len(completed.stdout)),
                    "stderr_chars": float(len(completed.stderr)),
                },
                value_summary=f"OPC demo子进程失败，returncode={completed.returncode}，不能作为有效样本。",
                status="failed",
                error_type="subprocess_error",
            )

        return self._result_from_stdout(request, completed.stdout, latency_ms)

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            metrics_capture=CapabilitySupport.SUPPORTED,
            shadow_run=CapabilitySupport.SUPPORTED,
            notes={
                "shadow_run": (
                    "OPC demo runs through a subprocess boundary; shadow mode is represented by "
                    "request.config['shadow'] and does not mutate deployed LoopHarness prompts."
                )
            },
        )

    @staticmethod
    def _resolve_command(config: dict[str, Any]) -> list[str]:
        configured = config.get("command")
        if isinstance(configured, list) and all(isinstance(item, str) for item in configured):
            return configured
        if isinstance(configured, str) and configured.strip():
            return configured.split()
        python_bin = DEFAULT_OPC_AGENT_DIR / "venv" / "bin" / "python"
        if python_bin.exists():
            return [str(python_bin), "main.py"]
        return ["python", "main.py"]

    def _result_from_stdout(
        self,
        request: AgentRunRequest,
        stdout: str,
        latency_ms: int,
    ) -> AgentRunResult:
        parsed = self._parse_json_stdout(stdout)
        if parsed is not None:
            answer = str(parsed.get("answer", stdout.strip()))
            metrics = self._normalized_metrics(parsed.get("metrics", {}))
            metrics["latency_ms"] = latency_ms
            metrics["stdout_chars"] = float(len(stdout))
            value_summary = str(parsed.get("value_summary") or self._fallback_summary(stdout, metrics))
            status: Literal["success", "failed"] = (
                "success" if str(parsed.get("status", "success")) == "success" else "failed"
            )
            return AgentRunResult(
                scenario_id=request.scenario_id,
                task=request.task,
                answer=answer,
                metrics=metrics,
                value_summary=value_summary,
                status=status,
                error_type=None if status == "success" else "adapter_error",
            )

        metrics = {
            "latency_ms": float(latency_ms),
            "stdout_chars": float(len(stdout)),
            "line_count": float(len([line for line in stdout.splitlines() if line.strip()])),
            "has_final_content": 1.0 if "最终内容" in stdout else 0.0,
            "has_distribution_result": 1.0 if "分发结果" in stdout else 0.0,
        }
        return AgentRunResult(
            scenario_id=request.scenario_id,
            task=request.task,
            answer=stdout.strip(),
            metrics=metrics,
            value_summary=self._fallback_summary(stdout, metrics),
            status="success",
        )

    @staticmethod
    def _parse_json_stdout(stdout: str) -> dict[str, Any] | None:
        stripped = stdout.strip()
        if not stripped:
            return None
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            for line in reversed(stripped.splitlines()):
                try:
                    parsed = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue
            else:
                return None
        return parsed if isinstance(parsed, dict) else None

    @staticmethod
    def _normalized_metrics(value: object) -> dict[str, float]:
        if not isinstance(value, dict):
            return {}
        metrics: dict[str, float] = {}
        for key, raw in value.items():
            if isinstance(raw, int | float):
                metrics[str(key)] = float(raw)
        return metrics

    @staticmethod
    def _fallback_summary(stdout: str, metrics: dict[str, float]) -> str:
        chars = int(metrics.get("stdout_chars", len(stdout)))
        has_final = bool(metrics.get("has_final_content", 0.0))
        has_distribution = bool(metrics.get("has_distribution_result", 0.0))
        return (
            f"OPC demo通过subprocess返回{chars}字符输出，"
            f"最终内容={'有' if has_final else '未知'}，"
            f"分发结果={'有' if has_distribution else '未知'}。"
        )
