#!/usr/bin/env python3
"""
whale_discover.py — find candidate wallets with forecast-tier weather positions.

The weather-copy strategy currently mirrors a single wallet (coldmath,
0x594edb91…). When coldmath stops opening forecast-tier ($0.30-$0.65)
positions, the strategy goes idle — see the 1804-signal / 0-trade
diagnosis in the audit notes (it is not a bug, it is data starvation).

This tool widens the search: enumerate the top 50 weather markets by
24h volume, fetch the top holders of each, and rank candidate wallets
by how many forecast-tier weather positions they currently hold. Output
is a candidate list the operator can review and add to the WHALES dict
in `weather_copy_paper.py`.

The tool is read-only. It never trades, never modifies state, never
adds wallets to the strategy automatically. Output is a list of
addresses + stats; the human decides which to add.

Usage:
    python3 whale_discover.py                           # default scan
    python3 whale_discover.py --markets 100 --top-k 20  # wider scan
    python3 whale_discover.py --json                    # machine-readable

Configuration via env (sensible defaults, override only if needed):
    SF_GAMMA_URL   default: https://gamma-api.polymarket.com/markets
    SF_DATA_URL    default: https://data-api.polymarket.com/positions
    HTTP_TIMEOUT   default: 15
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from typing import Any

GAMMA = os.environ.get("SF_GAMMA_URL", "https://gamma-api.polymarket.com/markets")
DATA_API = os.environ.get("SF_DATA_URL", "https://data-api.polymarket.com/positions")
TIMEOUT = float(os.environ.get("HTTP_TIMEOUT", "15"))
USER_AGENT = "sigforge-whale-discover/1.0"

FORECAST_MIN = 0.30
FORECAST_MAX = 0.65
WEATHER_SLUG_PREFIXES = ("highest-temperature-in-", "lowest-temperature-in-")


def http_get(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def is_weather(market: dict[str, Any]) -> bool:
    slug = (market.get("slug") or "").lower()
    return any(slug.startswith(p) for p in WEATHER_SLUG_PREFIXES)


def fetch_weather_markets(limit: int) -> list[dict[str, Any]]:
    """Return up to `limit` weather markets sorted by 24h volume.

    Gamma does not expose tag-based filtering on this endpoint, so we
    pull the top 500 markets by 24h volume and keep only the weather
    ones. Weather markets are typically rank 50-200 by volume, so 500 is
    a safe pull size; tighten only if Gamma rate-limits.
    """
    qs = urllib.parse.urlencode({
        "active": "true", "closed": "false",
        "order": "volume24hr", "ascending": "false",
        "limit": 500,
    })
    data = http_get(f"{GAMMA}?{qs}") or []
    weather = [m for m in data if is_weather(m)]
    return weather[:limit]


def fetch_user_positions(addr: str) -> list[dict[str, Any]]:
    qs = urllib.parse.urlencode({
        "user": addr, "limit": 500,
        "sortBy": "CURRENT", "sortDirection": "DESC",
    })
    d = http_get(f"{DATA_API}?{qs}")
    return d if isinstance(d, list) else []


def fetch_market_holders(condition_id: str) -> list[dict[str, Any]]:
    """Top holders of a market via the data-api positions endpoint."""
    qs = urllib.parse.urlencode({
        "market": condition_id, "limit": 50,
        "sortBy": "CURRENT", "sortDirection": "DESC",
    })
    d = http_get(f"{DATA_API}?{qs}")
    return d if isinstance(d, list) else []


def in_forecast_tier(pos: dict[str, Any]) -> bool:
    avg = pos.get("avgPrice")
    if avg is None:
        return False
    try:
        avg = float(avg)
    except (TypeError, ValueError):
        return False
    return FORECAST_MIN <= avg <= FORECAST_MAX


def score_wallet(addr: str) -> dict[str, Any]:
    """Return per-wallet stats: forecast-tier weather position count + size."""
    positions = fetch_user_positions(addr)
    weather = [p for p in positions if is_weather(p)]
    forecast = [p for p in weather if in_forecast_tier(p)]
    cur_value = sum(float(p.get("currentValue") or 0) for p in forecast)
    return {
        "address": addr,
        "weather_positions": len(weather),
        "forecast_tier_positions": len(forecast),
        "forecast_tier_value_usd": round(cur_value, 2),
        "sample_slugs": [p.get("slug") for p in forecast[:3]],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--markets", type=int, default=50,
                    help="number of weather markets to enumerate (default: 50)")
    ap.add_argument("--top-k", type=int, default=10,
                    help="how many candidate wallets to print (default: 10)")
    ap.add_argument("--exclude", action="append", default=[
        "0x594edb9112f526fa6a80b8f858a6379c8a2c1c11",  # coldmath, already wired up
    ], help="addresses to exclude (repeatable)")
    ap.add_argument("--min-positions", type=int, default=2,
                    help="skip wallets with fewer forecast-tier positions")
    ap.add_argument("--json", action="store_true",
                    help="emit machine-readable JSON instead of a table")
    args = ap.parse_args()

    excluded = {a.lower() for a in args.exclude}

    print(f"# scanning top {args.markets} weather markets...", file=sys.stderr)
    markets = fetch_weather_markets(args.markets)
    if not markets:
        print("ERROR: no weather markets returned by Gamma", file=sys.stderr)
        return 1
    print(f"# got {len(markets)} weather markets, fetching holders...", file=sys.stderr)

    candidates: dict[str, int] = defaultdict(int)
    for i, m in enumerate(markets, 1):
        cid = m.get("conditionId") or m.get("id")
        if not cid:
            continue
        for holder in fetch_market_holders(cid):
            addr = (holder.get("user") or "").lower()
            if not addr or addr in excluded:
                continue
            if not in_forecast_tier(holder):
                continue
            candidates[addr] += 1
        if i % 10 == 0:
            print(f"#   {i}/{len(markets)} markets scanned, "
                  f"{len(candidates)} unique candidates", file=sys.stderr)

    print(f"# scoring {len(candidates)} candidates with forecast-tier holdings...",
          file=sys.stderr)

    scored: list[dict[str, Any]] = []
    for addr in candidates:
        stats = score_wallet(addr)
        if stats["forecast_tier_positions"] >= args.min_positions:
            stats["markets_seen_in"] = candidates[addr]
            scored.append(stats)

    scored.sort(
        key=lambda x: (x["forecast_tier_positions"], x["forecast_tier_value_usd"]),
        reverse=True,
    )
    top = scored[:args.top_k]

    if args.json:
        print(json.dumps(top, indent=2))
        return 0

    if not top:
        print("\nNo candidates met the threshold "
              f"(min {args.min_positions} forecast-tier weather positions).")
        return 0

    print(f"\n=== Top {len(top)} candidate wallets "
          f"(min {args.min_positions} forecast-tier weather positions) ===\n")
    print(f"{'Address':<44}  {'fcst':>5}  {'mkts':>5}  {'value':>10}  sample slugs")
    print("-" * 90)
    for s in top:
        slugs = ", ".join((s["sample_slugs"] or [])[:2])[:30]
        print(f"{s['address']:<44}  "
              f"{s['forecast_tier_positions']:>5d}  "
              f"{s['markets_seen_in']:>5d}  "
              f"${s['forecast_tier_value_usd']:>9.2f}  "
              f"{slugs}")

    print(f"\n# Add a wallet to weather-copy by appending to the WHALES dict in")
    print(f"# strategies/yield_farm.py or weather_copy_paper.py — "
          "after reviewing its trade history.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
