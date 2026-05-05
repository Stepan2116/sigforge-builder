# SigForge — Multi-Strategy Validation Framework for Polymarket

**One-liner:** Open-source multi-strategy validation framework for Polymarket. Original prediction-market strategies under continuous A/B/C testing, structured risk-management methodology, infrastructure-first approach.

**Public showcase:** http://18.178.69.19/showcase.html (live, 24/7)
**Tour mode:** http://18.178.69.19/showcase.html?tour=1 (auto-starts 8-step guided walkthrough)

**Geography:** EU
**Status:** Working prototype, original strategies in active paper validation
**Builder Code:** `0x6a386ecc3a926b109e131d736ab0053cb6bb6745638ddefa2693247db62d8ba1`

---

## What we built

A full-stack validation harness for prediction-market strategies:

| Strategy | What it does | Track record |
|---|---|---|
| **BASKET** (multi-leg arbitrage) | Buys all weather buckets when total ask < $1.00 — math-guaranteed risk-free profit | **+$5.93 realized, 100% WR (9/9 closed)** |
| **YIELD-FARM** (cointrick) | Buys high-consensus markets at $0.99+ for guaranteed $1.00 resolution | 100% WR (18/18 closed), 25 active open positions |
| **COPY-TRADER** (esports) | Mirrors verified e-sports specialist whales with risk filters | $1,000 paper, scanning |
| **SPORT YIELD** | Yield-farm on extreme-consensus FIFA / sports markets | 10 open, scanning |
| **MM PAPER** | Maker-rebate market-making prototype | $990 paper |

All strategies are **original work** — no forked dependencies.

## Infrastructure

- **Live dashboard** at `http://18.178.69.19/showcase.html` — real-time PnL across all strategies, 24/7
- **Multi-variant A/B/C testing** — pm2 process management, isolated capital per variant
- **Audit framework** — every strategy decision logged in dated audit notes with hypothesis, expected outcome, rollback plan
- **Knowledge base** — 27-note synthesis of Smart Money Concepts, Wyckoff theory, auction microstructure, risk management — adapted for prediction-market dynamics
- **Vault auto-sync** — Obsidian vault auto-syncs to AWS via cron, full reproducibility
- **Builder Code obtained** — integration mechanism designed (see `/api/showcase` endpoint and showcase.html for live demo)

## What makes this different

Most retail Polymarket bots are single-strategy point solutions. SigForge is **infrastructure**:

1. **Methodology-first** — every strategic decision is documented with hypothesis, expected PnL impact, and rollback plan
2. **Multi-variant testing** — we run hypotheses in parallel with isolated capital, not sequential
3. **Original synthesis** — 27-note Trading Knowledge Base adapts trading theory specifically for prediction markets (jump-process resolution, thin liquidity, premium/discount under bounded probability)
4. **Open-source plan** — post-validation, we publish framework + strategy spec library MIT-licensed so retail can replicate disciplined approaches

## Why this matters for Polymarket

- **Retail-replicable:** when proven, our stack ports to live with Builder Code attribution wired in. Other retail traders clone our framework, attribute volume back to Polymarket, we share the infrastructure benefit
- **Underbuilt niche:** weather-arbitrage, multi-leg basket strategies, copy-trader frameworks not covered by Betmoar / PolyTraderPro / Stand.trade focus on liquid sports/election markets
- **Knowledge moat for retail:** our Trading Knowledge Base lowers entry barrier for retail traders who currently lose money to lack of methodology

## What we'll do with grant funding

1. **Port BASKET to live** with Builder Code attribution — $50-100 capital, generate first attributed volume on real chain
2. **V2 SDK migration** — upgrade from `py-clob-client v0.34.6` to V2 for builder code support across all bots
3. **Public website** — domain (`sigforge.io` or similar), brand, public-facing leaderboard for cloned-stack users
4. **Open-source release** — publish 3-5 most validated strategies with full setup docs and replication framework
5. **Knowledge base public mirror** — Trading Knowledge Base on public-facing site (currently in private Obsidian vault)

## Application context

- **Team:** solo builder + AI-augmented architect (Claude-powered workflow)
- **Geography:** EU (Ukraine)
- **Capital deployed:** $5 real / ~$3,500 across paper variants
- **Active since:** April 2026
- **Public infrastructure:** http://18.178.69.19/showcase.html (live)
- **Vault:** Obsidian-based, 200+ notes, auto-synced AWS

**Contact:** riznykstepan@gmail.com
