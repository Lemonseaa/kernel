"""Business line isolation example.

Demonstrates how BusinessLines keep data and context separate.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kernel import Kernel
from kernel.models import TaskSpec


async def main() -> None:
    """Create two isolated business lines and verify separation."""

    kernel = Kernel()

    # 1. Create two business lines
    bl_a = kernel.create_business_line('course_business')
    bl_b = kernel.create_business_line('website_business')

    print(f"Business A: {bl_a.name} ({bl_a.id})")
    print(f"Business B: {bl_b.name} ({bl_b.id})")

    # 2. Run tasks in each business line
    task_a = TaskSpec(description='发布新课程公告')
    task_b = TaskSpec(description='更新网站首页')

    run_a = await kernel.run(run=bl_a.id, tasks=[task_a])
    run_b = await kernel.run(run=bl_b.id, tasks=[task_b])

    # 3. Verify isolation - each run belongs to its business line
    print(f"\nRun A belongs to: {run_a.business_line_id}")
    print(f"Run B belongs to: {run_b.business_line_id}")

    # 4. Verify they are different
    assert run_a.business_line_id != run_b.business_line_id, "Business lines should be isolated!"

    print("\nIsolation verified: runs belong to different business lines")


if __name__ == '__main__':
    asyncio.run(main())
