# SigForge Roadmap

> *What we will deliver with grant funding. Concrete milestones at 30/60/90
> days. Continuous beyond that.*

This roadmap is the answer to the question every grant reviewer asks:
*"If we fund you, what specifically gets built?"*

The plan is sized for **$10K lean execution** — sufficient because most of
the infrastructure is already built (backtester, watchdog, methodology,
strategy specs, live showcase — five weeks of self-funded work). The grant
accelerates live deployment, not bootstraps from zero.

A **stretch tier of $20-25K** (if available) accelerates BASKET capital
scaling from $200 to $1,000 within the same 90-day window and supports
community programming. The execution path is the same; only the live-trade
step sizes change.

Each milestone has:
- **Output** — what is delivered.
- **Verification** — how the reviewer (or anyone) can confirm completion.
- **Funding allocation (lean / stretch)** — split for $10K vs $25K tier.

Estimates are conservative on purpose. Methodology overhead is a feature,
not a bug — see [`METHODOLOGY.md`](METHODOLOGY.md).

---

## Day 0 — current state (this commit)

### Already delivered

- ✅ Working multi-strategy paper validation framework (4 strategies live).
- ✅ Sharpe 3.10 verified on BASKET (math arb), 100% WR.
- ✅ Sharpe 1.21 verified on YIELD-FARM, 100% WR over 23 closed trades.
- ✅ SPORT-SNIPER (new vertical) deployed and operating.
- ✅ Backtester (universal trade-log analyzer + variant replay).
- ✅ Process watchdog (silent failure detection).
- ✅ Live public showcase with real-time metrics, Sharpe column, tour mode.
- ✅ Methodology doc (13 KB, 11 sections).
- ✅ Strategy deep-dive specs (3 documents).
- ✅ Architecture documentation with system diagram.
- ✅ 200+ Obsidian audit notes auto-synced to AWS.
- ✅ Builder Code obtained, integration designed.

This represents ~5 weeks of focused work. No grant funds expended.

---

## Days 1-30 — Live Builder Code attribution

**Theme:** First attributed live volume. Validate paper → live transfer.

### Milestones

| # | Output | Verification |
|---|---|---|
| 1.1 | py-clob-client v2 SDK migration completed | Bot v2 deployment with new SDK; Builder Code field in every CLOB order |
| 1.2 | BASKET ported to live with Builder Code | `builderCode = 0x6a386ecc...` in transaction logs |
| 1.3 | First $50 live trade executed and resolved | Polymarket transaction hash, attributed volume visible |
| 1.4 | Live BASKET PnL within ±25% of paper extrapolation | Compared via `analyze_bots.py` over 30 days |
| 1.5 | Domain registered + SSL configured | https://sigforge.dev/ resolves |
| 1.6 | GitHub Actions CI on backtester + tools | Green badge in README |

### Funding allocation

| Item | Lean ($10K) | Stretch ($25K) |
|---|---|---|
| Initial BASKET live capital | $25 | $50 |
| YIELD-FARM live capital | $25 | $50 |
| Developer time (V2 SDK + live integration) | ~$2.5K | ~$3K |
| Domain + SSL | $14 | $14 |
| AWS infrastructure (3 months) | $200 | $400 |
| Methodology + audit work | ~$1K | ~$2K |
| **Subtotal phase 1** | **~$3.7K** | **~$5.5K** |

### Risk

- V2 SDK has API differences vs v0.34.6. Migration may take longer than
  4 hours of focused work; we have buffer. Live trades not deployed until
  migration tested in isolation.

---

## Days 31-60 — Multi-strategy live + scale

**Theme:** Three live strategies attributing volume. Scale BASKET capital
in halving steps.

### Milestones

| # | Output | Verification |
|---|---|---|
| 2.1 | YIELD-FARM live with Builder Code | Transaction hashes show `builderCode` field |
| 2.2 | SPORT-SNIPER live with Builder Code | Live sport trades visible on Polymarket |
| 2.3 | BASKET capital scaled to $200 (×4 from $50) | If Sharpe holds > 1.5 across step transitions |
| 2.4 | Public open-source release v1.0 (MIT) | Strategy library + backtester + watchdog publicly versioned |
| 2.5 | Per-strategy detail page on showcase | One-click drilldown from main dashboard |
| 2.6 | First public blog post explaining BASKET edge | Linked from showcase + GitHub |

### Funding allocation

| Item | Lean ($10K) | Stretch ($25K) |
|---|---|---|
| BASKET capital scaling (halving steps) | up to $200 | up to $1,000 |
| SPORT-SNIPER live capital | $50 | $200 |
| Developer time (deployment, detail pages, content) | ~$3K | ~$5K |
| Community engagement (X, Discord, blog) | $500 | ~$2K |
| **Subtotal phase 2** | **~$3.7K** | **~$8.2K** |

### Strategy gates that must pass before scaling

- Live PnL within ±25% of paper extrapolation across 30 days.
- No unexplained losses (every loss explained by hypothesis).
- Sharpe-per-trade stays > 1.0 in live conditions.
- Watchdog uptime > 99%.

If any gate fails, capital is reduced or strategy halted. No
"yolo-and-hope" scaling.

---

## Days 61-90 — Continuous improvement loop + open-source community

**Theme:** Full production discipline. Iterate on validated strategies.
Onboard external contributors.

### Milestones

| # | Output | Verification |
|---|---|---|
| 3.1 | Resolution-clock arb extension (cross-domain) deployed | New strategy variant with paper-validated edge |
| 3.2 | Cross-platform monitoring (Polymarket vs Kalshi where accessible) | Public dashboard column |
| 3.3 | Public retrospective post: "What worked, what failed, what's next" | Blog + GitHub |
| 3.4 | First external contribution accepted | PR merged from non-Stepan2116 contributor |
| 3.5 | Documentation suite complete | All strategies + tools + methodology cross-linked |
| 3.6 | Cumulative attributed volume > $X (TBD with Polymarket) | Polymarket Builder dashboard |

### Funding allocation

| Item | Lean ($10K) | Stretch ($25K) |
|---|---|---|
| New strategy development time | ~$1.5K | ~$3K |
| Cumulative additional live capital | $300 | ~$1K |
| Reserves / unforeseen | ~$800 | ~$2K |
| **Subtotal phase 3** | **~$2.6K** | **~$6K** |
| **Total across 90 days** | **~$10K** | **~$19.7K** |
| Stretch reserve held | — | ~$5.3K (unallocated, performance-gated) |

### Reserve

~$2K reserve held against:
- Unexpected V2 SDK migration complications.
- Adverse market regime requiring strategy rework.
- Infrastructure scaling needs (additional AWS capacity).

---

## Beyond 90 days (vision)

After the 90-day grant period, SigForge continues with:

- **Continuous strategy expansion.** New verticals as Polymarket adds
  market types (election micro-markets, political events, crypto futures).
- **Community-driven development.** External contributors add strategies
  using the validated framework. Each contribution goes through the same
  validation gates.
- **Public methodology adoption.** The framework becomes the reference
  for disciplined retail prediction-market trading.
- **Sustainable revenue.** Builder Code attribution generates volume back
  to Polymarket (their interest); SigForge captures small per-trade margins
  on validated strategies (our interest). Both align long-term.

---

## What success looks like at day 90

A grant reviewer reading this in three months should be able to verify:

1. **3+ strategies live with Builder Code attribution.** Transaction logs
   visible. Cumulative attributed volume measured.
2. **Sharpe holds in live.** Live metrics within ±25% of paper baseline.
   Verified via `analyze_bots.py` on production data.
3. **Open-source release stable.** v1.0 published, MIT-licensed, with
   reproducible setup instructions. External users can run it.
4. **Methodology proven.** At least one strategy that *failed* gate criteria
   was killed. At least one strategy that *passed* was scaled. Both
   documented in audit notes.
5. **Community engagement.** Public blog posts, X presence, first external
   PR, Polymarket Discord activity.

Failure to deliver any of these triggers a public retrospective explaining
what happened and what we learned. We treat post-mortems as deliverables.

---

## Why this roadmap is realistic

Three reasons we believe these milestones are achievable:

### 1. Methodology already in place

The hardest infrastructure (validation framework, monitoring, audit
discipline) is already built. Day 1 starts with an operational system,
not a clean slate.

### 2. Conservative scaling

We promote strategies in halving steps with quantitative gates. We do not
deploy 5 strategies live simultaneously without testing. We do not scale
capital 10× and "see what happens." Each step is validated before the
next.

### 3. Honest about uncertainty

We do not claim "$X will be earned" or "Y win rate will hold at 100×
volume." Live trading at scale will reveal frictions paper trading
hides. The roadmap accommodates this — the 90-day reserve plus the
halving-step scaling create buffer for revisions.

---

## See also

- [`METHODOLOGY.md`](METHODOLOGY.md) — validation gates and lifecycle.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — system layout.
- [`../README.md`](../README.md) — project overview and current track record.
- [`../application/form-fields.md`](../application/form-fields.md) — submission text.
