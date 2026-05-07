# SigForge — Strategy Library

Original prediction-market strategies developed for SigForge. Each strategy is
paper-validated under the SigForge methodology before any live deployment with
Builder Code attribution.

---

## Strategy index

| # | Strategy | Vertical | Status | Closed trades | WR | Sharpe/trade | PnL |
|---|---|---|---|---|---|---|---|
| 1 | [BASKET](BASKET.md) | Weather arb | 🟢 Validated | 9 | 100% | **3.10** | +$5.93 |
| 2 | [YIELD-FARM](YIELD-FARM.md) | Cross-domain consensus | 🟢 Validated | 23 | 100% | 1.21 | +$2.26 |
| 3 | [SPORT-SNIPER](SPORT-SNIPER.md) | Sports late-game | 🟡 New (today) | 0 | — | — | — |
| 4 | [COPY-TRADER](#copy-trader) | Esports specialist mirror | 🟡 Filter debug | 0 | — | — | — |

Live metrics: https://sigforge.dev/showcase.html (refreshed every 30s)

---

## Implementation files

This directory contains the Python implementation of each strategy:

| File | Strategy |
|---|---|
| [`arb_basket.py`](arb_basket.py) | BASKET — multi-leg arbitrage |
| [`yield_farm.py`](yield_farm.py) | YIELD-FARM — cross-domain consensus |
| [`copy_trader.py`](copy_trader.py) | COPY-TRADER — esports specialist mirror |

SPORT-SNIPER (deployed 2026-05-06) shares the YIELD-FARM core logic with
sport-specific filters and faster polling. See SPORT-SNIPER.md for details.

---

## Deep-dive docs

Each strategy has a dedicated specification document covering edge thesis,
algorithm walkthrough, parameters, risk profile, current metrics, known
limitations, and scaling plan:

- 📘 [BASKET.md](BASKET.md) — Math-guaranteed arbitrage. Sharpe 3.10.
- 📘 [YIELD-FARM.md](YIELD-FARM.md) — Conservative consensus capture.
- 📘 [SPORT-SNIPER.md](SPORT-SNIPER.md) — Live-state sports edge.

---

## Methodology

Every strategy follows the SigForge methodology:

1. **Hypothesis-driven** — every entry rule is documented with the hypothesis
   it tests, before code is written.
2. **Audit-logged** — every trade decision recorded in audit notes (Obsidian
   vault, separate from this repo for size reasons).
3. **Multi-variant testing** — patches and improvements run as parallel
   A/B/C variants with isolated capital.
4. **Paper-first, live-later** — no live deployment until paper validation
   crosses risk gates (≥ 20 closed trades, Sharpe > 0.5, etc.).

See [`../docs/METHODOLOGY.md`](../docs/METHODOLOGY.md) for the full validation
framework.

---

## COPY-TRADER

(Brief inline note since this strategy does not yet warrant a full deep-dive.)

**Concept:** Monitor verified specialist whales every 60 seconds. When a NEW
position appears (or size increases significantly) on their wallet, mirror
it with our paper capital.

**Filters:** position size threshold, market end-date threshold, exposure
caps, daily limits.

**Note:** Whale addresses redacted in public repo for privacy. The framework
supports arbitrary specialist lists.

**Current status:** Filter logic is overly restrictive — over 1,800 whale
signals received with 0 trades executed in current paper run. Whale's actual
strategy (high-consensus $0.97-$0.99 entries) does not match our forecast-tier
filter. Strategy is paused pending revised filter design.

This is documented openly because failure-to-execute is itself an audit
trail. Capital is not lost; the bug is captured.

---

## Validation lifecycle

```
INCUBATE → PAPER → CANDIDATE → LIVE → SCALE / KILL
```

See [METHODOLOGY.md](../docs/METHODOLOGY.md) for the full lifecycle and
quantitative gates between phases.

Current phase per strategy:

| Strategy | Phase |
|---|---|
| BASKET | Late-stage paper (ready for live) |
| YIELD-FARM | Mid-stage paper (more sample needed) |
| SPORT-SNIPER | Early-stage paper (just deployed) |
| COPY-TRADER | Investigation (filter mismatch) |
