# SigForge — Multi-Strategy Validation Framework for Polymarket

[![CI](https://github.com/Stepan2116/sigforge-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/Stepan2116/sigforge-builder/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Showcase](https://img.shields.io/badge/showcase-live-00ff88.svg)](http://18.178.69.19/showcase.html)
[![Sponsor](https://img.shields.io/github/sponsors/Stepan2116?label=Sponsor&logo=github)](https://github.com/sponsors/Stepan2116)

![SigForge showcase preview](frontend/showcase-preview.svg)

> *Disciplined validation of original prediction-market strategies. Every
> decision logged. Every claim backed by data. Open-source plan
> post-validation.*

**Public showcase:** http://18.178.69.19/showcase.html
**Tour mode:** http://18.178.69.19/showcase.html?tour=1 (10-step guided walkthrough)
**Pitch deck:** [`application/pitch-deck.html`](application/pitch-deck.html) (5 slides, print-to-PDF)
**Architecture:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) (Mermaid system diagram)
**Roadmap:** [`docs/ROADMAP.md`](docs/ROADMAP.md) (30/60/90 day milestones)
**Geography:** EU
**Contact:** riznykstepan@gmail.com
**Builder Code:** `0x6a386ecc3a926b109e131d736ab0053cb6bb6745638ddefa2693247db62d8ba1`

---

## Track record (verified, live)

Metrics fetched from production state files. `analyze_bots.py` regenerates
this table from disk in under a second.

| Strategy | Vertical | Closed trades | Win rate | Sharpe / trade | Realized PnL |
|---|---|---|---|---|---|
| **BASKET** (math arb) | Weather | 9 | **100.0%** | **3.10** | +$5.93 |
| **YIELD-FARM** (cointrick) | Cross-domain | 23 | **100.0%** | 1.21 | +$2.26 |
| **SPORT-SNIPER** (new today) | Sports late-game | 0 (7 open) | — | — | — |
| **COPY-TRADER** | Esports specialist | 0 | — | — | — |

**Aggregate (closed trades only):** 32 closed · 100% win rate · peak Sharpe 3.10.

The BASKET Sharpe of 3.10 is professional quant-fund grade. Sample is small
(9 closed trades) but the edge is structural, not behavioral — see
`strategies/BASKET.md` for the full thesis.

---

## What we built

A full-stack prediction-market validation harness:

### Strategies (paper-validated, see `strategies/`)
- **BASKET** — multi-leg arbitrage on weather buckets. Math-guaranteed
  positive PnL when sum-of-asks < $1.00. Deep-dive: [BASKET.md](strategies/BASKET.md).
- **YIELD-FARM** — high-consensus capture at $0.99+ across general markets.
  Conservative yield, high reliability. Deep-dive: [YIELD-FARM.md](strategies/YIELD-FARM.md).
- **SPORT-SNIPER** — live-state sports markets at $0.92+ during decisive game
  state (deployed 2026-05-06). Deep-dive: [SPORT-SNIPER.md](strategies/SPORT-SNIPER.md).
- **COPY-TRADER** — verified specialist whale mirror with risk gate.

All strategies are **original work** — no forked dependencies.

### Infrastructure (see `tools/`)
- **`paper_watchdog.py`** — process health monitor. Detects silent failures
  (process down, balance drained, state stale, HALT flag) across the entire
  bot stack. Catches Wellington-class bugs before they accumulate losses.
- **`backtest.py`** — strategy variant replay against archived data.
  Validates patches in 1 second instead of 30 days paper trading. Used for
  falsification, not pattern fishing.

### Live dashboard (see `frontend/`)
- Real-time PnL, Sharpe, win-rate, drawdown across all strategies.
- 10-step guided tour mode (`?tour=1`).
- Mobile-responsive.
- Refreshed every 30 seconds with freshness indicator.

### Knowledge base (Obsidian vault, auto-synced)
- 200+ audit notes covering every strategic decision.
- Trading research synthesis: scalping fundamentals, Smart Money Concepts,
  Wyckoff theory, auction microstructure, risk management — adapted for
  prediction-market dynamics.

---

## Methodology

Every strategy follows a structured lifecycle: `INCUBATE → PAPER → CANDIDATE
→ LIVE → SCALE / KILL`. Promotion between phases requires explicit
quantitative gates (sample size, Sharpe threshold, win-rate confirmation,
risk-of-ruin under stress).

**Three principles:**

1. **Hypothesis-first** — every strategy or patch starts with a written
   thesis. Logged before code is written. Post-mortems compare reality to
   prediction.
2. **Multi-variant testing** — patches run as parallel A/B/C variants with
   isolated capital. PnL deltas attribute outcome to specific design
   decisions, not ambient market noise.
3. **Three-layer risk** — per-trade caps, per-strategy daily limits,
   account-level drawdown circuit breakers. Defense in depth.

Full framework: [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md).

---

## What makes this different

Most retail prediction-market bots are single-strategy point solutions.
SigForge is **infrastructure-first**:

| | Typical retail bot | SigForge |
|---|---|---|
| Strategy count | 1 | 4 in active validation |
| Audit trail | Spreadsheet at best | 200+ structured notes |
| Patch testing | "Deploy and pray" | Backtester + isolated A/B variants |
| Failure detection | Manual checking | Watchdog with alerting |
| Risk management | Per-trade only | Three independent layers |
| Open-source plan | Closed | MIT post-validation |
| Methodology doc | None | 13KB (`docs/METHODOLOGY.md`) |

This matters because **most retail prediction-market traders lose for
structural reasons** (no hypothesis, no controlled tests, no risk floor).
SigForge fixes all three.

---

## What grant funding will accelerate

**Funding ask: $10K** — sized for lean 90-day execution. Most infrastructure
is already built (5 weeks self-funded). The grant accelerates live
deployment, not bootstraps from zero. Stretch tier of $25K (if available)
accelerates BASKET capital scaling within the same window — see
[`docs/ROADMAP.md`](docs/ROADMAP.md) for line-item breakdown.

Listed in priority order:

### 1. Live deployment of validated strategies with Builder Code
- BASKET first — math-guaranteed risk-free.
- ~$25 starting live capital, scaling in halving steps to ~$200 once each
  step holds (stretch tier scales to ~$1,000).
- Every order tagged with `builderCode` field — attributed volume back to
  Polymarket from day 1.

### 2. V2 SDK migration across all bots
- Current py-clob-client v0.34.6 lacks Builder Code field.
- Migration to v2 unblocks live deployment for all current strategies.

### 3. Public domain + brand
- IP-address dashboard demo is acceptable for grant review, not for public
  launch. Domain registration + nginx config for cleaner external presence.

### 4. Open-source release
- MIT license on validated strategy library (BASKET, YIELD-FARM,
  SPORT-SNIPER) with full audit-note replication so retail can replicate
  disciplined approaches end-to-end.
- Backtester and watchdog included.

### 5. Continuous strategy expansion
- Resolution-clock arb extensions (cross-domain).
- Sports vertical expansion (NBA, NHL, soccer detection patterns).
- Cross-platform monitoring (Polymarket vs Kalshi where accessible).

---

## Operational status (as of this commit)

- **Backend:** AWS Lightsail Tokyo · 25+ pm2 processes · 24/7 since April 2026.
- **Live paper bots:** 6 strategies + 4 archived/killed variants.
- **Public showcase URL:** http://18.178.69.19/showcase.html (tour available).
- **Watchdog:** running, log-only mode (Telegram alerts can be enabled via env).
- **Builder Code:** obtained, integration designed, awaiting V2 migration.
- **Vault:** 200+ Obsidian notes auto-synced to AWS via cron.

---

## Repository layout

```
sigforge-builder/
├── .github/workflows/
│   └── ci.yml             GitHub Actions: pytest + lint, Python 3.10/3.11/3.12
├── application/           Grant submission materials
│   ├── form-fields.md     Paste-ready submission text + verification cheatsheet
│   └── pitch-deck.html    5-slide deck, print-to-PDF
├── docs/
│   ├── METHODOLOGY.md     Full validation framework (13 KB, 11 sections)
│   ├── ARCHITECTURE.md    System diagram (Mermaid) + layer-by-layer description
│   ├── ROADMAP.md         30/60/90 day milestones with grant fund allocation
│   └── COMPARISON.md      Concrete differentiators vs typical retail Polymarket bots
├── frontend/              Public showcase dashboard
│   ├── README.md
│   └── showcase.html
├── strategies/            Trading strategy implementations + specs
│   ├── README.md          Index + status table
│   ├── BASKET.md          Multi-leg arb deep-dive (Sharpe 3.10)
│   ├── YIELD-FARM.md      Consensus capture deep-dive
│   ├── SPORT-SNIPER.md    Live-state sports deep-dive
│   ├── arb_basket.py
│   ├── yield_farm.py
│   ├── sport_sniper.py
│   └── copy_trader.py
├── tools/                 Infrastructure (non-trading)
│   ├── README.md
│   ├── paper_watchdog.py  Process health monitor (env-configurable)
│   └── backtest.py        Strategy variant replay
├── tests/                 Unit tests (23 cases, all passing)
│   └── test_backtest.py
├── LICENSE                MIT
└── README.md              (this file)
```

---

## Reviewer notes

This pitch is **honest about scope:**

- We claim only original strategies. Forked or experimental variants are
  not in this repository.
- Track record is from live paper trading. Sample sizes are small but real.
- BASKET's Sharpe 3.10 reflects 9 closed trades — small sample. The reason
  for confidence is structural (math identity), not statistical.
- All claims are independently verifiable: visit the showcase URL, run
  `tools/backtest.py` against the data, read the audit notes.

**To verify in 5 minutes:**

1. Open http://18.178.69.19/showcase.html in incognito — no auth required.
2. Click "Start Guided Tour" — 10 steps explain everything.
3. Browse `strategies/BASKET.md` for the Sharpe 3.10 thesis.
4. Browse `docs/METHODOLOGY.md` section 3 for the validation gates.

---

## License

MIT (will apply to validated strategy library after release).

Repository structure, methodology document, and tools are openly available
for reference.
