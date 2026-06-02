"""Quant factor research template.

This template provides a complete factor research workflow using QuantContext tools.
"""

from typing import Any, cast

from checkpoint_ai.tools.quant.quant_context import (
    BacktestStrategyTool,
    FactorAnalysisTool,
    ScreenStocksTool,
)


class FactorResearchTemplate:
    """Template for quantitative factor research workflow.

    Workflow:
    1. Screen stocks by factor criteria
    2. Backtest the screening strategy
    3. Analyze factor decomposition
    4. Human approval at each stage
    """

    def __init__(self) -> None:
        self.screen_tool = ScreenStocksTool()
        self.backtest_tool = BacktestStrategyTool()
        self.factor_tool = FactorAnalysisTool()

    def screen(
        self,
        universe: str = "sp500",
        screen_type: str = "fundamental_screen",
        config: dict | None = None,
    ) -> dict[Any, Any]:
        """Screen stocks by factor criteria.

        Args:
            universe: sp500, nasdaq100, or russell2000
            screen_type: fundamental_screen, quality_screen, momentum_screen,
                        value_screen, factor_model, technical_signal, mean_reversion
            config: Screen parameters (pe_lt, roe_gt, etc.)

        Returns:
            Screening results with ranked candidates
        """
        if config is None:
            config = {}

        return cast(
            dict[Any, Any],
            self.screen_tool.run(
                universe=universe,
                screen_type=screen_type,
                config=config,
            ),
        )

    def backtest(
        self,
        stages: list[dict[Any, Any]],
        universe: str = "sp500",
        rebalance: str = "monthly",
        start_date: str = "2022-01-01",
        end_date: str | None = None,
    ) -> dict[Any, Any]:
        """Backtest screening strategy.

        Args:
            stages: List of screening stages
            universe: sp500, nasdaq100, or russell2000
            rebalance: monthly, weekly, or daily
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), optional

        Returns:
            Backtest results with metrics and equity curve
        """
        kwargs = {
            "stages": stages,
            "universe": universe,
            "rebalance": rebalance,
            "start_date": start_date,
        }
        if end_date:
            kwargs["end_date"] = end_date

        return cast(dict[Any, Any], self.backtest_tool.run(**kwargs))

    def analyze_factor(self, equity_curve: list[float]) -> dict[Any, Any]:
        """Analyze factor decomposition.

        Args:
            equity_curve: List of equity curve values from backtest

        Returns:
            Factor analysis with alpha and factor loadings
        """
        return cast(dict[Any, Any], self.factor_tool.run(equity_curve=equity_curve))

    def full_research(
        self,
        universe: str = "sp500",
        screen_type: str = "fundamental_screen",
        config: dict | None = None,
        rebalance: str = "monthly",
        start_date: str = "2022-01-01",
    ) -> dict[Any, Any]:
        """Run complete factor research workflow.

        Args:
            universe: sp500, nasdaq100, or russell2000
            screen_type: Type of screening
            config: Screen parameters
            rebalance: Rebalance frequency
            start_date: Backtest start date

        Returns:
            Complete research results
        """
        # Step 1: Screen
        screen_result = self.screen(universe, screen_type, config)
        if "error" in screen_result:
            return {"error": f"Screen failed: {screen_result['error']}"}

        # Step 2: Backtest
        stages = [
            {
                "order": 1,
                "type": "screen",
                "skill": screen_type,
                "config": config or {},
            }
        ]
        backtest_result = self.backtest(
            stages=stages,
            universe=universe,
            rebalance=rebalance,
            start_date=start_date,
        )
        if "error" in backtest_result:
            return {"error": f"Backtest failed: {backtest_result['error']}"}

        # Step 3: Factor analysis
        equity_curve = backtest_result.get("full_equity_curve", [])
        factor_result = self.analyze_factor(equity_curve)
        if "error" in factor_result:
            return {"error": f"Factor analysis failed: {factor_result['error']}"}

        return {
            "screen": screen_result,
            "backtest": backtest_result,
            "factor_analysis": factor_result,
        }
