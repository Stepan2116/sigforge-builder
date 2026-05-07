# SigForge — Manifold/Manifund Application Materials

> *Adapted from the Polymarket Builders submission. Same project, different
> emphasis: SigForge as a **platform-agnostic prediction-market validation
> framework** rather than a Polymarket-specific tool.*

---

## Where to apply

**Primary target: Manifund** (manifund.org)
- Grant platform for impact certs, public goods, community funding
- Application format: Markdown/text proposal
- Typical sizes: $500–$10,000 (variable)
- Decision time: 1-4 weeks

**Secondary target: Manifold Community Fund**
- $30K pool, sponsors prediction-market-adjacent projects
- Application format: forum post + reply from team
- Typical sizes: $500–$5,000

**If both:** apply Manifund first (more formal), then mention the application
in the Manifold Community Fund post for cross-reference.

---

## Pitch framing (Manifund version)

```
SigForge is an open-source validation framework for prediction-market
trading strategies. It is not specific to any one platform — the
methodology, backtester, watchdog, and audit-trail tooling work
identically across Polymarket, Manifold, Kalshi, and any future
prediction market that exposes a public CLOB or order API.

We are seeking $5,000 from Manifund to:
1. Open-source release of the framework under MIT license.
2. Adapt the SigForge tooling for Manifold's API (currently
   Polymarket-first; Manifold adapter is ~1 week of work).
3. Public retrospective + first community engagement post.

Most retail prediction-market traders lose for structural reasons
(no hypothesis, no controlled tests, no risk floor). SigForge is
the opposite of all three. The framework has been self-funded for
five weeks; it works on Polymarket today (Sharpe 3.10 verified on
the BASKET arbitrage strategy). A Manifund grant accelerates the
public release and the multi-platform expansion.

Why this matters for Manifold specifically: Manifold's user base
includes EA-aligned traders and quantitative researchers — exactly
the audience that benefits from disciplined methodology. Today,
those users build ad-hoc scripts. SigForge gives them a reusable
framework with proven tooling.
```

---

## Form fields (paste-ready)

### Project name
```
SigForge — open-source prediction-market validation framework
```

### Project description (3-5 sentences)
```
SigForge is an open-source framework for building, validating, and
scaling original prediction-market trading strategies. It includes a
universal backtester, a process watchdog, a 13 KB methodology
document, and four validated strategy specs. The framework is
platform-agnostic — designed to work on Polymarket, Manifold, Kalshi,
or any market with a public CLOB API. Five weeks of self-funded work
delivered the current state (Sharpe 3.10 verified on Polymarket
weather arbitrage). Funding accelerates the MIT-licensed public
release and Manifold-adapter implementation.
```

### Funding amount
```
$5,000
```

### Use of funds
```
- $1,500: Manifold API adapter — port existing Python tooling to
  Manifold's market schema. ~1 week development.
- $1,500: Open-source v1.0 release — MIT licensing, README polish,
  publish to PyPI/npm where applicable, contribution guide.
- $1,500: Documentation expansion — strategy spec library, cross-
  platform deployment guide, contribution onboarding.
- $500: Reserve for unforeseen / community engagement.
```

### Why this matters
```
Most retail prediction-market traders fail for three structural
reasons: no written hypothesis, no controlled testing, no risk
floor. The result is the well-documented retail wipeout pattern.

SigForge inverts all three. Every strategy starts with a written
edge thesis. Every patch is tested in isolation against archived
data via the backtester. Every position has bot-encoded stops and
account-level circuit breakers.

The 13 KB methodology doc is reviewer-grade. The four strategy
specs cover original work (BASKET multi-leg arbitrage, YIELD-FARM
consensus capture, SPORT-SNIPER live-state sports, COPY-TRADER
specialist mirror).

Public release lets retail traders replicate disciplined approaches
without rebuilding the framework themselves. That is the impact
case: not "fund a bot," but "fund the standard tooling that future
bots can use."
```

### Proof of work
```
GitHub: https://github.com/Stepan2116/sigforge-builder
Live showcase: http://18.178.69.19/showcase.html?tour=1
CI badge: green (23 unit tests, Python 3.10/3.11/3.12)
Recent commits: 8+ public commits over the past 48 hours, all
production-grade content (methodology, strategy specs, tools, tests).

The full architecture is documented in docs/ARCHITECTURE.md
including a Mermaid system diagram. The validation lifecycle and
funding allocation breakdown are in docs/ROADMAP.md.

I am also applying to the Polymarket Builders Program for live
deployment funding. The two grants are complementary: Polymarket
funds Polymarket-specific live trading; Manifund funds the
platform-agnostic open-source release.
```

### Team / About
```
Solo developer based in EU (Ukraine). Five weeks of full-time
self-funded work to reach the current state. No prior prediction-
market product launches; deep methodological discipline borrowed
from quantitative finance and software engineering practice.

Public identity: Stepan Riznyk (@SigForgeBot on X if available).
Verifiable via GitHub history.
```

---

## Why dual-apply is OK

The Polymarket and Manifund applications fund **different parts** of the
same project:

- **Polymarket Builders ($10K range):** funds the Polymarket-specific
  live deployment with Builder Code attribution. Capital is for actual
  trading, not infrastructure.
- **Manifund ($5K):** funds the open-source release, Manifold adapter,
  and platform-agnostic documentation. Capital is for public-good work
  that benefits the broader prediction-market ecosystem.

Each grant is justified on its own merits. We are transparent in both
applications about the dual track.

---

## Submission checklist

- [ ] Manifund profile created
- [ ] Project description pasted
- [ ] Funding amount specified
- [ ] Use-of-funds breakdown attached
- [ ] Proof-of-work links work in incognito
- [ ] Polymarket grant disclosure mentioned (transparency)
- [ ] Submitted

After submit:
- [ ] Cross-post to Manifold Community Fund forum
- [ ] Reference both submissions in upcoming X thread
- [ ] Set 14-day follow-up reminder
