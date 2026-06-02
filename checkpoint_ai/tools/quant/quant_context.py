"""QuantContext MCP tools integration.

This module integrates QuantContext's factor research tools into CheckpointAI.

QuantContext provides:
- screen_stocks: Filter stocks by fundamentals, momentum, quality, technical signals
- backtest_strategy: Historical backtesting with rebalance loop engine
- factor_analysis: Fama-French five-factor decomposition

No API keys required. Uses Yahoo Finance public data.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from checkpoint_ai.tools.base import BaseTool


class ScreenStocksTool(BaseTool):
    """Screen stocks by multi-factor criteria."""

    name = "screen_stocks"
    description = "Filter stocks by fundamentals, momentum, quality, technical signals"

    def run(self, **kwargs: Any) -> dict:
        """Execute stock screening.

        Args:
            universe: sp500, nasdaq100, or russell2000
            screen_type: fundamental_screen, quality_screen, momentum_screen,
                        value_screen, factor_model, technical_signal, mean_reversion
            config: Screen-specific parameters (pe_lt, roe_gt, lookback_days, etc.)

        Returns:
            dict with screening results
        """
        try:
            from quantcontext.server import screen_stocks

            result_json = asyncio.run(screen_stocks(**kwargs))
            return json.loads(result_json)
        except Exception as e:
            return {"error": str(e)}


class BacktestStrategyTool(BaseTool):
    """Backtest a screening strategy over historical data."""

    name = "backtest_strategy"
    description = "Backtest screening strategy with historical data and rebalance"

    def run(self, **kwargs: Any) -> dict:
        """Execute strategy backtest.

        Args:
            stages: List of screening stages
            universe: sp500, nasdaq100, or russell2000
            rebalance: monthly, weekly, or daily
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), optional

        Returns:
            dict with backtest metrics and equity curve
        """
        try:
            from quantcontext.server import backtest_strategy

            result_json = asyncio.run(backtest_strategy(**kwargs))
            return json.loads(result_json)
        except Exception as e:
            return {"error": str(e)}


class FactorAnalysisTool(BaseTool):
    """Decompose strategy returns into Fama-French factors."""

    name = "factor_analysis"
    description = "Fama-French factor decomposition to identify alpha sources"

    def run(self, **kwargs: Any) -> dict:
        """Execute factor analysis.

        Args:
            equity_curve: List of equity curve values from backtest

        Returns:
            dict with factor loadings and alpha
        """
        try:
            from quantcontext.server import factor_analysis

            result_json = asyncio.run(factor_analysis(**kwargs))
            return json.loads(result_json)
        except Exception as e:
            return {"error": str(e)}
