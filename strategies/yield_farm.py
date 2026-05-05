#!/usr/bin/env python3
"""
cointrick_paper.py — paper version of cointrick yield-farming arb.

Strategy: scan all active markets every 5 min; buy "obvious winner" side
at price >= MIN_PRICE; hold to resolution; profit = $1 - buy_price if win, -buy_price if loss.

Idempotent — won't re-bet markets already in state file.

Outputs:
  data/paper_cointrick_trades.jsonl — append-only trade log
  data/paper_cointrick_state.json   — {market_id: {...trade}} so we can dedup + reconcile
"""
import json
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/opt/sigforge/weather")
DATA = ROOT / "data"
TRADES = DATA / "paper_cointrick_trades.jsonl"
STATE = DATA / "paper_cointrick_state.json"

GAMMA = "https://gamma-api.polymarket.com/markets"
POLL_INTERVAL_SEC = 300              # scan every 5 min
MIN_PRICE = 0.98                     # 0.98+ counts as "obvious"
MAX_PRICE = 0.999                    # avoid 1.00 (no profit)
MIN_VOL_24H = 1_000                  # at least $1K daily volume
MAX_DAYS_TO_RESOLVE = 30             # resolves within 30 days
SIZE_PER_TRADE_USD = 20              # paper $20 per pick
MAX_OPEN_USD = 500                   # cap total open exposure
SKIP_TAG_SLUGS = {"sports", "politics", "geopolitics", "esports"}   # avoid dispute-prone
SKIP_KEYWORDS = ["fifa", "election", "ceasefire", "trump", "putin"]


def log(msg):
    print(f"{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} {msg}", flush=True)


def load_state():
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {}


def save_state(s):
    STATE.write_text(json.dumps(s, separators=(",", ":")))


def append_trade(row):
    with TRADES.open("a") as f:
        f.write(json.dumps(row, separators=(",", ":")) + "\n")


def fetch_markets(limit=500, offset=0):
    qs = urllib.parse.urlencode({
        "closed": "false",
        "active": "true",
        "limit": limit,
        "offset": offset,
        "order": "volume24hr",
        "ascending": "false",
    })
    req = urllib.request.Request(f"{GAMMA}?{qs}", headers={"User-Agent": "cointrick-paper/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def parse_prices(m):
    op = m.get("outcomePrices")
    if isinstance(op, str):
        try:
            op = json.loads(op)
        except Exception:
            return None
    if not op or len(op) < 2:
        return None
    try:
        return [float(p) for p in op]
    except Exception:
        return None


def parse_outcomes(m):
    o = m.get("outcomes")
    if isinstance(o, str):
        try:
            o = json.loads(o)
        except Exception:
            return None
    return o


def is_skip(m):
    slug = (m.get("slug") or "").lower()
    if any(k in slug for k in SKIP_KEYWORDS):
        return True
    tags = m.get("tags") or []
    if isinstance(tags, list):
        for t in tags:
            tslug = ((t or {}).get("slug") or "").lower() if isinstance(t, dict) else str(t).lower()
            if tslug in SKIP_TAG_SLUGS:
                return True
    return False


def days_until_end(end_iso):
    if not end_iso:
        return None
    try:
        end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
        return (end - datetime.now(timezone.utc)).total_seconds() / 86400
    except Exception:
        return None


def scan_once(state):
    try:
        markets = fetch_markets(limit=500)
    except Exception as e:
        log(f"fetch err: {e}")
        return
    open_usd = sum(t.get("buy_price", 0) * t.get("shares", 0) for t in state.values() if t.get("status") == "open")
    new = 0
    skipped = {"already": 0, "skip_tag": 0, "no_outcome": 0, "low_vol": 0, "wrong_price": 0, "too_far": 0, "low_budget": 0, "single_outcome": 0}

    for m in markets:
        mid = m.get("id") or m.get("conditionId") or m.get("slug")
        if not mid:
            continue
        if str(mid) in state:
            skipped["already"] += 1
            continue
        if is_skip(m):
            skipped["skip_tag"] += 1
            continue
        prices = parse_prices(m)
        outcomes = parse_outcomes(m)
        if not prices or not outcomes or len(outcomes) < 2:
            skipped["no_outcome"] += 1
            continue
        if len(outcomes) != 2:
            skipped["single_outcome"] += 1
            continue
        vol24 = float(m.get("volume24hr") or 0)
        if vol24 < MIN_VOL_24H:
            skipped["low_vol"] += 1
            continue
        days = days_until_end(m.get("endDate"))
        if days is None or days < 0 or days > MAX_DAYS_TO_RESOLVE:
            skipped["too_far"] += 1
            continue
        # find side with price >= MIN_PRICE
        idx = None
        for i, p in enumerate(prices):
            if MIN_PRICE <= p <= MAX_PRICE:
                idx = i
                break
        if idx is None:
            skipped["wrong_price"] += 1
            continue
        if open_usd + SIZE_PER_TRADE_USD > MAX_OPEN_USD:
            skipped["low_budget"] += 1
            continue

        buy_price = prices[idx]
        outcome = outcomes[idx]
        shares = round(SIZE_PER_TRADE_USD / buy_price, 2)

        trade = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "market_id": str(mid),
            "slug": m.get("slug"),
            "endDate": m.get("endDate"),
            "outcomes": outcomes,
            "outcome_picked": outcome,
            "outcome_idx": idx,
            "buy_price": buy_price,
            "shares": shares,
            "spend": round(buy_price * shares, 4),
            "vol24h": round(vol24, 2),
            "status": "open",
        }
        state[str(mid)] = trade
        append_trade(trade)
        open_usd += trade["spend"]
        new += 1

    save_state(state)
    log(f"scan: total={len(markets)} new_buys={new} open_usd=${open_usd:.2f} skip={skipped}")


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    log("cointrick_paper starting")
    while True:
        try:
            state = load_state()  # reload each tick to pick up reconciler changes
            scan_once(state)
        except Exception as e:
            log(f"loop err: {e}")
        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    main()
