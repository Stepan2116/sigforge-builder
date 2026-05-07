# SPORT-SNIPER — Live-State Sports Resolution Capture

> *Buy decisive-state live sport markets at $0.92+ and hold to resolution.
> New vertical, deployed 2026-05-06.*

**Status:** 🟢 Paper validation — first cohort complete.
**Sample:** 22 trades opened, 20 closed, 2 still open · 100% win rate · Sharpe 2.41 · realized PnL +$11.28 on $200 spend (ROI +5.64%).
**Goal:** continue to 50 closed trades for variance confirmation; then promote to CANDIDATE phase.

SPORT-SNIPER is the first non-weather strategy in the SigForge portfolio.
It applies the YIELD-FARM logic (high-consensus capture) to live sport
markets, with two adaptations: lower entry threshold ($0.92+ vs $0.99+) and
faster polling (60s vs 300s) because sport-resolve windows are minutes,
not days.

---

## TL;DR

When a Polymarket sport market shows decisive game state (team leading 6-1
in MLB late innings, series 1-0 in best-of-3 esports), the favored side
trades at $0.92 – $0.99. Buying that side and holding to resolution captures
the gap between the priced uncertainty and the actual outcome.

Profit per trade ≈ $1.00 − buy_price (if win, target ~85-95% rate).

---

## Edge thesis

| Question | Answer |
|---|---|
| **What is the inefficiency?** | Decisive-state sport markets price the favored side too cheap relative to actual win probability. A team up 6-1 in MLB 7th inning rarely loses, but the market often quotes $0.92 – $0.96. |
| **Why does it persist?** | Retail leaves capital "on table" rather than locking small profits for hours. Some traders exit early to free capital. Liquidity providers price for residual variance + holding cost. |
| **What is the edge magnitude?** | Empirically TBD — first results in 24-72h. Theoretical: $0.04 – $0.08 per trade at $0.92 entry, 85-95% WR projected. |
| **What is the failure mode?** | Game-state reversal. Sports have higher tail variance than weather (comebacks happen). Limits per-trade size accordingly. |

---

## Algorithm

```
EVERY 60s:
  fetch all active markets (top by volume)
  for each market:
    skip unless market.sportsMarketType is set (filters to sports only)
    skip if game.ended (would not get fill in real life)
    skip if days_to_resolve > 7 or < 0
    skip if volume24h < $500
    skip if best_ask < $0.92 or best_ask > $0.999
    skip if any keyword in {referee, controversial, var-decision, playoff-format}
    skip if already in our state
    
    buy favored side at best_ask
    record trade with target = $1.00 - buy_price
```

Three implementation details:

**1. `sportsMarketType` detection.** Polymarket sport markets carry
`sportsMarketType: "moneyline"` and `feeType: "sports_fees_v2"` — explicit
indicators not present on other categories. We use these (not tag slugs,
which are not returned by the markets endpoint).

**2. Live game state extraction.** Each event has `events[].score`,
`events[].elapsed`, `events[].period`, `events[].live`, `events[].ended`.
Bot uses these for context logging and ended-game filtering.

**3. Faster polling.** Sport markets resolve within minutes of final whistle
on Polymarket. 60s polling is necessary to enter before close.

---

## Parameters

| Parameter | Value | Reason |
|---|---|---|
| Scan interval | 60s | Sport-resolve windows are minutes |
| Min entry price | $0.92 | Lower than YIELD-FARM (sport variance) |
| Max entry price | $0.999 | Avoid $1.00 (no profit margin) |
| Min volume 24h | $500 | Liquid sport markets |
| Max days to resolve | 7 | Sport markets are short-dated |
| Per-trade size | $10 | Smaller than YIELD-FARM (higher tail risk) |
| Max open exposure | $200 | Conservative for new vertical |

The smaller per-trade size ($10 vs YIELD-FARM's $20) reflects higher tail
variance in sports. We tighten if first 50 trades confirm low upset rate.

---

## Risk profile

**Best case:** Game outcome confirms decisive state. Profit = $1.00 −
buy_price. Realized within hours.

**Adverse case 1 — Comeback.** Trailing team rallies and wins. Loss =
buy_price. Comeback rate at decisive state empirically:
- MLB 5+ run leads after 7th: ~5% reversal rate
- BoX series 1-0 leads in esports: ~25-35% reversal rate

This is why per-trade size is conservative.

**Adverse case 2 — Suspended/postponed game.** Polymarket may resolve
ambiguously. Capital locked until manual review.

**Adverse case 3 — Platform issue.** Same as YIELD-FARM.

The strategy is intentionally smaller-sized than YIELD-FARM precisely
because sports have higher reversal variance. As empirical reversal rate
becomes known, sizing can adjust.

---

## Current performance

Deployed 2026-05-06 ~19:25 UTC. First wave of trades:

```
MLB Dodgers vs Astros        @ $0.945 | game live 6-1 | resolves in 7d
MLB Toronto vs Tampa Bay     @ $0.976 | game live 0-3 | resolves in 7d
MLB Brewers vs Cardinals     @ $0.981 | game live 5-0 | resolves in 7d
LoL KCB vs IJC (Game 2)      @ $0.995 | series 1-0    | resolves in 5h
... + 3 more added subsequently
```

First closes expected within 5-24 hours of deployment. Metrics file:
`paper_cointrick_sports_state.json`.

Initial validation period: 50 closed trades. Strategy advances or retires
based on Sharpe-per-trade > 0.5 threshold at sample 50.

---

## Known limitations

1. **Comeback variance.** Sports are not weather. Even at decisive state,
   reversals happen. The $0.92 threshold is calibrated for ~85% expected
   WR; if observed WR is < 80%, threshold rises to $0.95.

2. **Resolution latency.** Some sport markets resolve hours after final
   whistle (UMA dispute window). Capital tied up longer than play time.

3. **Tag dependency.** Strategy relies on Polymarket maintaining
   `sportsMarketType` field. If schema changes, detection breaks.

4. **No live-game streaming.** Bot reads cached game state from market
   payload. Not real-time score updates. Decisions on snapshot data.

5. **No reverse-mirror logic.** Strategy only goes long the favorite. Could
   theoretically short the underdog at $0.05 if mispriced; not currently
   implemented.

---

## Scaling plan

### Phase 1 (current): First 50 closed trades
- Establish baseline WR, avg PnL, Sharpe-per-trade.
- Identify reversal patterns (which sports? which periods?)

### Phase 2: Parameter tuning
- A/B test threshold $0.95 vs $0.92 (filter quality)
- A/B test by sport type (MLB vs basketball vs esports)
- Backtest if historical sport market data accessible

### Phase 3: Selective live deployment
- Deploy only winning sport-types live
- $25 starting live capital
- Builder Code attribution from day 1

### Phase 4: Multi-sport scaling
- Add new sport detection patterns (NBA, NHL, soccer)
- Scale capital in halving steps once each sport-vertical confirms edge

---

## Why this strategy is unique to SigForge

SigForge's other strategies (BASKET, YIELD-FARM) are weather-domain or
cross-domain. SPORT-SNIPER is the first **vertical-specific** strategy that
exploits a Polymarket schema feature (`sportsMarketType`).

This matters for grant context: it demonstrates we are not a single-vertical
team. We can identify edge sources across categories, validate them in
isolation, and operate them in parallel with the rest of the portfolio.

---

## See also

- Methodology framework: [`../docs/METHODOLOGY.md`](../docs/METHODOLOGY.md)
- Implementation reference: [`yield_farm.py`](yield_farm.py) (cousin strategy)
- Live metrics: https://sigforge.dev/showcase.html
