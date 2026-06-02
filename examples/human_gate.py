"""Human Gate example.

Demonstrates how approval requests work.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from opc_os import Kernel
from opc_os.control.gate import HumanApprovalGate


async def main() -> None:
    """Create a human approval gate."""

    kernel = Kernel()

    # 1. Create a business line
    bl = kernel.create_business_line('content_business')

    # 2. Create an approval gate with event bus
    gate = HumanApprovalGate(event_bus=kernel.event_bus)

    # 3. Check if gate is subscribed to cost events
    print(f"Approval gate created for business line: {bl.id}")

    # 4. Get pending approvals
    pending = gate.pending_requests()
    print(f"Pending approval requests: {len(pending)}")


if __name__ == '__main__':
    asyncio.run(main())
