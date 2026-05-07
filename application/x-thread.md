# BASKET edge — X thread (10 tweets)

> *Ready-to-paste thread. Copy each block as one tweet (each ≤280 chars).
> Recommended cadence: post 1 tweet per 30-60 seconds, no scheduler.
> Engage replies in real time — first 30 minutes determines reach.*

---

## Tweet 1/10 — Hook

```
There's a 100% win rate, Sharpe 3.10 strategy on Polymarket weather markets.

It's not a model. It's not pattern recognition. It's a math identity.

Most traders walk past it because nobody sums the asks across all buckets.

🧵 1/10
```

## Tweet 2/10 — Setup

```
Polymarket weather events have N buckets (e.g. "Tokyo high will be 18-19°C", "20-21°C", etc.).

Exactly ONE bucket resolves to $1.00.
The others all resolve to $0.00.

This isn't an opinion — it's how the market is constructed.

2/
```

## Tweet 3/10 — The math

```
If you buy 1 share of EVERY bucket, your guaranteed payout is exactly $1.00 (one bucket must win).

Your cost? sum(asks) of all buckets.

Profit per opportunity = $1.00 − sum(asks) − fees.

If sum(asks) < $1.00, the trade is a math-guaranteed positive return.

3/
```

## Tweet 4/10 — Why it persists

```
"OK but if it's free money, why does it persist?"

Three structural reasons:
- Each bucket is a separate binary market with independent LPs.
- Retail rarely sums across all buckets.
- LP rebalancing is slower than scanner cadence.

Remove any of these and the arb closes. As of May 2026, all three are present.

4/
```

## Tweet 5/10 — Edge magnitude

```
Empirically, opportunities give $0.02-$0.10 profit on $30-$100 typical exposure.

That's 0.5%-5% per trade.

Not a moonshot. But:
- 100% win rate (math)
- Sharpe-per-trade 3.10 (verified, 9 closed trades)
- Frequency-bounded by liquidity

5/
```

## Tweet 6/10 — Sharpe context

```
Sharpe 3.10 is what quant funds chase. For reference:
- > 1.0 = strong edge
- > 2.0 = professional level
- > 3.0 = quant-fund grade

The reason it's this high isn't the sample (only 9 closed trades).
It's that the edge is structural, not behavioral. No drawdown is possible per-trade.

6/
```

## Tweet 7/10 — Fragility

```
Things that can go wrong:
- Partial leg fill → unhedged exposure (mitigated by atomic-fill timeouts)
- Resolution dispute on UMA (delays PnL, doesn't reverse it)
- Sudden liquidity drop on one leg (sizing bounded by leg depth)

None observed in 9 trades. First real failure will arrive eventually.

7/
```

## Tweet 8/10 — Why open-source

```
We're applying for a Polymarket Builders grant to:
- port BASKET live with builderCode attribution
- ship the open-source release (MIT)
- build the framework other retail traders can replicate

This isn't a defensive moat. The math is the moat. The framework is the gift.

8/
```

## Tweet 9/10 — Anti-claim

```
Things this thread is NOT claiming:
- "Free money" — the edge is small per trade and frequency-bounded
- "I'll make you rich" — capital scaling is performance-gated
- "First mover advantage" — the math has always been there

What we did was build the infrastructure to act on it consistently.

9/
```

## Tweet 10/10 — CTA

```
Live tracker (Sharpe, WR, drawdown, refreshed every 30s):
https://sigforge.dev/showcase.html?tour=1

Full repo (MIT-licensed methodology + tools):
https://github.com/Stepan2116/sigforge-builder

Replies open for any technical question. 🧵 end.
```

---

## Posting checklist

Before posting:
- [ ] Verify showcase URL loads in incognito
- [ ] Verify GitHub repo is public and last commit visible
- [ ] Have a screenshot of `analyze_bots.py` output ready (in case anyone challenges Sharpe number)
- [ ] Have BASKET deep-dive open in another tab for replies
- [ ] Decide whether to tag `@PolymarketBuild` (probably yes after thread)

After posting:
- [ ] Pin thread to profile
- [ ] Reply to your own first tweet with thread link (helps reach)
- [ ] Cross-post to LinkedIn or Mirror.xyz (longer-form)
- [ ] Save engagement metrics 24h later
- [ ] Reference in grant submission as "active community engagement"

---

## Tone notes

- Confident but not breathless. Math identity is solid; we don't need adjectives.
- Acknowledge limits honestly (small sample, structural fragility) — builds trust.
- Don't tag Polymarket in tweet 1 (looks needy). Tag in tweet 10 or in a follow-up reply.
- Leave room for replies — questions about V2 SDK migration, builder code mechanics, etc. are welcome.

If a tweet feels too long when pasting, trim adjectives first, then prepositions, never numbers.
