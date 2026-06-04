"""Deterministic quant research demo adapter for Pre-V3 data runs."""

from __future__ import annotations

import math
import time

from checkpoint_ai.adapter.base import (
    AgentAdapter,
    AgentRunRequest,
    AgentRunResult,
    latency_ms_since,
)
from checkpoint_ai.adapter.capabilities import AdapterCapabilities, CapabilitySupport


class QuantResearchDemoAdapter(AgentAdapter):
    """Replayable rule-strategy backtest adapter with objective metrics."""

    @property
    def name(self) -> str:
        return "quant_research_demo"

    @property
    def supported_task_types(self) -> list[str]:
        return ["backtest_strategy", "quant_research"]

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Run a deterministic backtest and return comparable metrics."""

        start = time.perf_counter()
        symbol = str(request.context.get("symbol", "SPY")).upper()
        strategy_type = str(request.context.get("strategy_type", request.config.get("strategy_type", "moving_average")))
        prices = _synthetic_prices(symbol)
        signals = self._signals(strategy_type, prices, request.config)
        metrics = _backtest(prices, signals)
        metrics["latency_ms"] = float(latency_ms_since(start))
        metrics["sample_count"] = float(len(prices))
        answer = (
            f"Quant demo backtested {strategy_type} on {symbol}: "
            f"total_return={metrics['total_return']:.4f}, "
            f"max_drawdown={metrics['max_drawdown']:.4f}, "
            f"sharpe={metrics['sharpe']:.4f}, trades={int(metrics['trade_count'])}."
        )
        value_summary = (
            f"量化demo对{symbol}执行{strategy_type}回测，"
            f"收益={metrics['total_return']:.2%}，回撤={metrics['max_drawdown']:.2%}，"
            f"sharpe={metrics['sharpe']:.2f}，交易次数={int(metrics['trade_count'])}，"
            "可作为Pre-V3的可重复比较样本。"
        )
        return AgentRunResult(
            scenario_id=request.scenario_id,
            task=request.task,
            answer=answer,
            metrics=metrics,
            value_summary=value_summary,
            status="success",
        )

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            metrics_capture=CapabilitySupport.SUPPORTED,
            shadow_run=CapabilitySupport.SUPPORTED,
            continuous_params=CapabilitySupport.SUPPORTED,
        )

    def _signals(
        self,
        strategy_type: str,
        prices: list[float],
        config: dict[str, object],
    ) -> list[int]:
        if strategy_type == "rsi":
            return _rsi_signals(
                prices,
                _int_config(config, "rsi_period", 14),
                _float_config(config, "rsi_buy", 35.0),
            )
        if strategy_type == "momentum":
            return _momentum_signals(prices, _int_config(config, "lookback", 20))
        return _moving_average_signals(
            prices,
            _int_config(config, "fast_window", 10),
            _int_config(config, "slow_window", 30),
        )


def _synthetic_prices(symbol: str) -> list[float]:
    """Return deterministic, symbol-specific pseudo market data."""

    seed = sum(ord(char) for char in symbol)
    base = 100.0 + (seed % 30)
    prices: list[float] = []
    for day in range(260):
        trend = day * (0.045 + (seed % 7) * 0.002)
        cycle = math.sin(day / 9.0 + seed) * 1.8
        shock = math.sin(day / 23.0 + seed / 3.0) * 2.2
        price = max(10.0, base + trend + cycle + shock)
        prices.append(round(price, 4))
    return prices


def _moving_average_signals(prices: list[float], fast_window: int, slow_window: int) -> list[int]:
    fast_window = max(2, fast_window)
    slow_window = max(fast_window + 1, slow_window)
    signals: list[int] = []
    for index, _price in enumerate(prices):
        if index < slow_window:
            signals.append(0)
            continue
        fast = _mean(prices[index - fast_window + 1 : index + 1])
        slow = _mean(prices[index - slow_window + 1 : index + 1])
        signals.append(1 if fast > slow else 0)
    return signals


def _momentum_signals(prices: list[float], lookback: int) -> list[int]:
    lookback = max(2, lookback)
    signals: list[int] = []
    for index, price in enumerate(prices):
        signals.append(1 if index >= lookback and price > prices[index - lookback] else 0)
    return signals


def _rsi_signals(prices: list[float], period: int, buy_threshold: float) -> list[int]:
    period = max(2, period)
    signals: list[int] = []
    for index, _price in enumerate(prices):
        if index < period:
            signals.append(0)
            continue
        changes = [prices[i] - prices[i - 1] for i in range(index - period + 1, index + 1)]
        gains = [change for change in changes if change > 0]
        losses = [-change for change in changes if change < 0]
        avg_gain = _mean(gains) if gains else 0.0
        avg_loss = _mean(losses) if losses else 0.0001
        rsi = 100.0 - (100.0 / (1.0 + (avg_gain / avg_loss)))
        signals.append(1 if rsi < buy_threshold else 0)
    return signals


def _backtest(prices: list[float], signals: list[int]) -> dict[str, float]:
    strategy_returns: list[float] = []
    benchmark_returns: list[float] = []
    trades = 0
    previous_signal = 0
    for index in range(1, len(prices)):
        daily_return = (prices[index] - prices[index - 1]) / prices[index - 1]
        signal = signals[index - 1]
        strategy_returns.append(daily_return * signal)
        benchmark_returns.append(daily_return)
        if signal != previous_signal:
            trades += 1
        previous_signal = signal
    equity = _equity_curve(strategy_returns)
    benchmark_equity = _equity_curve(benchmark_returns)
    total_return = equity[-1] - 1.0
    benchmark_return = benchmark_equity[-1] - 1.0
    max_drawdown = _max_drawdown(equity)
    sharpe = _sharpe(strategy_returns)
    win_rate = _win_rate(strategy_returns)
    annual_return = (1.0 + total_return) ** (252.0 / len(strategy_returns)) - 1.0
    stability_score = max(0.0, min(1.0, (sharpe / 3.0) + (1.0 - max_drawdown) * 0.25))
    return {
        "total_return": round(total_return, 6),
        "annual_return": round(annual_return, 6),
        "benchmark_return": round(benchmark_return, 6),
        "excess_return": round(total_return - benchmark_return, 6),
        "max_drawdown": round(max_drawdown, 6),
        "sharpe": round(sharpe, 6),
        "win_rate": round(win_rate, 6),
        "trade_count": float(trades),
        "stability_score": round(stability_score, 6),
    }


def _equity_curve(returns: list[float]) -> list[float]:
    equity = [1.0]
    for value in returns:
        equity.append(equity[-1] * (1.0 + value))
    return equity


def _max_drawdown(equity: list[float]) -> float:
    peak = equity[0]
    drawdown = 0.0
    for value in equity:
        peak = max(peak, value)
        drawdown = max(drawdown, (peak - value) / peak)
    return drawdown


def _sharpe(returns: list[float]) -> float:
    if not returns:
        return 0.0
    mean = _mean(returns)
    variance = _mean([(value - mean) ** 2 for value in returns])
    std = math.sqrt(variance)
    return 0.0 if std == 0 else (mean / std) * math.sqrt(252.0)


def _win_rate(returns: list[float]) -> float:
    active = [value for value in returns if value != 0]
    if not active:
        return 0.0
    wins = [value for value in active if value > 0]
    return len(wins) / len(active)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _int_config(config: dict[str, object], key: str, default: int) -> int:
    value = config.get(key, default)
    if isinstance(value, int | float | str):
        return int(value)
    return default


def _float_config(config: dict[str, object], key: str, default: float) -> float:
    value = config.get(key, default)
    if isinstance(value, int | float | str):
        return float(value)
    return default
