#!/usr/bin/env python3
"""
backtest.py — Strategy variant replay on historical Polymarket data.

Reads archived market files (each containing position + resolution outcome +
forecast/market snapshot timeline) and replays hypothetical strategy variants
against them. Computes per-variant performance metrics (trades, win rate,
total PnL, max drawdown, Sharpe-per-trade).

The tool is designed to validate or falsify proposed strategy patches before
deployment. A typical workflow:

    1. Identify a hypothesis ("ban entries < $0.20 will save losses").
    2. Implement the hypothesis as a strategy function in this file.
    3. Run against archived data covering the prior month.
    4. Compare the variant's metrics against `as_recorded` baseline.
    5. Promote to live only if metrics improve and rationale holds.

The backtester is intentionally a tool, not an oracle. See section 6 of
docs/METHODOLOGY.md for the philosophical framing — backtesting is for
falsification, not pattern fishing.

Usage:
    python3 backtest.py /path/to/markets [/path/to/markets2 ...]
    python3 backtest.py --strategy combined_patches /path/to/markets

Strategy function contract:
    def strategy_fn(market: dict, position: dict) -> dict:
        return {
            "entry": bool,                       # whether to take the trade
            "override_exit_price": float | None, # replace recorded exit price
            "override_reason": str | None,       # tag for audit
        }
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from glob import glob
from statistics import mean, pstdev
from typing import Any, Callable, Optional


# ─── Data loading ───────────────────────────────────────────────────────

def load_markets(paths: list[str]) -> list[dict[str, Any]]:
    """Load all market JSON files from given directories."""
    markets: list[dict[str, Any]] = []
    for path in paths:
        for filepath in sorted(glob(os.path.join(path, "*.json"))):
            try:
                with open(filepath) as f:
                    data = json.load(f)
                data["_source"] = path
                data["_file"] = os.path.basename(filepath)
                markets.append(data)
            except (OSError, json.JSONDecodeError) as exc:
                print(f"WARN: failed to load {filepath}: {exc}", file=sys.stderr)
    return markets


def has_closed_position(market: dict[str, Any]) -> bool:
    pos = market.get("position")
    return pos is not None and pos.get("status") == "closed"


# ─── Strategy variants ──────────────────────────────────────────────────
# Each strategy takes (market, position) and returns a decision dict.

def strat_as_recorded(market: dict, pos: dict) -> dict:
    """Baseline — replay exactly what happened."""
    return {"entry": True, "override_exit_price": None, "override_reason": None}


def strat_filter_cheap(market: dict, pos: dict) -> dict:
    """Skip entries below $0.20 — empirically lottery-grade losers."""
    if pos.get("entry_price", 1.0) < 0.20:
        return {"entry": False}
    return {"entry": True, "override_exit_price": None, "override_reason": None}


def strat_filter_cheap_high_volume(market: dict, pos: dict) -> dict:
    """Filter cheap + require bucket volume ≥ $5,000."""
    if pos.get("entry_price", 1.0) < 0.20:
        return {"entry": False}
    market_id = pos.get("market_id")
    volume = 0.0
    for outcome in market.get("all_outcomes", []):
        if outcome.get("market_id") == market_id:
            volume = outcome.get("volume", 0)
            break
    if volume < 5000:
        return {"entry": False}
    return {"entry": True, "override_exit_price": None, "override_reason": None}


def strat_forecast_floor(market: dict, pos: dict) -> dict:
    """Replace forecast_changed dumps below entry × 0.50 with proxy
    hold-to-resolution (50/50 outcome assumption → exit_price = $0.30)."""
    entry = pos.get("entry_price", 1.0)
    if entry < 0.20:
        return {"entry": False}
    exit_price = pos.get("exit_price", 0)
    reason = pos.get("close_reason", "")
    if reason == "forecast_changed" and exit_price < entry * 0.50:
        return {
            "entry": True,
            "override_exit_price": 0.30,
            "override_reason": "forecast_floor_holdsim",
        }
    return {"entry": True, "override_exit_price": None, "override_reason": None}


def strat_combined_patches(market: dict, pos: dict) -> dict:
    """Filter cheap + forecast floor + cap stop_loss exits at entry × 0.75.
    Models the current live patches on coldmath_bot."""
    entry = pos.get("entry_price", 1.0)
    if entry < 0.20:
        return {"entry": False}
    exit_price = pos.get("exit_price", 0)
    reason = pos.get("close_reason", "")
    if reason == "forecast_changed" and exit_price < entry * 0.50:
        return {
            "entry": True,
            "override_exit_price": 0.30,
            "override_reason": "forecast_floor_holdsim",
        }
    if reason == "stop_loss" and exit_price < entry * 0.75:
        return {
            "entry": True,
            "override_exit_price": entry * 0.75,
            "override_reason": "hard_stop_25pct_capped",
        }
    return {"entry": True, "override_exit_price": None, "override_reason": None}


STRATEGIES: dict[str, Callable[[dict, dict], dict]] = {
    "as_recorded": strat_as_recorded,
    "filter_cheap": strat_filter_cheap,
    "filter_cheap_high_volume": strat_filter_cheap_high_volume,
    "forecast_floor": strat_forecast_floor,
    "combined_patches": strat_combined_patches,
}


# ─── Replay engine ──────────────────────────────────────────────────────

def simulate(markets: list[dict], strategy_fn: Callable[[dict, dict], dict]) -> list[dict]:
    """Apply a strategy function across all closed positions, return trade rows."""
    trades = []
    for market in markets:
        pos = market.get("position")
        if not pos or pos.get("status") != "closed":
            continue
        decision = strategy_fn(market, pos)
        if not decision.get("entry"):
            continue

        entry = pos["entry_price"]
        cost = pos.get("cost", 0)
        shares = pos.get("shares", 0)

        if decision.get("override_exit_price") is not None:
            exit_price = decision["override_exit_price"]
            pnl = round((exit_price - entry) * shares, 4)
            reason = decision.get("override_reason") or "override"
        else:
            exit_price = pos.get("exit_price", 0)
            pnl = pos.get("pnl", 0)
            reason = pos.get("close_reason", "?")

        trades.append({
            "city": market.get("city"),
            "date": market.get("date"),
            "entry": entry,
            "exit": exit_price,
            "cost": cost,
            "shares": shares,
            "pnl": pnl,
            "reason": reason,
            "source": market.get("_source"),
        })
    return trades


# ─── Metrics ────────────────────────────────────────────────────────────

def compute_metrics(trades: list[dict]) -> dict:
    """Compute summary metrics over a list of trades."""
    if not trades:
        return {"n": 0}
    pnls = [t["pnl"] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    n = len(trades)
    total = sum(pnls)
    win_rate = len(wins) / n if n else 0

    cumulative = []
    running = 0.0
    for p in pnls:
        running += p
        cumulative.append(running)
    peak = cumulative[0] if cumulative else 0
    max_drawdown = 0.0
    for value in cumulative:
        peak = max(peak, value)
        drawdown = peak - value
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    stdev = pstdev(pnls) if len(pnls) > 1 else 0.0
    sharpe_per_trade = (mean(pnls) / stdev) if stdev > 0 else 0.0

    return {
        "n": n,
        "wr": win_rate,
        "wins": len(wins),
        "losses": len(losses),
        "avg_pnl": mean(pnls),
        "avg_win": mean(wins) if wins else 0,
        "avg_loss": mean(losses) if losses else 0,
        "total": total,
        "best": max(pnls),
        "worst": min(pnls),
        "max_dd": max_drawdown,
        "sharpe_pt": sharpe_per_trade,
    }


def format_row(name: str, m: dict) -> str:
    if m["n"] == 0:
        return f"{name:24} | n=0"
    return (
        f"{name:24} | "
        f"n={m['n']:3} | "
        f"WR {m['wr']*100:5.1f}% ({m['wins']:>2}W/{m['losses']:>2}L) | "
        f"avg ${m['avg_pnl']:+6.2f} | "
        f"win avg ${m['avg_win']:+6.2f} | "
        f"loss avg ${m['avg_loss']:+6.2f} | "
        f"total ${m['total']:+8.2f} | "
        f"DD ${m['max_dd']:6.2f} | "
        f"Sharpe/trade {m['sharpe_pt']:+5.2f}"
    )


# ─── CLI ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Directories containing market JSON files")
    parser.add_argument("--strategy", default="all", help="Strategy name or 'all'")
    parser.add_argument("--show-trades", action="store_true", help="Print every trade")
    args = parser.parse_args()

    markets = load_markets(args.paths)
    closed = [m for m in markets if has_closed_position(m)]
    print(f"Loaded {len(markets)} markets, {len(closed)} with closed positions, "
          f"from {len(args.paths)} source(s).\n")

    if args.strategy == "all":
        names = list(STRATEGIES.keys())
    else:
        if args.strategy not in STRATEGIES:
            print(f"Unknown strategy: {args.strategy}\nAvailable: {list(STRATEGIES.keys())}",
                  file=sys.stderr)
            sys.exit(1)
        names = [args.strategy]

    print("=" * 200)
    for name in names:
        trades = simulate(closed, STRATEGIES[name])
        metrics = compute_metrics(trades)
        print(format_row(name, metrics))
        if args.show_trades and trades:
            print("    [trades]")
            for t in trades:
                print(f"      {t['city']:14} {t['date']} | "
                      f"${t['entry']:.3f} -> ${t['exit']:.3f} | "
                      f"{t['reason']:25} | PnL {t['pnl']:+7.2f}")
    print("=" * 200)


if __name__ == "__main__":
    main()
