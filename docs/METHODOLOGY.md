# SigForge Methodology

The SigForge methodology is an opinionated framework for validating prediction-market strategies before risking live capital.

## Core principles

### 1. Hypothesis-first
Every strategy or patch starts with a written hypothesis:
> *"If we filter entries by [X criterion], we expect [Y outcome] because [Z mechanism]."*

The hypothesis is logged before the patch is applied, not retrofitted. This makes post-mortems honest.

### 2. Audit trails
Every strategic decision creates an audit note: hypothesis, expected impact, observed result, rollback condition.

### 3. Multi-variant A/B/C testing
We do not run one strategy. We run multiple variants in parallel with isolated capital. Each variant tests a specific hypothesis. PnL deltas attribute outcome to specific design decisions.

### 4. Paper-first, live-later
No strategy is promoted to live capital without:
- Minimum sample size of closed trades (20+)
- Empirical confirmation of hypothesized win rate
- Risk-of-ruin under stress scenarios documented

### 5. Risk-managed scaling
Live capital starts small ($50-100), proves out, then scales. No "yolo" position sizes. Builder Code attribution is wired in from day-1 of any live deployment.

## Strategy validation gates

Before any strategy moves from paper to live:

| Gate | Threshold |
|---|---|
| Closed sample size | ≥ 20 trades |
| Realized PnL | > 0 over sample |
| Risk-of-ruin under 3-sigma loss | < 5% of capital |
| Hypothesis re-tested under stress | yes |
| Audit log complete | yes |

## Patch lifecycle

```
HYPOTHESIS → IMPLEMENT → A/B test on isolated variant → 14d observe → 
  → if positive: merge to canonical → rollback plan documented
  → if negative: archive variant → audit note captures what failed
```

## Why this matters

Most retail prediction-market traders lose money because:
- They do not document hypotheses (so they cannot tell luck from skill)
- They do not run controlled tests (so they cannot attribute PnL)
- They do not size for ruin (so one bad streak ends the run)

SigForge is the opposite of all three.
