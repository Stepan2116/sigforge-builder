# SigForge — Octant Public Goods Application

> *Adapted for Octant's quadratic-funding model where GLM-staker voting
> determines allocations from Golem Foundation's staking rewards.*

---

## Where to apply

**Octant** (octant.build / docs.octant.app)
- Pool source: Golem Foundation staking rewards distributed quarterly per epoch
- Mechanism: GLM stakers vote on which public-goods projects to fund
- Decision time: ~3 months per epoch
- Application: project profile + community discussion

**Status note (May 2026):** Epoch 11 was the final v1 Allocation Window
(ended March 2026). The platform is migrating to v2. Application timing:
target the first v2 epoch when applications open. Engage via Octant
Discord in the interim.

---

## Eligibility check — does SigForge qualify?

Octant's stated criteria:

| Criterion | SigForge fit |
|---|---|
| Direct impact on Ethereum mainnet (security, scalability, sustainability) | 🟡 Polygon-native (Ethereum L2). Not direct mainnet, but within ecosystem. |
| Address critical infrastructure needs | ✅ Yes — disciplined trading framework is tooling that retail prediction-market traders lack. |
| Long-term public goods benefiting multiple stakeholders | ✅ MIT-licensed, multi-platform (Polymarket, Manifold, Kalshi adapters planned). |
| Technical innovation | ✅ Universal backtester with strategy variant replay, three-layer risk hierarchy, hypothesis-first methodology. |
| Verifiable deliverables | ✅ All deliverables in repo with CI verification. |

**Honest assessment:** The Polygon-not-mainnet framing is the soft point.
We'll lean on the multi-platform adapter angle (which extends to any
EVM-compatible prediction market, including Ethereum mainnet protocols
like Augur or Polymarket-style deployments on L1).

---

## Pitch (ready for Octant proposal form)

### Project name
```
SigForge — Open-source validation framework for prediction-market trading
```

### Category
```
Developer tooling / Public goods infrastructure
```

### One-line summary
```
Reproducible methodology + tooling stack so retail prediction-market
traders can validate strategies before risking capital. MIT-licensed,
Sharpe 3.10 verified on the included BASKET arbitrage strategy.
```

### Why public good
```
Most retail prediction-market traders lose money for structural reasons:
no written hypothesis, no controlled testing, no risk floor. The result
is the well-documented retail wipeout pattern.

SigForge addresses all three. The framework includes:
- A 13 KB methodology document with validation lifecycle and risk hierarchy.
- A universal backtester with strategy variant replay (1-second validation
  vs 30 days of paper trading).
- A process watchdog that detects silent failures across the bot stack.
- Four production strategy specs covering original work.
- An architecture document with system diagram.

The framework is platform-agnostic. It works today on Polymarket
(Polygon); Manifold and Kalshi adapters are in scope. Any EVM-based
prediction-market protocol — including future Ethereum L1 deployments —
can be supported with a thin adapter layer.

The MIT license means anyone can fork, adapt, and run this. The validation
gates are the contribution, and the methodology reproduces regardless of
whose capital is at stake.
```

### Eligibility justification — Ethereum ecosystem alignment
```
SigForge today runs on Polygon (Ethereum L2). The strategies trade on
Polymarket, which settles on-chain via UMA optimistic oracles (Ethereum-
ecosystem infrastructure).

Beyond today, the framework is designed to support any prediction-market
protocol with a public CLOB API. This explicitly includes EVM L1
deployments. The Manifold adapter (planned) extends to a non-Polygon
target; the architecture is platform-neutral by design.

Public goods value: retail traders on Polymarket today, plus future users
of any prediction-market protocol that adopts the framework, plus the
research community that benefits from open-sourced trading methodology.
```

### Funding ask
```
$3,000 - $5,000 per epoch (matched via QF-style allocation by GLM stakers).
```

### Use of funds
```
- $1,500: Developer time on platform-agnostic adapter layer (Polymarket
  remains primary; Manifold + Kalshi adapters next).
- $1,500: Open-source release polish — package for `pip install sigforge`,
  contributing guide, CHANGELOG, code of conduct.
- $1,500: Community engagement (Discord, X content, contribution
  onboarding for first external PRs).
- $500: Reserve for unforeseen.
```

### Verifiable deliverables (per epoch)
```
By end of epoch:
- v1.0 release tagged on GitHub
- Manifold adapter in alpha
- 3 community blog posts published (BASKET edge, methodology overview,
  first failed-strategy retrospective)
- First external contribution PR merged
- Updated documentation reflecting adapter coverage
```

### Proof of work
```
Repository: https://github.com/Stepan2116/sigforge-builder
Live showcase: http://18.178.69.19/showcase.html?tour=1
CI badge: green
Builder Code (Polymarket): 0x6a386ecc...8ba1
9+ commits in past 48 hours, all production-grade content.
```

### Applications to other programs (transparency)
```
SigForge is also applying to:
- Polymarket Builders Program ($10K range, lean execution)
- Manifund / Manifold Community Fund ($5K, public goods)
- Gitcoin Grants OSS round ($2K matched via QF, open-source)

Each grant funds different parts of the project:
- Polymarket: Polymarket-specific live deployment with Builder Code attribution
- Manifund / Gitcoin / Octant: open-source release, multi-platform adapters,
  community engagement (the public-good portion)

We are transparent in every application about the dual track. No grant is
duplicating another's scope.
```

---

## Engagement strategy (Octant-specific)

GLM stakers are the actual voters. To win allocation we need:

1. **Discord presence** — join Octant Discord, introduce SigForge in
   appropriate channel, answer questions about the framework.
2. **Forum post on discuss.octant.app** — a "Public Good Projects Discussion"
   thread describing SigForge, expected impact, and what we'd build.
3. **Engagement with previously-funded projects** — see what voters
   responded to in past epochs.
4. **X presence** — link our X thread (already drafted) to demonstrate
   active community work.
5. **Updates during the epoch** — weekly status posts, build trust.

Quadratic-style voting rewards consistent visible work over single-point
launches.

---

## Submission checklist

- [ ] Octant Discord joined, SigForge introduced
- [ ] Forum post drafted (use the pitch above as basis)
- [ ] Project profile created on Octant platform when v2 application opens
- [ ] Banner image (`frontend/showcase-preview.svg` works)
- [ ] All links verified in incognito
- [ ] Cross-disclosure of other grant applications
- [ ] Submitted

After submit:
- [ ] Engage on forum during epoch
- [ ] Vote-day push: ask community to vote (only via existing relationships,
      no spam to GLM stakers)
- [ ] Document outcome in next epoch retrospective regardless of result

---

## Realistic expectation

Octant is selective. ~450 applications, only a portion get funded per
epoch. SigForge's strength: documentation + methodology + working
prototype. Weakness: not Ethereum-mainnet-direct.

Expected outcome:
- 30-40% chance of selection in first application
- Higher in subsequent epochs once we've established Discord/forum presence

Apply, engage consistently regardless of first-epoch outcome.
