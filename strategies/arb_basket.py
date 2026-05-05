#!/usr/bin/env python3
"""ARB PAPER SIMULATOR — симулює $500 demo-банк виконує arb_opportunities.

Loop кожні 5 хв:
  1. Читає нові entries з arb_opportunities.jsonl
  2. Якщо балансу досить + ще не "куплено" — "виконує" arb (списує cost, тримає legs)
  3. Перевіряє resolved.jsonl. Для відкритих позицій:
     - Знаходить winning leg (slug == winner_slug АБО bucket-match)
     - Додає shares × $1 до балансу
     - Логує realized P&L
  4. Cap: ARB_USD_DAY (з оригінального scanner)

Output:
  - data/arb_paper_state.json   — баланс + open_positions
  - data/arb_paper_trades.jsonl — виконані «трейди» + резолви
"""
import json, time, sys, os, re
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path("/opt/sigforge/weather")
DATA = ROOT / "data"
OPPORTUNITIES = DATA / "arb_opportunities.jsonl"
RESOLVED = DATA / "resolved.jsonl"
STATE = DATA / "arb_paper_state.json"
TRADES = DATA / "arb_paper_trades.jsonl"

# === Config ===
INITIAL_BALANCE = 500.00
DAILY_CAP = 40.00       # max spend per day
MIN_PROFIT_USD = 0.10   # skip arbs with profit < 10c (noise)
LOOP_SLEEP = 300        # 5 min


def log(m):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"{ts} arb_paper: {m}", flush=True)


def parse_dt(s):
    if not s: return None
    try: return datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    except Exception: return None


def event_key_from_slug(slug):
    if not slug: return None
    m = re.match(r'highest-temperature-in-([a-z-]+)-on-(\w+-\d+-\d+)', slug)
    return f"{m.group(1)}|{m.group(2)}" if m else None


def init_state():
    return {
        'balance': INITIAL_BALANCE,
        'initial_balance': INITIAL_BALANCE,
        'opened_at': datetime.now(timezone.utc).isoformat(),
        'day_spent': {},                # {date_str: spent}
        'open_positions': {},           # event_slug -> {legs:[...], cost, entered_at, projected_payout}
        'closed_positions': [],         # for stats
        'cumulative_pnl': 0.0,
        'cumulative_spent': 0.0,
        'cumulative_redeemed': 0.0,
        'opportunities_seen': set(),    # opportunity ts strings; persisted as list
    }


def load_state():
    if STATE.exists():
        try:
            d = json.loads(STATE.read_text())
            d['opportunities_seen'] = set(d.get('opportunities_seen', []))
            return d
        except Exception: pass
    return init_state()


def save_state(s):
    s2 = dict(s)
    s2['opportunities_seen'] = sorted(s['opportunities_seen'])
    tmp = str(STATE) + ".tmp"
    with open(tmp, 'w') as f: json.dump(s2, f, default=str, indent=2)
    os.replace(tmp, STATE)


def append_trade(rec):
    with open(TRADES, 'a') as f:
        f.write(json.dumps(rec, default=str) + '\n')


def today_str(dt=None):
    return (dt or datetime.now(timezone.utc)).strftime('%Y-%m-%d')


def latest_opportunities(state):
    """Tail-read arb_opportunities.jsonl for new entries."""
    if not OPPORTUNITIES.exists(): return []
    new = []
    sz = OPPORTUNITIES.stat().st_size
    with open(OPPORTUNITIES, 'rb') as f:
        f.seek(max(0, sz - 1_500_000))  # last 1.5MB
        f.readline()
        for line in f:
            try:
                r = json.loads(line)
                ts = r.get('ts')
                if ts and ts not in state['opportunities_seen']:
                    new.append(r)
            except Exception: pass
    return new


def load_resolved_index():
    """Build event_key → {winner_slug, winner_bucket}."""
    months = ['', 'january','february','march','april','may','june','july','august','september','october','november','december']
    idx = {}
    if not RESOLVED.exists(): return idx
    with open(RESOLVED) as f:
        for line in f:
            try:
                r = json.loads(line)
                c = r.get('city'); d = r.get('date')
                if c and d:
                    m = re.match(r'(\d+)-(\d+)-(\d+)', d)
                    if m:
                        ek = f"{c}|{months[int(m.group(2))]}-{int(m.group(3))}-{m.group(1)}"
                        idx[ek] = {'winner_slug': r.get('winner_slug'), 'winner_bucket': r.get('winner_bucket')}
            except Exception: pass
    return idx


def execute_arb(state, opp):
    """'Виконати' arb opportunity: списати cost, додати позицію."""
    event_slug = opp.get('eventSlug')
    cost = float(opp.get('totalCost') or opp.get('fresh_cost') or 0)
    payout = float(opp.get('payout') or 0)
    profit = payout - cost
    legs = opp.get('legs', [])
    n_legs = len(legs)

    if cost <= 0 or n_legs == 0:
        return False, 'invalid'
    if profit < MIN_PROFIT_USD:
        return False, f'profit_too_small_${profit:.2f}'
    if state['balance'] < cost:
        return False, 'insufficient_balance'

    # Daily cap check
    td = today_str()
    if state['day_spent'].get(td, 0) + cost > DAILY_CAP:
        return False, 'daily_cap'
    if event_slug in state['open_positions']:
        return False, 'already_open'

    # True arb: scanner sets minShares = floor(min(cost/sum_asks, etc))
    # which guarantees at least minShares of EVERY leg for cost.
    # When ANY leg wins, payout = minShares × $1.
    min_shares = float(opp.get('minShares') or 0)
    if min_shares <= 0:
        # Fallback: shares = cost / sum_of_asks (true arb math)
        sum_asks = sum(float(leg.get('bestAsk') or leg.get('fillPrice') or 0) for leg in legs)
        min_shares = (cost / sum_asks) if sum_asks > 0 else 0
    leg_records = []
    for leg in legs:
        ask = float(leg.get('bestAsk') or leg.get('fillPrice') or 0)
        leg_records.append({
            'slug': leg.get('slug'),
            'tokenId': leg.get('tokenId'),
            'ask': ask,
            'shares': min_shares,  # equal across all legs — that's what makes it arb
        })

    # Update state
    state['balance'] -= cost
    state['day_spent'][td] = state['day_spent'].get(td, 0) + cost
    state['cumulative_spent'] += cost
    state['open_positions'][event_slug] = {
        'event_slug': event_slug,
        'legs': leg_records,
        'cost': cost,
        'projected_payout': payout,
        'projected_profit': profit,
        'entered_at': datetime.now(timezone.utc).isoformat(),
    }
    state['opportunities_seen'].add(opp.get('ts'))

    append_trade({
        'ts': datetime.now(timezone.utc).isoformat(),
        'action': 'OPEN',
        'event_slug': event_slug,
        'cost': cost,
        'projected_payout': payout,
        'projected_profit': profit,
        'n_legs': n_legs,
        'balance_after': state['balance'],
    })
    return True, 'opened'


def check_resolutions(state, resolved_idx):
    """Для відкритих позицій — перевірити resolution + закрити."""
    closed = []
    for event_slug, pos in list(state['open_positions'].items()):
        ek = event_key_from_slug(event_slug)
        # try also bucket leg slug
        if not ek:
            for leg in pos['legs']:
                ek = event_key_from_slug(leg.get('slug'))
                if ek: break
        if not ek: continue
        res = resolved_idx.get(ek)
        if not res: continue

        winner_slug = res['winner_slug']
        # find which leg won
        winner_shares = 0
        for leg in pos['legs']:
            if leg.get('slug') == winner_slug:
                winner_shares = leg.get('shares', 0)
                break
        redeem = winner_shares * 1.0
        pnl = redeem - pos['cost']

        # Update state
        state['balance'] += redeem
        state['cumulative_redeemed'] += redeem
        state['cumulative_pnl'] += pnl
        state['closed_positions'].append({
            'event_slug': event_slug,
            'cost': pos['cost'],
            'redeem': redeem,
            'pnl': pnl,
            'winner_slug': winner_slug,
            'opened_at': pos['entered_at'],
            'closed_at': datetime.now(timezone.utc).isoformat(),
        })
        closed.append((event_slug, pnl, redeem))
        del state['open_positions'][event_slug]

        append_trade({
            'ts': datetime.now(timezone.utc).isoformat(),
            'action': 'CLOSE',
            'event_slug': event_slug,
            'winner_slug': winner_slug,
            'cost': pos['cost'],
            'redeem': redeem,
            'pnl': pnl,
            'balance_after': state['balance'],
        })
    return closed


def main():
    state = load_state()
    log(f"starting arb paper sim. balance=${state['balance']:.2f} "
        f"open={len(state['open_positions'])} closed={len(state['closed_positions'])} "
        f"cumPnL=${state['cumulative_pnl']:+.2f}")

    while True:
        try:
            # 1. Check new opportunities
            new_opps = latest_opportunities(state)
            opened = 0; skipped = 0
            for opp in new_opps:
                ok, reason = execute_arb(state, opp)
                if ok:
                    opened += 1
                    log(f"OPEN {opp.get('eventSlug','?')[:50]} cost=${opp.get('totalCost'):.2f} "
                        f"profit=${opp.get('payout',0)-opp.get('totalCost',0):.2f} "
                        f"balance=${state['balance']:.2f}")
                else:
                    skipped += 1
                    state['opportunities_seen'].add(opp.get('ts'))  # mark seen even if skipped

            # 2. Check resolutions
            resolved_idx = load_resolved_index()
            closed = check_resolutions(state, resolved_idx)
            for ek, pnl, redeem in closed:
                log(f"CLOSE {ek[:50]} pnl=${pnl:+.2f} redeem=${redeem:.2f} balance=${state['balance']:.2f}")

            save_state(state)
            wr = sum(1 for c in state['closed_positions'] if c['pnl'] > 0) / max(len(state['closed_positions']), 1)
            log(f"loop: new={len(new_opps)} opened={opened} skipped={skipped} closed={len(closed)} | "
                f"balance=${state['balance']:.2f} cumPnL=${state['cumulative_pnl']:+.2f} "
                f"open_pos={len(state['open_positions'])} closed_pos={len(state['closed_positions'])} WR={wr*100:.0f}%")
        except Exception as e:
            log(f"ERROR: {e!r}")

        time.sleep(LOOP_SLEEP)


if __name__ == '__main__':
    main()
