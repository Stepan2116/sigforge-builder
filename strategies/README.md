# SigForge — Original Strategies

This directory contains the original prediction-market strategies developed for SigForge. All strategies are paper-validated before any live deployment.

## Strategies

### `arb_basket.py` — BASKET (Multi-Leg Arbitrage)
**Concept:** Polymarket weather events resolve as exactly one bucket = $1.00 (others = $0.00). When the sum of all bucket asks for an event drops below $1.00, buying every bucket guarantees a payout regardless of outcome.

**Math:**
```
For an N-bucket event with asks [a_1, a_2, ..., a_N]:
  if sum(a_i) < 1.00:
    buy 1 share of each bucket → cost = sum(a_i)
    payout = $1.00 (one bucket must win)
    profit = $1.00 - sum(a_i)
```

**Status:** 100% win rate (9/9 closed), +$5.93 realized, 3 active positions.

**Risk profile:** Math-guaranteed. Only failure mode is platform-level (e.g., resolution delay, no buyer for resolved positions).

---

### `yield_farm.py` — YIELD-FARM (cointrick)
**Concept:** Scan all active markets every 5 minutes. When a market shows overwhelming consensus (one outcome ≥ $0.99), buy that side. Hold to resolution. Profit ≈ $1.00 - $buy_price.

**Trade-off:** Tiny per-trade profit (~$0.005) but very high reliability when filtered properly.

**Status:** 100% win rate (18/18 closed), 25 active positions.

**Risk profile:** Tail risk — overwhelming consensus markets occasionally do reverse (e.g., last-minute event surprises). Position sizing capped to limit any single tail-loss impact.

---

### `copy_trader.py` — COPY-TRADER (esports specialist mirror)
**Concept:** Monitor verified specialist whales every 60 seconds. When a NEW position appears (or size increases significantly) on their wallet, mirror it with our paper capital. Filters: position size threshold, market end-date threshold, exposure caps, daily limits.

**Note:** Whale addresses redacted in public repo for privacy. The framework supports arbitrary specialist lists.

**Risk profile:** Specialist signal can decay. Mirror-lag can flip the trade unfavorably if our entry is much later than the specialist's. Filter discipline reduces but does not eliminate this.

---

### Methodology notes

Each strategy follows the SigForge methodology:
1. **Hypothesis-driven** — every entry rule is documented with the hypothesis it tests
2. **Audit-logged** — every trade decision is recorded in audit notes (separate vault, not in repo)
3. **Multi-variant** — patches and improvements run as parallel A/B/C tests with isolated capital
4. **Paper-first** — no live deployment until paper validation crosses risk gates

See [`../docs/METHODOLOGY.md`](../docs/METHODOLOGY.md) for the full validation framework.
