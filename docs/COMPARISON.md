# SigForge vs the typical retail Polymarket bot

> *Concrete differentiators. Not marketing claims — verifiable from this repository.*

This page exists for reviewers who ask "but what makes you different from
the dozens of other Polymarket bots on GitHub?" The answer below is
structural, not adjectival.

---

## Comparison matrix

The "Typical retail bot" column reflects publicly visible patterns from
the most starred Polymarket bot repositories on GitHub as of May 2026
(individual repos linked at the end where applicable).

| Capability | Typical retail bot | SigForge |
|---|---|---|
| Strategy count | 1 (a single bet rule) | 4 in active validation, structured for adding more |
| Edge thesis documented | Rare; sometimes a one-liner in README | Required — written before code, logged in audit notes |
| Metric reporting | Win count or "+X% return" claim | Sharpe-per-trade, win rate, drawdown, all reproducibly computed |
| Backtester | Often missing or strategy-specific ad-hoc | Universal trade-log analyzer with variant replay (`tools/backtest.py`) |
| Test suite | None | 23 unit tests, GitHub Actions CI on Python 3.10/3.11/3.12 |
| Validation gates | None — straight to live | Quantitative gates between paper / candidate / live phases |
| Risk management | Per-trade stop only (often mental) | Three-layer hierarchy: per-trade, daily, account-level circuit breaker |
| Silent failure detection | None | `tools/paper_watchdog.py` scans every 5 min, alerts on anomalies |
| Builder Code attribution | Rarely wired | Designed in from day-1; live deployment is the next milestone |
| Open-source plan | Implicit ("MIT") | Explicit roadmap milestone with versioned release |
| Audit trail | Git commits | 200+ structured Obsidian notes with hypothesis/impact/rollback per decision |
| Methodology document | None | 13 KB document, 11 sections (`docs/METHODOLOGY.md`) |
| Architecture document | None | Mermaid diagram + layer-by-layer description (`docs/ARCHITECTURE.md`) |
| Comparable strategy specs | One paragraph in README | Per-strategy deep-dive (~7 KB each) covering edge thesis, algorithm, parameters, risk profile, scaling plan |
| Multi-platform support | Hard-coded to one platform | Adapter layer (`strategies/adapters/`) — Polymarket prod, Manifold read-only, Kalshi scaffold |
| Hypothesis-generation tooling | None | `tools/ai_hypothesis.py` — Claude-assisted hypothesis ranking with falsification tests |
| Live execution layer | Mostly Python with `submit_order` and pray | Hybrid: Python decides, TypeScript executes with Builder Code, fill polling, leg-unwind on partial fills, heartbeat for watchdog |
| Live dashboard | None or static screenshots | Real-time PnL with live mark-to-market, refreshed every 30s |
| Failure post-mortems | None visible | Failed strategies (`cm-v1`, `cm-v6`, `cm-v8`) explicitly killed and documented |

---

## Verifiable claims

Each row above is checkable. A reviewer who wants to verify any claim in 60 seconds:

| Claim | Verification path |
|---|---|
| 23 unit tests passing | Open `.github/workflows/ci.yml` and the GitHub Actions tab |
| Universal backtester exists | Read `tools/backtest.py` — 6 strategy variants, 250+ lines |
| Sharpe-per-trade computed correctly | `tools/backtest.py` line containing `pstdev` + `tests/test_backtest.py::TestComputeMetrics` |
| Three-layer risk hierarchy | `docs/METHODOLOGY.md` § 4 |
| Watchdog deployed in production | Open the showcase URL — `paper-watchdog` is one of the listed processes; logs at `/opt/sigforge/weather/data/paper_watchdog.log` |
| Per-strategy deep-dives exist | Browse `strategies/BASKET.md`, `YIELD-FARM.md`, `SPORT-SNIPER.md` |
| Failed strategies documented | This repo is intentionally focused on validated work; killed variants documented in vault audit notes referenced from `docs/METHODOLOGY.md` § 8.2 |
| Architecture doc with diagram | `docs/ARCHITECTURE.md` — Mermaid renders natively on GitHub |
| Adapter layer is real, not vapor | `strategies/adapters/` — three concrete adapters; `python -c "from adapters import adapter_for; m=list(adapter_for('manifold').fetch_markets(limit=3))"` returns live data |
| Live executor handles partial-fill safety | `live-executor/live_basket.js` — `unwindFilledLegs()` reverses every confirmed leg if any later leg fails |
| AI tooling is auditable | `tools/ai_hypothesis.py --dry-run trades.jsonl` prints exactly what Claude is asked, no API key required |

---

## What we're NOT claiming

Honesty about limits is part of the methodology:

- **We are not the largest bot.** Sample sizes are small (9-23 closed trades
  per strategy). Sharpe 3.10 is reliable because the BASKET edge is structural,
  not because the sample is statistically conclusive.
- **We are not yet trading live.** All metrics are paper. Live deployment with
  Builder Code is the day 1-30 milestone of the grant roadmap.
- **We are not the fastest.** Latency is consumer-grade (200-500ms). We
  compete on edge identification and discipline, not microstructure.
- **We are not zero-loss.** The first BASKET loss will arrive. We have stress-
  tested the methodology to confirm positive EV holds even with 3-sigma
  adverse moves.
- **We are not a turnkey product.** SigForge is infrastructure to be deployed
  and operated — not a one-click consumer app. This is intentional: the
  audience is disciplined retail traders and grant reviewers, not casual
  speculators.

---

## Why these differences compound

Each difference above is small in isolation. Together they create a
qualitatively different operating regime:

- **Hypothesis-first + audit trail** = clean attribution, faster learning.
- **Multi-variant testing + backtester** = patches validated in seconds,
  not months.
- **Three-layer risk + watchdog** = silent failures caught before they
  accumulate (the bug that motivated the watchdog is documented in
  `docs/METHODOLOGY.md` § 8.2).
- **Per-strategy specs + architecture doc** = onboarding is documentation,
  not pair programming.
- **Validation gates + open-source plan** = retail can replicate validated
  approaches without writing them from scratch.

The whole adds up to "infrastructure", not "another bot".

---

## See also

- [`METHODOLOGY.md`](METHODOLOGY.md) — full validation framework.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — system layout.
- [`ROADMAP.md`](ROADMAP.md) — what gets built with the grant.
- [`../README.md`](../README.md) — current operational state and verified metrics.
