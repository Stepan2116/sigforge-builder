#!/usr/bin/env python3
"""
ai_hypothesis.py — generate strategy hypotheses from trade logs via Claude.

The SigForge methodology requires every strategy or patch to start with a
written hypothesis (`docs/METHODOLOGY.md` section 1). Writing a hypothesis
that survives backtesting is the hard part — most retail traders skip it
entirely. This tool helps by reading the structured trade log and asking
Claude to propose hypotheses that would explain the observed pattern,
ranked by falsifiability.

The output is intentionally a *list of candidate hypotheses with proposed
falsification tests*, not a single answer. The framework rewards thinking
in alternatives, not picking the first plausible explanation.

Usage:
  ANTHROPIC_API_KEY=sk-ant-... python3 ai_hypothesis.py path/to/trades.jsonl
  python3 ai_hypothesis.py --dry-run path/to/trades.jsonl   # print prompt only

Configuration via env:
  ANTHROPIC_API_KEY   required for live calls (omit for --dry-run mode)
  ANTHROPIC_MODEL     default: claude-sonnet-4-6
  HTTP_TIMEOUT_SEC    default: 60
  MAX_TRADES          default: 100 (most recent N trades sent to Claude)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-6"
SYSTEM_PROMPT = """You are a quantitative research assistant for SigForge,
a prediction-market validation framework. Your job is to read trade logs
and propose hypotheses that would explain the observed pattern.

Output rules:
  1. Propose 3 candidate hypotheses, ranked by falsifiability (most
     falsifiable first).
  2. For each hypothesis, include: the claim in one sentence, the
     mechanism (why it would produce the observed pattern), and a
     concrete falsification test (specific data the team could collect
     that would disprove it).
  3. Do NOT propose untestable hypotheses ("market is inefficient",
     "lucky sample"). The framework explicitly rejects those.
  4. Lead with the hypothesis you would test first if forced to choose.

Format the response in plain markdown with H3 headings per hypothesis."""


def load_trades(path: Path, max_trades: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows[-max_trades:] if max_trades > 0 else rows


def summarize_trades(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Reduce raw trade rows to the small set of fields Claude needs.

    Sending raw 1000-row JSON wastes tokens; this function distills the
    fields most useful for hypothesis generation: entry price, win/loss,
    PnL, market category, sample size."""
    closed = [r for r in rows if r.get("status") in ("won", "lost")]
    open_ = [r for r in rows if r.get("status") == "open"]
    won = [r for r in closed if r.get("status") == "won"]
    n = len(closed)
    pnl = sum(float(r.get("pnl") or 0) for r in closed)
    spend = sum(float(r.get("spend") or 0) for r in closed)
    by_price_band = {"$0.30-0.50": 0, "$0.50-0.70": 0, "$0.70-0.90": 0, "$0.90+": 0}
    for r in closed:
        p = float(r.get("buy_price") or 0)
        if p < 0.50: by_price_band["$0.30-0.50"] += 1
        elif p < 0.70: by_price_band["$0.50-0.70"] += 1
        elif p < 0.90: by_price_band["$0.70-0.90"] += 1
        else: by_price_band["$0.90+"] += 1

    return {
        "closed_count": n,
        "open_count": len(open_),
        "win_rate": (len(won) / n) if n else None,
        "realized_pnl_usd": round(pnl, 4),
        "total_spend_usd": round(spend, 2),
        "roi_pct": (100 * pnl / spend) if spend else None,
        "by_buy_price_band": by_price_band,
        "sample_first_3_closed": closed[:3],
        "sample_last_3_closed": closed[-3:],
    }


def build_user_prompt(strategy_name: str, summary: dict[str, Any]) -> str:
    return (
        f"Strategy: {strategy_name}\n\n"
        f"Aggregate stats:\n```json\n{json.dumps(summary, indent=2)}\n```\n\n"
        "Propose 3 candidate hypotheses that could explain this pattern, "
        "ranked by falsifiability. For each, include the claim, mechanism, "
        "and a concrete falsification test."
    )


def call_claude(api_key: str, model: str, system: str, user: str,
                timeout: float) -> str:
    body = json.dumps({
        "model": model,
        "max_tokens": 2048,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }).encode()
    req = urllib.request.Request(
        API_URL,
        data=body,
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    parts = d.get("content") or []
    return "\n".join(p.get("text", "") for p in parts if isinstance(p, dict))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("trades_path", type=Path, help="path to a trades JSONL file")
    ap.add_argument("--strategy", default="UNNAMED",
                    help="strategy name shown to Claude (default: UNNAMED)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the prompt and exit without calling the API")
    ap.add_argument("--max-trades", type=int,
                    default=int(os.environ.get("MAX_TRADES", "100")))
    args = ap.parse_args()

    if not args.trades_path.exists():
        print(f"ERROR: {args.trades_path} not found", file=sys.stderr)
        return 1

    rows = load_trades(args.trades_path, args.max_trades)
    if not rows:
        print(f"ERROR: no trades parsed from {args.trades_path}", file=sys.stderr)
        return 2

    summary = summarize_trades(rows)
    user_prompt = build_user_prompt(args.strategy, summary)

    if args.dry_run:
        print("=" * 60)
        print("DRY RUN — would send the following to Claude:")
        print("=" * 60)
        print(f"system: {SYSTEM_PROMPT}\n")
        print(f"user: {user_prompt}")
        return 0

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set. Use --dry-run to preview the "
              "prompt without calling the API.", file=sys.stderr)
        return 3

    model = os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
    timeout = float(os.environ.get("HTTP_TIMEOUT_SEC", "60"))
    try:
        response = call_claude(api_key, model, SYSTEM_PROMPT, user_prompt, timeout)
    except urllib.error.HTTPError as e:
        print(f"ERROR: API returned {e.code}: {e.read().decode(errors='replace')}",
              file=sys.stderr)
        return 4
    except Exception as e:
        print(f"ERROR: API call failed: {e}", file=sys.stderr)
        return 5

    print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
