# SigForge Roadmap

> *What we will deliver with grant funding. Concrete milestones at 30/60/90
> days. Continuous beyond that.*

This roadmap is the answer to the question every grant reviewer asks: *"If
we fund you with $25K, what specifically gets built?"*

Each milestone has:
- **Output** — what is delivered.
- **Verification** — how the reviewer (or anyone) can confirm completion.
- **Funding allocation** — what portion of the grant supports it.

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

### Funding allocation: ~$8K of $25K

- $50 initial live capital (BASKET).
- $200 for sport-sniper live deployment after paper sample matures.
- ~$3K developer time for V2 SDK migration + live integration testing.
- $14 / year domain + SSL (negligible).
- ~$1K AWS infrastructure (1 month at current scale + headroom).
- ~$3K methodology refinement, audit reviews, dependency lockdown.

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

### Funding allocation: ~$10K of $25K

- $1K-$3K cumulative live capital across strategies (still small, scaling
  responsibly).
- ~$5K developer time for live deployment of YIELD-FARM and SPORT-SNIPER,
  per-strategy detail pages, blog content.
- ~$2K for community engagement (X account active, Polymarket Discord,
  user feedback iteration).

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

### Funding allocation: ~$5K of $25K

- ~$3K developer time for new strategy development and community engagement.
- ~$1K cumulative additional live capital.
- ~$1K reserves / unforeseen.

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
