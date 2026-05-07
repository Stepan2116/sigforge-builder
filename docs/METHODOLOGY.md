# SigForge Methodology

> *Disciplined validation framework for prediction-market strategies on Polymarket.*

This document describes how SigForge identifies, validates, scales, and retires
trading strategies. It is the answer to a single operational question:
**"How do we know this strategy actually works, and not that we got lucky?"**

---

## 1. Vision

Most retail prediction-market traders lose capital for three structural reasons:

1. **No hypothesis** — they cannot distinguish skill from luck after the fact.
2. **No controlled testing** — every change is a confounded variable.
3. **No risk floor** — one adverse streak terminates the run.

SigForge is the opposite of all three. Every strategic decision starts with a
written hypothesis, every patch runs as an isolated A/B variant, and every
strategy passes quantitative gates before touching live capital.

The goal is not maximum trades — it is **high-confidence attribution** of PnL to
specific design choices.

---

## 2. Edge thesis framework

Before any strategy is implemented, we write a one-paragraph **edge thesis**
that answers four questions:

| Question | Example (BASKET strategy) |
|---|---|
| **What is the inefficiency?** | Polymarket weather buckets occasionally trade with sum-of-asks < $1.00, despite exactly one bucket being guaranteed to resolve $1.00. |
| **Why does it persist?** | Each bucket is a separate binary market. Retail traders rarely sum them. Liquidity providers price each leg independently. |
| **What is the edge magnitude?** | Profit per trade = $1.00 − sum(asks). Empirically $0.02 – $0.10 per opportunity. |
| **What is the failure mode?** | Resolution dispute, bucket double-counting bug, sudden liquidity drop preventing all-leg fills. |

If any of the four cannot be answered cleanly, the strategy does not start.

The thesis is committed to the audit trail before code is written. Post-mortems
compare observed PnL to the predicted edge magnitude — if reality diverges, we
investigate the gap rather than re-fit the narrative.

---

## 3. Strategy lifecycle

Every strategy travels through five phases. Promotion between phases requires
explicit gate criteria, not vibes.

```
INCUBATE → PAPER → CANDIDATE → LIVE → SCALE / KILL
```

### 3.1 Incubate

- Edge thesis written and reviewed.
- Initial implementation in code.
- Backtest on historical data if available.
- Deployed locally, no capital, no public exposure.

**Gate to next phase:** thesis is internally consistent and backtest does not
falsify the edge.

### 3.2 Paper

- Strategy runs as `pm2` process with paper-money state.
- Capital allocated: typically $200 – $1,000 paper.
- Metrics tracked: trades, win rate, realized PnL, Sharpe-per-trade, max
  drawdown, time-to-resolution distribution.
- Watchdog monitors for silent failures.

**Gate to next phase (Candidate):**
- ≥ 20 closed trades.
- Sharpe-per-trade > 0.5.
- Win rate confirms thesis-predicted distribution within ±15%.
- No unexplained losses (every loss explained by hypothesis).

### 3.3 Candidate

- Strategy is on the live deployment shortlist.
- 30-day extended paper observation under varied market conditions.
- Stress tests: simulated 3-sigma adverse moves; ruin probability documented.
- Builder Code integration verified.

**Gate to next phase (Live):**
- All paper gates still pass after 30 days.
- Risk-of-ruin under 3-sigma loss < 5% of allocated live capital.
- Audit log complete and reproducible.
- Manual sign-off after final review.

### 3.4 Live

- Real Polymarket capital deployed via Builder Code.
- Initial size: $50 – $100 per strategy.
- All orders attribute volume to Polymarket via `builderCode` field.
- Continuous monitoring with drawdown circuit breakers.

### 3.5 Scale or kill

Decision after 30 days live:

- **Scale:** real PnL within ±25% of paper PnL extrapolation. Capital increases
  in halving steps (e.g. $100 → $200 → $400) provided each step holds.
- **Kill:** real PnL < 50% of paper extrapolation, or any unexplained loss.
  Strategy archived with post-mortem note. No retry without revised thesis.

The "kill" branch is non-negotiable. Strategies that worked in paper and failed
live almost always indicate the thesis missed a friction (slippage, latency,
adverse selection) — fixing it requires going back to phase 1, not phase 5.

---

## 4. Risk management hierarchy

Risk is enforced at three independent levels. Any one breach pauses the
relevant scope.

### 4.1 Per-trade

- Hard cap on position size as % of strategy capital.
- Pre-defined exit at entry × structural-stop multiplier (typically 0.75 for
  swing-style; 0.50 for tail-risk strategies).
- No mental stops — every position has the exit logic encoded in the bot.

### 4.2 Per-strategy

- Daily loss limit halts new entries for the rest of the UTC day.
- Maximum open exposure cap (e.g. 30% of strategy capital).
- Drawdown circuit breaker: −15% from peak halts the strategy entirely until
  manual review.

### 4.3 Portfolio

- Total exposure across all strategies capped.
- Correlation monitoring — strategies with > 0.7 PnL correlation cannot
  exceed combined cap.
- Master watchdog detects silent failures across the entire stack.

### 4.4 Why three layers

Single-layer risk control fails predictably:

- Per-trade only → death by 1,000 cuts.
- Daily-only → one big position blows the day.
- Account-only → triggers too late, after capital is impaired.

Three independent layers create defense-in-depth. A single bug or adverse
streak cannot defeat all three simultaneously.

---

## 5. Validation gates (quantitative)

Strategies move between phases only when these thresholds are met. The numbers
are conservative on purpose — false negatives are cheaper than false positives.

| Metric | Paper → Candidate | Candidate → Live |
|---|---|---|
| Closed trades (sample size) | ≥ 20 | ≥ 50 |
| Sharpe per trade | > 0.5 | > 1.0 |
| Win rate vs. thesis | within ±15% | within ±10% |
| Max drawdown | < 30% of strategy capital | < 20% |
| Risk-of-ruin (3-sigma) | < 10% | < 5% |
| Independent PnL audit | initial | quarterly |

**Sharpe per trade** = mean(trade_pnl) / stdev(trade_pnl). It is the cleanest
single number to compare strategies at this scale. It does not annualize
(meaningless for sporadic prediction-market opportunities) and it does not
penalize concentration (high-frequency arbitrage with stable edge correctly
shows high Sharpe even at small notional).

---

## 6. Backtester philosophy

The SigForge backtester is a tool, not an oracle. Three principles govern its use:

### 6.1 Backtest validates falsification, not confirmation

We use the backtester to **disprove** strategy variants, not to "find" them.
Running 50 random variants and picking the best is overfitting. Running one
specific variant proposed by the thesis and confirming the edge holds is
validation.

### 6.2 Survivorship bias is real

The backtester only sees trades that were taken. It cannot see what a
candidate filter would have prevented from opening — those positions simply
do not exist in the data. We acknowledge this explicitly when interpreting
results.

### 6.3 Proxy assumptions are documented

When the backtester replays exit logic, it sometimes uses proxies (e.g.
"if forecast left bucket, assume 50/50 hold-to-resolution"). These proxies
are stated up front. Live data is the only authority — backtester results
are hypotheses about live performance, not predictions.

---

## 7. Decision logging template

Every non-trivial decision creates an audit note. The template:

```markdown
# [YYYY-MM-DD] [strategy] [short-title]

## Hypothesis
[Single sentence: "If we [change], we expect [outcome] because [mechanism]."]

## Evidence supporting hypothesis
- [bullet] [reference to data, prior trade, related strategy result]

## Implementation
- [bullet] What changes in code
- [bullet] What changes in config
- [bullet] Backups / rollback steps

## Expected impact
- Win rate: [predicted change]
- Avg PnL: [predicted change]
- Max DD: [predicted change]
- Time horizon for evaluation: [N days]

## Rollback condition
[If [observation], revert by [action] within [time].]

## Result (filled in after observation period)
- Observed metrics
- Hypothesis confirmed / partially confirmed / falsified
- Lessons captured
```

These notes accumulate. After a year, they form a structured corpus showing
exactly what was tried, what worked, what failed, and why.

---

## 8. Concrete examples from current operations

### 8.1 BASKET — Sharpe 3.10 confirmed

Edge thesis: math-arb on weather buckets. Predicted Sharpe > 2.0.
Observed: 100% win rate over 9 closed trades, Sharpe-per-trade 3.10, total
realized $5.93 on $40-60 typical trade size.

Hypothesis confirmed. Capital scaling next.

### 8.2 ЛЬОДНИК (forecast-edge swing) — patches deployed today

Pre-patch baseline (79 closed trades): −$467 total, 19.5% WR, Sharpe −0.53.
Three structural problems identified:

1. Cheap entries < $0.20 lost 100% of the time (24/24 trades, −$236).
2. Old `−20%` stop in `monitor_positions()` was being silently bypassed
   when `forecast_changed` exits dumped at near-zero.
3. Patch had been written to `scan_and_update()` which runs hourly, not to
   `monitor_positions()` which runs every 10 minutes.

Patches: ban entries < $0.20, symmetric +25% lock / −25% stop, hold-to-
resolution floor when bid drops below entry × 0.50.

Backtester proxy showed +$130 net on 162 historical positions versus −$1,482
unpatched. Live observation period: 5–7 days.

This is also why we built the watchdog. The Wellington bug (stop not firing
because patched the wrong function) was caught by manual inspection — the
watchdog now monitors silent failures across the entire stack.

### 8.3 weather-copy — filter mismatch, debug pending

1,804 whale signals received over multiple days, **0 trades executed**.
Root cause: filter expects forecast-tier alignment, but the tracked whale
buys at $0.97 – $0.99 obvious-winner prices that do not match the forecast-
tier filter. Hypothesis was wrong about the whale's edge source.

The strategy is paused pending revised filter logic. Capital is dead but
not lost — and the failure mode is now a documented learning, not a silent
drain.

---

## 9. Anti-patterns we explicitly avoid

| Anti-pattern | Why it fails | What we do instead |
|---|---|---|
| Chasing trades after losing streak | Compounds adverse variance | Daily loss limit halts entries |
| Mental stops | Hope kicks in, stop moves, account dies | Every entry has bot-encoded exit |
| Sizing without stop | Unbounded loss per trade | Position size = risk_dollars / stop_distance |
| No audit log | Cannot tell luck from skill at scale | Every decision logged before action |
| Lower threshold to "get more trades" | Negative-EV trades degrade overall edge | Threshold tightening is the default; loosening requires evidence |
| Single-strategy concentration | Single regime change = total ruin | Multi-strategy portfolio with correlation cap |

---

## 10. Known limitations

This methodology has costs we accept openly:

- **Slow scaling.** Strategies take 30–60 days to advance through the gates.
  We deliberately trade off speed for confidence.
- **Conservative capital allocation.** Real-trade sizes start very small
  ($50–$100). This means absolute PnL early is modest.
- **Some opportunities missed.** Tight gates filter out short-window edges
  that need fast deployment. We accept this — chasing every opportunity is
  not our edge.
- **Methodology overhead.** Audit notes, gate reviews, and backtester runs
  consume time that could be spent on more strategies. We believe the
  attribution clarity is worth the overhead.

---

## 11. Open-source plan

Post-validation, we will release MIT-licensed:

1. **Backtester core** — universal trade-log analyzer with strategy variant
   replay.
2. **Strategy spec library** — reference implementations of validated strategies
   (BASKET, YIELD-FARM, SPORT-SNIPER) with decision logs.
3. **Risk management primitives** — drawdown circuit breaker, watchdog,
   audit-note templates.
4. **Methodology documentation** — this document, expanded with case studies.

The goal is to make disciplined retail trading on prediction markets
reproducible. Most retail traders fail by skipping process; we want to make
process the default.

---

## Appendix: live infrastructure summary

- **Backend:** AWS Lightsail Tokyo, Node.js + Python `pm2` process tree.
- **Bot processes:** ~25 concurrent (strategies + variants + monitors + data
  feeds + watchdog).
- **Knowledge base:** Obsidian vault auto-synced to AWS via cron.
- **Public showcase:** https://sigforge.dev/showcase.html (live, 24/7).
- **Builder Code:** `0x6a386ecc...8ba1` obtained, integration designed.

For implementation detail see `strategies/` and `frontend/` directories.
