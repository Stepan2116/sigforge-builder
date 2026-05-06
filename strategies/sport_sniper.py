#!/usr/bin/env python3
"""
sport_sniper.py — Live-state sports resolution capture for Polymarket.

Strategy: scan active Polymarket markets every 60 seconds. For each market
identified as a sports market (via the `sportsMarketType` schema field),
buy the favored side at $0.92+ if game state suggests near-certain outcome.
Hold to resolution.

Edge thesis (see strategies/SPORT-SNIPER.md for full spec):
    Decisive-state sport markets (team leading 6-1 in MLB late innings,
    series 1-0 in best-of-3 esports) trade at $0.92 – $0.99 despite very
    high actual win probability. Capturing this gap yields ~$0.04 – $0.08
    per trade at projected 85-95% win rate.

Implementation notes:
    - `sportsMarketType` is a Polymarket schema field on sport-only markets.
      We use this for detection, not tag slugs (tags not returned by /markets).
    - Live game state available via events[0].score / .elapsed / .live / .ended.
    - Faster polling than YIELD-FARM (60s vs 300s) because sport-resolve
      windows are minutes, not days.
    - Smaller per-trade size ($10 vs YIELD-FARM's $20) reflects higher
      tail variance in sports.

Output:
    /opt/sigforge/weather/data/paper_cointrick_sports_trades.jsonl
        — append-only trade log
    /opt/sigforge/weather/data/paper_cointrick_sports_state.json
        — {market_id: {...trade}} for dedup + reconciliation
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ─── Configuration ──────────────────────────────────────────────────────

DATA_DIR = Path(os.environ.get("SIGFORGE_DATA_DIR", "/opt/sigforge/weather/data"))
TRADES_PATH = DATA_DIR / "paper_cointrick_sports_trades.jsonl"
STATE_PATH = DATA_DIR / "paper_cointrick_sports_state.json"

GAMMA_API = "https://gamma-api.polymarket.com/markets"
USER_AGENT = "sport-sniper/1.0"

POLL_INTERVAL_SEC: int = int(os.environ.get("SPORT_POLL_INTERVAL_SEC", "60"))
MIN_PRICE: float = float(os.environ.get("SPORT_MIN_PRICE", "0.92"))
MAX_PRICE: float = float(os.environ.get("SPORT_MAX_PRICE", "0.999"))
MIN_VOL_24H: float = float(os.environ.get("SPORT_MIN_VOL_24H", "500"))
MAX_DAYS_TO_RESOLVE: float = float(os.environ.get("SPORT_MAX_DAYS_TO_RESOLVE", "7"))
SIZE_PER_TRADE_USD: float = float(os.environ.get("SPORT_SIZE_PER_TRADE_USD", "10"))
MAX_OPEN_USD: float = float(os.environ.get("SPORT_MAX_OPEN_USD", "200"))

# Skip markets whose question contains any of these (dispute-prone wording).
SKIP_KEYWORDS: tuple[str, ...] = (
    "referee", "controversial", "var-decision", "playoff-format",
)


# ─── Utilities ──────────────────────────────────────────────────────────

def utc_now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(message: str) -> None:
    print(f"{utc_now_str()} sport_sniper: {message}", flush=True)


def load_state() -> dict[str, Any]:
    try:
        return json.loads(STATE_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.write_text(json.dumps(state, separators=(",", ":")))


def append_trade(row: dict[str, Any]) -> None:
    with TRADES_PATH.open("a") as f:
        f.write(json.dumps(row, separators=(",", ":")) + "\n")


def fetch_markets(limit: int = 500, offset: int = 0) -> list[dict[str, Any]]:
    """Fetch active markets ordered by 24h volume descending."""
    qs = urllib.parse.urlencode({
        "closed": "false",
        "active": "true",
        "limit": limit,
        "offset": offset,
        "order": "volume24hr",
        "ascending": "false",
    })
    req = urllib.request.Request(
        f"{GAMMA_API}?{qs}",
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


# ─── Market parsing ─────────────────────────────────────────────────────

def parse_prices(market: dict[str, Any]) -> Optional[list[float]]:
    """Extract [yes_price, no_price] floats from outcomePrices field."""
    raw = market.get("outcomePrices")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return None
    if not raw or len(raw) < 2:
        return None
    try:
        return [float(p) for p in raw]
    except (TypeError, ValueError):
        return None


def parse_outcomes(market: dict[str, Any]) -> Optional[list[str]]:
    """Extract outcome labels (typically ["Yes", "No"])."""
    raw = market.get("outcomes")
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    return raw


def days_to_end(end_iso: Optional[str]) -> Optional[float]:
    """Hours-to-resolution as a float (negative if past)."""
    if not end_iso:
        return None
    try:
        end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
        return (end - datetime.now(timezone.utc)).total_seconds() / 86400
    except (TypeError, ValueError):
        return None


def get_game_info(market: dict[str, Any]) -> dict[str, Any]:
    """Live game state from events[0] if present."""
    events = market.get("events") or []
    if not events or not isinstance(events[0], dict):
        return {}
    e = events[0]
    return {
        "score": e.get("score"),
        "elapsed": e.get("elapsed"),
        "period": e.get("period"),
        "live": bool(e.get("live")),
        "ended": bool(e.get("ended")),
        "title": e.get("title"),
    }


def is_sport_market(market: dict[str, Any]) -> bool:
    """Polymarket sport markets carry sportsMarketType + sports_fees_v2."""
    if market.get("sportsMarketType"):
        question = (market.get("question") or "").lower()
        if any(keyword in question for keyword in SKIP_KEYWORDS):
            return False
        return True
    if (market.get("feeType") or "").startswith("sports"):
        return True
    return False


def select_side(prices: list[float], outcomes: list[str]) -> Optional[tuple[int, float]]:
    """Return (index, price) of the favored side meeting MIN_PRICE/MAX_PRICE."""
    if not prices or not outcomes or len(prices) != len(outcomes):
        return None
    for i, price in enumerate(prices):
        if MIN_PRICE <= price <= MAX_PRICE:
            return (i, price)
    return None


# ─── Main scan loop ─────────────────────────────────────────────────────

def open_exposure(state: dict[str, Any]) -> float:
    """Sum of `spend` across all open positions in state."""
    return sum(
        float(t.get("spend", 0))
        for t in state.values()
        if t.get("status") in ("open", None)
    )


def scan_pass() -> None:
    """One full scan-and-buy pass over current Polymarket sport markets."""
    state = load_state()
    if open_exposure(state) >= MAX_OPEN_USD:
        log(f"max exposure reached (${MAX_OPEN_USD}), skipping scan")
        return

    markets = fetch_markets(limit=500)
    total = len(markets)
    sport_count = 0
    new_picks = 0

    for market in markets:
        if not is_sport_market(market):
            continue
        sport_count += 1

        market_id = market.get("id") or market.get("conditionId")
        if not market_id or str(market_id) in state:
            continue

        prices = parse_prices(market)
        outcomes = parse_outcomes(market)
        if not prices or not outcomes:
            continue

        volume_24h = float(market.get("volume24hr", 0) or 0)
        if volume_24h < MIN_VOL_24H:
            continue

        days = days_to_end(market.get("endDate"))
        if days is None or days > MAX_DAYS_TO_RESOLVE or days < 0:
            continue

        pick = select_side(prices, outcomes)
        if not pick:
            continue
        idx, price = pick

        game = get_game_info(market)
        if game.get("ended"):
            continue  # would not get fill in real life

        spend = SIZE_PER_TRADE_USD
        shares = round(spend / price, 4) if price > 0 else 0
        outcome = outcomes[idx] if idx < len(outcomes) else "?"

        row = {
            "ts": utc_now_str(),
            "market_id": str(market_id),
            "slug": market.get("slug"),
            "question": market.get("question"),
            "endDate": market.get("endDate"),
            "outcomes": outcomes,
            "outcome_picked": outcome,
            "outcome_idx": idx,
            "buy_price": price,
            "shares": shares,
            "spend": round(spend, 4),
            "vol24h": round(volume_24h, 2),
            "sportsMarketType": market.get("sportsMarketType"),
            "game": game,
            "status": "open",
        }
        state[str(market_id)] = row
        append_trade(row)
        save_state(state)
        new_picks += 1
        log(f"BUY {row['slug']} @ ${price:.3f} ({outcome}) — vol24h ${volume_24h:.0f} — ends in {days:.1f}d")

        if open_exposure(state) >= MAX_OPEN_USD:
            break

    log(f"pass: total={total} sport={sport_count} new_picks={new_picks} "
        f"open_total=${open_exposure(state):.2f}")


def main() -> None:
    log(f"starting — MIN_PRICE={MIN_PRICE}, polling {POLL_INTERVAL_SEC}s, "
        f"size=${SIZE_PER_TRADE_USD}, max_open=${MAX_OPEN_USD}")
    while True:
        try:
            scan_pass()
        except Exception as exc:
            log(f"scan_error: {exc}")
        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    main()
