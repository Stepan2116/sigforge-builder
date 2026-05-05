#!/usr/bin/env python3
"""
esports_copy_paper.py — paper copy-trader for esports insiders.

Strategy:
  - Snapshot positions of 2 esports specialist whales every 60s
  - When a NEW position appears (or size +50%) on their side, mirror it
  - Filter: whale size >= $1K (real signal, not test trade)
            market endDate > 30 min from now (still actionable)
            our open exposure < cap, daily cap not hit
            our buy price <= $0.92 (skip if already too late)
  - Paper-buy at bestAsk for our share, $5-50/signal scaled to whale conviction
  - Hold to resolve, reconciler matches via market.closed

Whales (all $$ values from 2026-05-02 deep-dive):
  - 0x18871c8e... 95% WR (19/1) on 20 LoL closed mkts, +$152K profit
  - 0x52ecea7b... 81% WR (13/3),  440 open pos, +$131K realized lifetime

Outputs:
  data/esports_copy_state.json  — portfolio (balance, open, history)
  data/esports_copy_trades.jsonl — append log
  data/esports_copy_signals.jsonl — every signal seen (even skipped) for analysis
  data/esports_copy_whale_snaps/<whale>/<ts>.json — raw snapshots (kept 7 days)
"""
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/opt/sigforge/weather")
DATA = ROOT / "data"
STATE = DATA / "esports_copy_state.json"
TRADES = DATA / "esports_copy_trades.jsonl"
SIGNALS = DATA / "esports_copy_signals.jsonl"
SNAP_DIR = DATA / "esports_copy_whale_snaps"

POS_URL = "https://data-api.polymarket.com/positions"
GAMMA = "https://gamma-api.polymarket.com/markets"

WHALES = {
    "0x[REDACTED_FOR_PRIVACY]": "specialist_alpha",
    "0x[REDACTED_FOR_PRIVACY]": "specialist_beta",
}

# === Strategy params ===
INITIAL_BALANCE = 1000.0
POLL_INTERVAL_SEC = 60
MIN_WHALE_SIZE_USD = 1000              # whale position must be ≥ this to copy
MIN_MARKET_TIME_MIN = 30               # at least 30 min before market end
MAX_BUY_PRICE = 0.92                   # skip if too late (price already settled)
COPY_SIZE_USD = 10                     # $10 per signal (10 / $1000 = 1% per trade)
MAX_OPEN_USD = 500                     # 50% capital deployed cap
MAX_DAILY_OPEN_USD = 100               # cap new exposure / day
SIZE_UP_RATIO = 1.5                    # 50%+ size increase = renewed signal


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg):
    print(f"{now_iso()} esports-copy: {msg}", flush=True)


def http_get(url, retries=2):
    for _ in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "esports-copy/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read())
        except Exception:
            time.sleep(1)
    return None


def load_state():
    if not STATE.exists():
        return {
            "balance": INITIAL_BALANCE,
            "initial_balance": INITIAL_BALANCE,
            "open_positions": {},   # market_id -> {...}
            "closed_positions": {}, # market_id -> {...}
            "last_snap": {},        # whale -> {asset: {size, slug, ...}}
            "started_at": now_iso(),
        }
    return json.loads(STATE.read_text())


def save_state(s):
    STATE.write_text(json.dumps(s, default=str, indent=2))


def append_trade(row):
    with TRADES.open("a") as f:
        f.write(json.dumps(row, separators=(",", ":")) + "\n")


def append_signal(row):
    with SIGNALS.open("a") as f:
        f.write(json.dumps(row, separators=(",", ":")) + "\n")


def fetch_whale_positions(addr):
    """Get current open positions for a wallet (paginated)."""
    out = []
    offset = 0
    while True:
        qs = urllib.parse.urlencode({
            "user": addr, "limit": 500, "offset": offset,
            "sortBy": "CURRENT", "sortDirection": "DESC",
        })
        d = http_get(f"{POS_URL}?{qs}")
        if not isinstance(d, list) or not d:
            break
        out.extend(d)
        if len(d) < 500: break
        offset += 500
    return out


def is_esports_pos(p):
    """Filter: only consider esports markets (not their sport/political plays)."""
    s = (p.get("slug") or "").lower()
    t = (p.get("title") or "").lower()
    text = s + " " + t
    return any(k in text for k in [
        "cs2", "csgo", "counter-strike", "cs-go",
        "dota", "lol-", "league-of-legends",
        "valorant", "vct-",
        "iem-", "esl-", "blast-", "lck-", "lpl-", "lec-", "lcs-",
    ])


def fetch_market_state(mid_or_cid):
    """Get fresh market state (best ask, end date, closed)."""
    qs = urllib.parse.urlencode({"id": mid_or_cid})
    d = http_get(f"{GAMMA}?{qs}")
    if isinstance(d, list) and d: return d[0]
    return None


def days_until(end_iso):
    if not end_iso: return None
    try:
        end = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
        return (end - datetime.now(timezone.utc)).total_seconds() / 86400
    except Exception:
        return None


def get_outcome_price(market, outcome_idx):
    """Best ask for our outcome side."""
    op = market.get("outcomePrices")
    if isinstance(op, str):
        try: op = json.loads(op)
        except: return None
    if not op or len(op) <= outcome_idx: return None
    try:
        return float(op[outcome_idx])
    except: return None


def daily_open_today(state):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return sum(p["spend"] for p in state["open_positions"].values()
               if p.get("opened_at", "").startswith(today))


def total_open(state):
    return sum(p["spend"] for p in state["open_positions"].values())


def diff_signals(prev_snap, cur_positions):
    """Return list of (asset, position, signal_type) tuples — new or sized-up."""
    prev_by_asset = {p["asset"]: p for p in (prev_snap or []) if p.get("asset")}
    out = []
    for p in cur_positions:
        a = p.get("asset")
        if not a: continue
        if a not in prev_by_asset:
            out.append((a, p, "NEW"))
        else:
            prev = prev_by_asset[a]
            cur_sz = float(p.get("size") or 0)
            prev_sz = float(prev.get("size") or 0)
            if prev_sz > 0 and cur_sz / prev_sz >= SIZE_UP_RATIO:
                out.append((a, p, f"SIZE_UP_{cur_sz/prev_sz:.1f}x"))
    return out


def consider_signal(state, whale_addr, whale_label, asset, pos, signal_type):
    """Decide whether to copy this signal. Returns (decision, reason, trade_dict_or_none)."""
    cid = pos.get("conditionId")
    mid = pos.get("conditionId")  # gamma uses both; conditionId works
    slug = pos.get("slug") or ""
    whale_cur = float(pos.get("currentValue") or 0)
    whale_size = float(pos.get("size") or 0)
    whale_avg = float(pos.get("avgPrice") or 0)
    outcome = pos.get("outcome", "")
    outcome_idx = pos.get("outcomeIndex")
    if outcome_idx is None:
        return ("skip", "no_outcome_idx", None)
    try: outcome_idx = int(outcome_idx)
    except: return ("skip", "bad_outcome_idx", None)
    end_iso = pos.get("endDate")

    # Filter 0: must be esports
    if not is_esports_pos(pos):
        return ("skip", "not_esports", None)

    # Filter 1: whale conviction size
    whale_value_for_threshold = whale_cur
    if whale_value_for_threshold < MIN_WHALE_SIZE_USD:
        return ("skip", f"whale_size_too_small_${whale_value_for_threshold:.0f}", None)

    # Filter 2: not already mirroring
    if cid in state["open_positions"]:
        return ("skip", "already_mirroring", None)
    if cid in state["closed_positions"]:
        return ("skip", "already_closed", None)

    # Fetch fresh market state
    mk = fetch_market_state(mid)
    if not mk:
        return ("skip", "fetch_market_failed", None)
    if mk.get("closed"):
        return ("skip", "market_closed", None)

    days = days_until(mk.get("endDate") or end_iso)
    if days is None or days * 24 * 60 < MIN_MARKET_TIME_MIN:
        return ("skip", f"too_late_{days*24*60:.0f}min" if days else "no_endDate", None)

    cur_px = get_outcome_price(mk, outcome_idx)
    if cur_px is None:
        return ("skip", "no_price", None)
    if cur_px > MAX_BUY_PRICE:
        return ("skip", f"price_too_high_${cur_px:.3f}", None)
    if cur_px < 0.01:
        return ("skip", f"price_dust_${cur_px:.4f}", None)

    # Filter 3: budget
    open_now = total_open(state)
    if open_now + COPY_SIZE_USD > MAX_OPEN_USD:
        return ("skip", f"open_cap_${open_now:.0f}", None)
    if state["balance"] < COPY_SIZE_USD:
        return ("skip", f"low_balance_${state['balance']:.2f}", None)
    daily = daily_open_today(state)
    if daily + COPY_SIZE_USD > MAX_DAILY_OPEN_USD:
        return ("skip", f"daily_cap_${daily:.0f}", None)

    # Approve! Build trade
    shares = COPY_SIZE_USD / cur_px
    spend = shares * cur_px
    trade = {
        "opened_at": now_iso(),
        "market_id": str(mid),
        "conditionId": cid,
        "slug": slug,
        "title": pos.get("title", "")[:90],
        "endDate": mk.get("endDate") or end_iso,
        "outcome": outcome, "outcome_idx": outcome_idx,
        "buy_price": round(cur_px, 4),
        "shares": round(shares, 4),
        "spend": round(spend, 4),
        "whale": whale_addr, "whale_label": whale_label,
        "whale_size_usd": round(whale_cur, 2),
        "whale_avg_price": round(whale_avg, 4),
        "signal_type": signal_type,
        "status": "open",
    }
    return ("buy", "ok", trade)


def run_once(state):
    snap_today = SNAP_DIR / datetime.now(timezone.utc).strftime("%Y-%m-%d")
    snap_today.mkdir(parents=True, exist_ok=True)

    new_signals = 0
    bought = 0
    for whale_addr, whale_label in WHALES.items():
        positions = fetch_whale_positions(whale_addr)
        if not positions:
            continue

        # Save raw snapshot (timestamped)
        snap_path = snap_today / f"{whale_label}_{int(time.time())}.json"
        snap_path.write_text(json.dumps(positions, default=str))

        # Diff vs last
        prev = state.get("last_snap", {}).get(whale_addr) or []
        diffs = diff_signals(prev, positions)
        for asset, pos, sigtype in diffs:
            if not is_esports_pos(pos):
                continue
            new_signals += 1
            decision, reason, trade = consider_signal(state, whale_addr, whale_label, asset, pos, sigtype)
            sig_row = {
                "ts": now_iso(),
                "whale": whale_addr, "whale_label": whale_label,
                "asset": asset, "slug": pos.get("slug"),
                "outcome": pos.get("outcome"),
                "whale_cur_value": pos.get("currentValue"),
                "signal_type": sigtype,
                "decision": decision, "reason": reason,
            }
            append_signal(sig_row)
            if decision == "buy" and trade:
                state["balance"] -= trade["spend"]
                state["open_positions"][trade["conditionId"]] = trade
                append_trade(trade)
                bought += 1
                log(f"  +COPY {whale_label} {trade['outcome']} @ ${trade['buy_price']} on {(trade['slug'] or '')[:60]}  spend=${trade['spend']:.2f}  whale_cur=${trade['whale_size_usd']:.0f}")
            else:
                if reason not in ("not_esports", "already_mirroring", "already_closed"):
                    log(f"  -skip [{whale_label}] {reason}: {(pos.get('slug') or '')[:55]}")

        # Update last snapshot for diff
        state.setdefault("last_snap", {})[whale_addr] = [
            {"asset": p.get("asset"), "size": p.get("size"),
             "slug": p.get("slug"), "outcome": p.get("outcome")}
            for p in positions
        ]

    # Cleanup old snapshots (keep 7 days)
    cutoff = (datetime.now(timezone.utc).timestamp() - 7 * 86400)
    for d in SNAP_DIR.glob("*"):
        if d.is_dir():
            try:
                day_ts = datetime.strptime(d.name, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
                if day_ts < cutoff:
                    for f in d.glob("*"): f.unlink()
                    d.rmdir()
            except: pass

    if new_signals or bought:
        save_state(state)
        log(f"  cycle: signals={new_signals} bought={bought} balance=${state['balance']:.2f} open={len(state['open_positions'])}")
    else:
        log(f"  cycle: 0 new signals, balance=${state['balance']:.2f} open={len(state['open_positions'])}")


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    state = load_state()
    log(f"starting — balance=${state['balance']:.2f} open={len(state['open_positions'])} POLL={POLL_INTERVAL_SEC}s")
    while True:
        try:
            run_once(state)
        except Exception as e:
            log(f"loop err: {e}")
        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    main()
