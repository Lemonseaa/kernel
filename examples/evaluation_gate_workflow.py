"""Evaluation gate workflow example."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from opc_os import Kernel
from opc_os.models import TaskSpec


async def main() -> None:
    """Run a small workflow with evaluation enabled."""

    kernel = Kernel()
    run = await kernel.run(
        "生成高质量内容",
        [
            TaskSpec(
                description=(
                    "AI内容质量检查实战\n\n"
                    "首先说明发布前质量检查的价值，避免低质量草稿进入分发。"
                    "其次给出标题、正文和平台格式三步检查法。"
                    "最后用分数和建议决定是否改写。 #AI #内容"
                    + "这个内容质量检查流程可以复用到选题、写作、审核和分发环节。" * 8
                ),
                evaluation_required=True,
                evaluation_platform="xiaohongshu",
                min_score=55.0,
            )
        ],
    )
    task = run.tasks[0]
    print(f"run={run.state.value}")
    print(f"task={task.state.value}")
    print(f"evaluation={task.metadata.get('evaluation')}")


if __name__ == "__main__":
    asyncio.run(main())
