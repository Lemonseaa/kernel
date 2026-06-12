"""V2.7 first demo adapter tests."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from loop_harness.adapter import AgentRunRequest, OPCAgentAdapter
from loop_harness.logs import RawLogStore
from tests.helpers import project_root


class V27OPCAgentAdapterTest(unittest.TestCase):
    """Validate first-party demo adapter without importing the demo package."""

    def test_opc_agent_adapter_calls_demo_by_subprocess_with_structured_io(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = self._write_fake_opc_agent(Path(tmp))
            adapter = OPCAgentAdapter()

            result = adapter.run(
                AgentRunRequest(
                    scenario_id="opc-demo",
                    task="content_pipeline",
                    context={"topic": "AI内容增长", "platform": "xiaohongshu"},
                    config={"command": [sys.executable, str(script)], "cwd": tmp},
                )
            )

        self.assertEqual(result.status, "success")
        self.assertIn("content_pipeline", result.answer)
        self.assertEqual(result.metrics["content_quality"], 0.91)
        self.assertGreater(result.metrics["stdout_chars"], 0)
        self.assertIn("OPC demo", result.value_summary)

    def test_opc_agent_adapter_falls_back_from_plain_stdout_to_structured_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "plain_opc.py"
            script.write_text(
                "import sys\n"
                "_ = sys.stdin.read()\n"
                "print('最终内容：小红书内容草稿')\n"
                "print('分发结果：skipped')\n",
                encoding="utf-8",
            )
            adapter = OPCAgentAdapter()

            result = adapter.run(
                AgentRunRequest(
                    scenario_id="opc-demo",
                    task="content_pipeline",
                    context={"topic": "AI内容增长"},
                    config={"command": [sys.executable, str(script)], "cwd": tmp},
                )
            )

        self.assertEqual(result.status, "success")
        self.assertIn("最终内容", result.answer)
        self.assertEqual(result.metrics["has_final_content"], 1.0)
        self.assertTrue(result.value_summary)

    def test_cli_and_report_show_demo_adapter_run_and_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v27.db"
            script = self._write_fake_opc_agent(Path(tmp))
            adapter_config = json.dumps(
                {"command": [sys.executable, str(script)], "cwd": tmp},
                ensure_ascii=False,
            )

            self._run(
                db_path,
                "scenario",
                "create",
                "--id",
                "opc-demo",
                "--name",
                "OPC Demo",
                "--description",
                "First demo adapter",
                "--adapter",
                "opc_agent_demo",
                "--adapter-config-json",
                adapter_config,
            )
            adapter_run = self._run(
                db_path,
                "adapter",
                "run",
                "--scenario-id",
                "opc-demo",
                "--task",
                "content_pipeline",
                "--context-json",
                '{"topic": "AI内容增长"}',
            )
            report = self._run(db_path, "report", "latest")
            scenario_show = self._run(db_path, "scenario", "show", "opc-demo")
            logs = RawLogStore(db_path).query_by_scenario("opc-demo")

        self.assertIn("Adapter Run Report", adapter_run.stdout)
        self.assertIn("opc_agent_demo", scenario_show.stdout)
        self.assertIn("content_quality", adapter_run.stdout)
        self.assertIn("OPC demo", report.stdout)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["result"]["metrics"]["content_quality"], 0.91)

    @staticmethod
    def _write_fake_opc_agent(root: Path) -> Path:
        script = root / "fake_opc_agent.py"
        script.write_text(
            "import json, os, sys\n"
            "request = json.loads(sys.stdin.read())\n"
            "env_request = json.loads(os.environ['LOOP_HARNESS_REQUEST_JSON'])\n"
            "assert request['task'] == env_request['task']\n"
            "topic = request['context'].get('topic', 'unknown')\n"
            "print(json.dumps({\n"
            "  'answer': f\"OPC demo handled {request['task']} for {topic}\",\n"
            "  'metrics': {'content_quality': 0.91, 'topic_len': len(topic)},\n"
            "  'value_summary': f'OPC demo生成了{topic}内容，并返回可评估metrics。',\n"
            "  'status': 'success'\n"
            "}, ensure_ascii=False))\n",
            encoding="utf-8",
        )
        return script

    @staticmethod
    def _run(db_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
        root = project_root()
        result = subprocess.run(
            ["./loopharness", "--db", str(db_path), *args],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr or result.stdout)
        return result


if __name__ == "__main__":
    unittest.main()
