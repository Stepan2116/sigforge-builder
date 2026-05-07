# SigForge — Gitcoin Grants Application

> *Adapted for Gitcoin's Open Source Software (OSS) round. Emphasizes
> public-good infrastructure and quadratic-funding-friendly framing.*

---

## Where to apply

**Gitcoin Grants — OSS round** (grants.gitcoin.co)
- Focus: open-source web3 / Ethereum-ecosystem software
- Mechanism: Quadratic Funding — many small contributors > few large
- Round cadence: typically quarterly; check current at grants.gitcoin.co
- Application format: Grant page with description, image, links
- Funding: matched from a pool, scales with unique contributors

**Why this fits SigForge:**
- We are 100% open-source (MIT license).
- The framework runs on Polygon (Ethereum L2) — within ecosystem.
- Polymarket and prediction markets broadly are part of the on-chain
  capital allocation infrastructure web3 cares about.

---

## Quadratic-funding-friendly framing

Gitcoin Grants reward **broad community signal** more than absolute dollar
asks. Optimize for:
- Small, real ask (not $25K — that scares the long-tail funders)
- Public good narrative (not "fund our profitable bot")
- Replicability (others can use it, not just us)

Recommended ask: **$2,000-$5,000** matched from QF pool.

---

## Pitch (for Gitcoin grant page)

### Title
```
SigForge — Open-source validation framework for prediction-market trading
```

### Short description (1 sentence, shows up in browse)
```
A reproducible methodology + tooling stack so retail prediction-market
traders can validate strategies before risking capital — Sharpe 3.10
verified on the included BASKET arbitrage strategy.
```

### Full description (Markdown — pasted into Gitcoin grant page)

````markdown
## What this is

SigForge is an open-source framework that retail prediction-market traders
can fork to **validate strategies properly before risking capital**. It
runs on Polygon (Polymarket today; Manifold and Kalshi adapters planned).

The framework includes:

- **Universal backtester** — reads any trade log, computes Sharpe-per-
  trade, win rate, drawdown, and replays hypothetical strategy variants
  in seconds. 23 unit tests, GitHub Actions CI on Python 3.10/3.11/3.12.

- **Process watchdog** — detects silent failures across the bot stack
  (process down, balance drained, state stale, HALT flag). Prevents
  the well-documented "bot died but I didn't notice" failure mode.

- **13 KB methodology document** — full validation lifecycle (incubate
  → paper → candidate → live → scale/kill), three-layer risk hierarchy,
  decision logging template, concrete operational examples.

- **Strategy spec library** — four production specs for original
  strategies (BASKET multi-leg arbitrage with **Sharpe 3.10 verified**,
  YIELD-FARM consensus capture, SPORT-SNIPER live-state sports,
  COPY-TRADER specialist mirror).

- **Architecture diagram** — Mermaid-rendered, 7-layer breakdown
  showing data → signal → strategy → execution → portfolio →
  validation → monitoring.

## Why it's a public good

Most retail prediction-market traders lose money for **structural**
reasons (not bad luck): no written hypothesis, no controlled tests,
no risk floor. The result is a documented retail wipeout pattern.

SigForge inverts all three. Every strategy starts with a written
edge thesis. Every patch is tested in isolation against archived
data via the backtester. Every position has bot-encoded stops and
account-level circuit breakers.

The MIT license means anyone can fork, adapt, and run this on
Polymarket, Manifold, Kalshi, or any future prediction-market
protocol with a public CLOB. The validation gates are the
contribution — the methodology is reproducible regardless of
whose capital is at stake.

## What I've already built (5 weeks self-funded)

- Public live showcase: `http://18.178.69.19/showcase.html?tour=1`
- GitHub repo: `https://github.com/Stepan2116/sigforge-builder`
- 8+ commits in past 48 hours, all production-grade content
- 23 unit tests passing, CI green
- Sharpe 3.10 BASKET verified on 9 closed trades
- 200+ Obsidian audit notes (private, but methodology is public)

## What grant funding accelerates

- **MIT-licensed v1.0 release** — package the framework for `pip
  install sigforge-backtest` style consumption.
- **Multi-platform adapters** — Manifold and Kalshi adapters
  (Polymarket-first today).
- **Community onboarding** — contribution guide, "your first
  strategy" tutorial, public retrospective on what failed.
- **Documentation expansion** — strategy spec library grows; each
  community-contributed strategy goes through the validation gates
  documented in METHODOLOGY.md.

## Modest, realistic ask

Asking for $2,000 (will be matched via QF). This funds:
- ~2 weeks developer time on documentation + multi-platform adapters
- Open-source release polish (CHANGELOG, contributing guide, code of conduct)
- Community engagement (X content, Discord/Telegram presence)

I am also applying to Polymarket Builders for live-deployment-specific
funding ($10K range). The two grants fund **different parts** of the
same project. Polymarket funds Polymarket-specific live trading;
Gitcoin funds the platform-agnostic open-source public good.

## Verifiable in 5 minutes

1. Open the showcase — Sharpe 3.10 visible, refreshed every 30 seconds.
2. Open the repo — see methodology, strategy specs, backtester source.
3. Run the backtester yourself: `python tools/backtest.py /path/to/data`.
4. Read METHODOLOGY.md — 11 sections, no fluff.

Sample sizes are honest (small but real). Track record is paper
(live deployment is in flight via the Polymarket grant track).

---

**Builder Code (Polymarket attribution):** `0x6a386ecc...8ba1`
**License:** MIT
**Geography:** EU (Ukraine)
**Solo founder:** Stepan Riznyk
````

---

## Submission checklist

- [ ] Gitcoin profile created (Passport / Holonym verification done)
- [ ] Grant page populated with title + description
- [ ] Banner image (1200×675, can use the `frontend/showcase-preview.svg`)
- [ ] All links (showcase, repo, methodology) verified in incognito
- [ ] Cross-disclosure of Polymarket + Manifund applications
- [ ] Submitted

After submit:
- [ ] Share QF round announcement on X (drives QF contributions)
- [ ] Encourage community to contribute — even $1 contributions matter for QF
- [ ] Reply to contribution comments
- [ ] 14-day follow-up reminder

---

## QF strategy notes

Quadratic Funding rewards **breadth of support** more than depth. To
optimize:

1. **Ship the X thread first** (already drafted in `x-thread.md`) —
   build awareness before round opens.
2. **Engage Polymarket Discord and prediction-market Twitter** —
   these are the natural funders.
3. **Encourage $1-5 contributions** from anyone interested. A grant
   page with 50 unique $2 contributions out-matches a page with 2
   unique $50 contributions.
4. **Stay engaged through the round** — reply to contribution comments,
   tweet weekly status.

Round duration is typically 14-21 days. Plan engagement across the
full window, not just first day.
