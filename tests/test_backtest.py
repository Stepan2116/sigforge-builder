"""
Unit tests for tools/backtest.py.

Validates strategy variant logic, metrics computation, and edge cases.
Run with `pytest tests/` from the repository root.
"""
from __future__ import annotations

import os
import sys

import pytest

# Make tools/ importable from tests/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "tools"))

from backtest import (  # noqa: E402
    STRATEGIES,
    compute_metrics,
    simulate,
    strat_as_recorded,
    strat_combined_patches,
    strat_filter_cheap,
    strat_filter_cheap_high_volume,
    strat_forecast_floor,
)


# ─── Fixtures ───────────────────────────────────────────────────────────

def _market(entry: float = 0.30,
            exit_price: float = 1.0,
            close_reason: str = "resolved",
            shares: float = 67,
            cost: float = 20,
            pnl: float = None,
            volume: float = 10000,
            market_id: str = "m1") -> dict:
    """Build a synthetic market dict matching real archive shape."""
    if pnl is None:
        pnl = round((exit_price - entry) * shares, 4)
    return {
        "city": "Testville",
        "city_name": "Testville",
        "date": "2026-05-01",
        "position": {
            "market_id": market_id,
            "entry_price": entry,
            "exit_price": exit_price,
            "close_reason": close_reason,
            "shares": shares,
            "cost": cost,
            "pnl": pnl,
            "status": "closed",
        },
        "all_outcomes": [
            {"market_id": market_id, "volume": volume, "bid": 0.30, "ask": 0.32},
        ],
    }


# ─── Strategy logic ─────────────────────────────────────────────────────

class TestStratAsRecorded:
    def test_passes_all_trades_through(self):
        market = _market()
        result = strat_as_recorded(market, market["position"])
        assert result["entry"] is True
        assert result["override_exit_price"] is None


class TestStratFilterCheap:
    def test_skips_below_threshold(self):
        market = _market(entry=0.15)
        result = strat_filter_cheap(market, market["position"])
        assert result["entry"] is False

    def test_passes_at_threshold(self):
        market = _market(entry=0.20)
        result = strat_filter_cheap(market, market["position"])
        assert result["entry"] is True

    def test_passes_above_threshold(self):
        market = _market(entry=0.50)
        result = strat_filter_cheap(market, market["position"])
        assert result["entry"] is True


class TestStratFilterCheapHighVolume:
    def test_skips_low_volume(self):
        market = _market(entry=0.30, volume=1000)
        result = strat_filter_cheap_high_volume(market, market["position"])
        assert result["entry"] is False

    def test_passes_high_volume(self):
        market = _market(entry=0.30, volume=10000)
        result = strat_filter_cheap_high_volume(market, market["position"])
        assert result["entry"] is True


class TestStratForecastFloor:
    def test_replaces_dump_below_floor(self):
        # Entry $0.30, exit $0.005 — dump well below entry × 0.50.
        market = _market(entry=0.30, exit_price=0.005, close_reason="forecast_changed")
        result = strat_forecast_floor(market, market["position"])
        assert result["entry"] is True
        assert result["override_exit_price"] == 0.30  # the proxy value
        assert result["override_reason"] == "forecast_floor_holdsim"

    def test_keeps_normal_forecast_change(self):
        # Forecast changed but exit $0.20 (above entry × 0.50 = $0.15)
        market = _market(entry=0.30, exit_price=0.20, close_reason="forecast_changed")
        result = strat_forecast_floor(market, market["position"])
        assert result["entry"] is True
        assert result["override_exit_price"] is None  # use recorded

    def test_does_not_apply_to_other_reasons(self):
        market = _market(entry=0.30, exit_price=0.05, close_reason="stop_loss")
        result = strat_forecast_floor(market, market["position"])
        assert result["override_exit_price"] is None


class TestStratCombinedPatches:
    def test_applies_both_floor_and_stop_cap(self):
        # Stop-loss far past -25%, should be capped at entry * 0.75.
        market = _market(entry=0.40, exit_price=0.10, close_reason="stop_loss")
        result = strat_combined_patches(market, market["position"])
        assert result["entry"] is True
        assert result["override_exit_price"] == pytest.approx(0.30)  # 0.40 * 0.75 (float)

    def test_skips_cheap_entries_first(self):
        market = _market(entry=0.10, exit_price=0.005, close_reason="forecast_changed")
        result = strat_combined_patches(market, market["position"])
        assert result["entry"] is False


# ─── Metrics ────────────────────────────────────────────────────────────

class TestComputeMetrics:
    def test_empty_input(self):
        m = compute_metrics([])
        assert m == {"n": 0}

    def test_all_wins(self):
        trades = [{"pnl": 1.0}, {"pnl": 2.0}, {"pnl": 0.5}]
        m = compute_metrics(trades)
        assert m["n"] == 3
        assert m["wins"] == 3
        assert m["losses"] == 0
        assert m["wr"] == 1.0
        assert m["total"] == 3.5
        assert m["max_dd"] == 0.0

    def test_all_losses(self):
        # Cumulative: [-1, -3]. Peak initialised from first cumulative value (-1),
        # so the recorded drawdown from that peak to the trough (-3) is 2.0.
        # The algorithm intentionally does not assume an implicit zero-baseline,
        # making it robust to strategies that begin with a profit before losing.
        trades = [{"pnl": -1.0}, {"pnl": -2.0}]
        m = compute_metrics(trades)
        assert m["wins"] == 0
        assert m["losses"] == 2
        assert m["wr"] == 0.0
        assert m["total"] == -3.0
        assert m["max_dd"] == 2.0

    def test_drawdown_after_runup(self):
        # cumulative: 5, 10, 5, 0
        trades = [{"pnl": 5}, {"pnl": 5}, {"pnl": -5}, {"pnl": -5}]
        m = compute_metrics(trades)
        assert m["max_dd"] == 10.0  # peak 10 → trough 0

    def test_sharpe_zero_when_no_variance(self):
        # All identical trades → stdev = 0 → Sharpe = 0 (handled gracefully).
        trades = [{"pnl": 1.0}, {"pnl": 1.0}, {"pnl": 1.0}]
        m = compute_metrics(trades)
        assert m["sharpe_pt"] == 0.0

    def test_sharpe_positive_for_winning_strategy(self):
        trades = [{"pnl": 1.0}, {"pnl": 2.0}, {"pnl": 1.5}, {"pnl": 0.5}]
        m = compute_metrics(trades)
        assert m["sharpe_pt"] > 0


# ─── End-to-end simulate ────────────────────────────────────────────────

class TestSimulate:
    def test_simulate_collects_trades(self):
        markets = [_market(), _market(market_id="m2"), _market(market_id="m3")]
        trades = simulate(markets, strat_as_recorded)
        assert len(trades) == 3

    def test_simulate_respects_filter(self):
        markets = [
            _market(entry=0.30, market_id="m1"),
            _market(entry=0.10, market_id="m2"),  # filtered
        ]
        trades = simulate(markets, strat_filter_cheap)
        assert len(trades) == 1
        assert trades[0]["entry"] == 0.30

    def test_simulate_applies_overrides(self):
        markets = [_market(entry=0.30, exit_price=0.005,
                           close_reason="forecast_changed", market_id="m1")]
        trades = simulate(markets, strat_forecast_floor)
        assert len(trades) == 1
        assert trades[0]["exit"] == 0.30
        assert trades[0]["reason"] == "forecast_floor_holdsim"

    def test_simulate_skips_open_positions(self):
        markets = [_market()]
        markets[0]["position"]["status"] = "open"
        trades = simulate(markets, strat_as_recorded)
        assert len(trades) == 0


# ─── Strategy registry ──────────────────────────────────────────────────

class TestStrategiesRegistry:
    def test_registry_contains_all_strategies(self):
        expected = {
            "as_recorded",
            "filter_cheap",
            "filter_cheap_high_volume",
            "forecast_floor",
            "combined_patches",
        }
        assert set(STRATEGIES.keys()) == expected

    def test_each_strategy_callable(self):
        market = _market()
        for name, fn in STRATEGIES.items():
            result = fn(market, market["position"])
            assert "entry" in result, f"{name} missing 'entry' in result"
