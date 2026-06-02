"""Quick start example - create a business line and run a task."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from opc_os import Kernel
from opc_os.models import TaskSpec


async def main() -> None:
    """Create a business line and run a simple task."""

    # 1. Initialize kernel
    kernel = Kernel()

    # 2. Create a business line
    bl = kernel.create_business_line('content_business')
    print(f"Created business line: {bl.name} ({bl.id})")

    # 3. Create and run a task
    task_spec = TaskSpec(
        description='写一篇500字的文章介绍AI在内容创作中的应用'
    )

    run = await kernel.run(
        run=bl.id,
        tasks=[task_spec]
    )

    # 4. Check result
    print(f"Run state: {run.state.value}")
    print(f"Tasks count: {len(run.tasks)}")


if __name__ == '__main__':
    asyncio.run(main())
