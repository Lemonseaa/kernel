"""Quant Context tools for factor research.

Provides:
- ScreenStocksTool: Multi-factor screening
- BacktestStrategyTool: Historical backtesting
- FactorAnalysisTool: Fama-French factor decomposition
- FactorResearchTemplate: Complete factor research workflow
"""

from checkpoint_ai.tools.quant.quant_context import (
    ScreenStocksTool,
    BacktestStrategyTool,
    FactorAnalysisTool,
)
from checkpoint_ai.tools.quant.factor_template import FactorResearchTemplate

__all__ = [
    "ScreenStocksTool",
    "BacktestStrategyTool",
    "FactorAnalysisTool",
    "FactorResearchTemplate",
]
