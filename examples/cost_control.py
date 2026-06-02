"""Cost control example.

Demonstrates how to set daily budgets and track spending.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from opc_os import OPCOS
from opc_os.observability.cost_tracker import CostTracker


async def main() -> None:
    """Set budget and track cost in real-time."""

    opc_os = OPCOS()
    cost_tracker = CostTracker()

    # 1. Set daily budget for each provider
    cost_tracker.set_budget('minimax', 50.0)
    cost_tracker.set_budget('openai', 30.0)

    print("Budgets set:")
    print(f"  minimax: $50.0/day")
    print(f"  openai: $30.0/day")

    # 2. Track token usage (input_tokens, output_tokens)
    cost_tracker.track('minimax', input_tokens=1000, output_tokens=500, business_line_id='test')
    cost_tracker.track('minimax', input_tokens=2000, output_tokens=1000, business_line_id='test')
    cost_tracker.track('openai', input_tokens=500, output_tokens=200, business_line_id='test')

    # 3. Check daily cost
    daily_minimax = cost_tracker.get_daily_cost('minimax', business_line_id='test')
    daily_openai = cost_tracker.get_daily_cost('openai', business_line_id='test')

    print(f"\nCurrent daily spending:")
    print(f"  minimax: ${daily_minimax:.2f}")
    print(f"  openai: ${daily_openai:.2f}")


if __name__ == '__main__':
    asyncio.run(main())
