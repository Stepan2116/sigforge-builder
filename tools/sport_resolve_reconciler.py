#!/usr/bin/env python3
"""
sport_resolve_reconciler.py — match open paper sport-sniper positions to resolved markets.

Run from cron hourly (sport markets resolve once per game; no need to poll
faster). For each position with status="open" in the state file:

  1. Fetch market by id from Gamma (`closed=true` filter).
  2. If the market is closed and one outcome priced >=0.99, that outcome is
     the resolved winner.
  3. Mark our position won (resolve_value = shares × $1) or lost ($0).
  4. Update state file in-place and append a row to the reconcile log.

Cycle prints summary stats so the cron output is greppable.

Configuration (env vars; sensible defaults match SigForge production):
  SF_DATA_DIR     directory holding state + reconcile log files
                  (default: /opt/sigforge/weather/data)
  SF_STATE_FILE   path to sport-sniper state JSON
                  (default: $SF_DATA_DIR/paper_cointrick_sports_state.json)
  SF_LOG_FILE     path to append-only JSONL reconcile log
                  (default: $SF_DATA_DIR/paper_cointrick_sports_reconcile.jsonl)
  SF_GAMMA_URL    Polymarket Gamma API endpoint
                  (default: https://gamma-api.polymarket.com/markets)
  SF_HTTP_TIMEOUT seconds before HTTP request times out (default: 15)
  SF_USER_AGENT   User-Agent header (default: sport-sniper-reconcile/1.0)
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.environ.get("SF_DATA_DIR", "/opt/sigforge/weather/data"))
STATE_FILE = Path(os.environ.get("SF_STATE_FILE",
                                 str(DATA_DIR / "paper_cointrick_sports_state.json")))
LOG_FILE = Path(os.environ.get("SF_LOG_FILE",
                               str(DATA_DIR / "paper_cointrick_sports_reconcile.jsonl")))
GAMMA_URL = os.environ.get("SF_GAMMA_URL", "https://gamma-api.polymarket.com/markets")
HTTP_TIMEOUT = float(os.environ.get("SF_HTTP_TIMEOUT", "15"))
USER_AGENT = os.environ.get("SF_USER_AGENT", "sport-sniper-reconcile/1.0")

WINNING_PRICE_FLOOR = 0.99   # outcome priced >= this is treated as the winner


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    print(f"{now_iso()} sport-sniper-recon: {msg}", flush=True)


def fetch_market(mid: str) -> dict[str, Any] | None:
    """Fetch a single closed market by id. Returns None on failure or if the
    market is not yet closed (Gamma omits open markets when closed=true)."""
    qs = urllib.parse.urlencode({"id": mid, "closed": "true"})
    req = urllib.request.Request(f"{GAMMA_URL}?{qs}", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
            d = json.loads(r.read())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    if isinstance(d, list) and d:
        return d[0]
    if isinstance(d, dict):
        return d
    return None


def parse_prices(m: dict[str, Any]) -> list[float] | None:
    op = m.get("outcomePrices")
    if isinstance(op, str):
        try:
            op = json.loads(op)
        except json.JSONDecodeError:
            return None
    if not op:
        return None
    try:
        return [float(p) for p in op]
    except (TypeError, ValueError):
        return None


def winner_index(prices: list[float]) -> int | None:
    for i, p in enumerate(prices):
        if p >= WINNING_PRICE_FLOOR:
            return i
    return None


def main() -> int:
    if not STATE_FILE.exists():
        log(f"no state file at {STATE_FILE} — nothing to reconcile")
        return 0

    state: dict[str, dict[str, Any]] = json.loads(STATE_FILE.read_text())
    open_positions = [(k, t) for k, t in state.items() if t.get("status") == "open"]
    log(f"total={len(state)} open={len(open_positions)}")

    won = lost = still_open = errors = 0
    cycle_pnl = 0.0
    cycle_spend = 0.0

    for mid, t in open_positions:
        m = fetch_market(mid)
        if not m or not (m.get("closed") or m.get("archived")):
            still_open += 1
            continue
        prices = parse_prices(m)
        if not prices:
            errors += 1
            continue
        widx = winner_index(prices)
        if widx is None:
            # closed but ambiguous (void, partial, dispute) — leave to operator
            still_open += 1
            continue

        our_idx = t.get("outcome_idx")
        shares = float(t.get("shares") or 0)
        spend = float(t.get("spend") or 0)
        won_pos = our_idx == widx
        resolve_value = shares if won_pos else 0.0
        pnl = resolve_value - spend

        t["status"] = "won" if won_pos else "lost"
        t["resolve_value"] = round(resolve_value, 4)
        t["pnl"] = round(pnl, 4)
        t["resolved_at"] = now_iso()
        t["winner_idx"] = widx

        if won_pos:
            won += 1
        else:
            lost += 1
        cycle_pnl += pnl
        cycle_spend += spend

        with LOG_FILE.open("a") as f:
            f.write(json.dumps({
                "ts": now_iso(),
                "market_id": mid,
                "slug": t.get("slug"),
                "buy_price": t.get("buy_price"),
                "won": won_pos,
                "pnl": round(pnl, 4),
                "spend": round(spend, 4),
                "sportsMarketType": t.get("sportsMarketType"),
            }, separators=(",", ":")) + "\n")

    STATE_FILE.write_text(json.dumps(state, separators=(",", ":")))

    closed_all = [t for t in state.values() if t.get("status") in ("won", "lost")]
    total_pnl = sum(float(t.get("pnl") or 0) for t in closed_all)
    total_spend = sum(float(t.get("spend") or 0) for t in closed_all)
    wr = (sum(1 for t in closed_all if t.get("status") == "won") / len(closed_all)
          if closed_all else 0)
    roi = 100 * total_pnl / total_spend if total_spend else 0
    log(f"cycle:    won=+{won}  lost=-{lost}  open={still_open}  err={errors}")
    log(f"cycle:    realized PnL ${cycle_pnl:+.4f} on ${cycle_spend:.2f}")
    log(f"all-time: WR={wr:.1%} N={len(closed_all)} "
        f"spend=${total_spend:.2f} pnl=${total_pnl:+.4f} ROI={roi:+.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
