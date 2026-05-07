# strategies/adapters/

> *Uniform interface over prediction-market platforms. Strategies talk to
> the abstract `Platform` interface; only the adapter knows about each
> platform's REST quirks.*

This is what makes SigForge platform-agnostic. The same strategy code
runs against Polymarket today; against Manifold tomorrow with a thin
adapter swap; against future EVM-based prediction markets without any
strategy-side rewrites.

## Layout

```
adapters/
├── __init__.py        REGISTRY + factory function
├── base.py            Platform interface + dataclasses (Market, Book,
│                       Order, OrderResult)
├── polymarket.py      Production-tested. Read via Gamma API; trading
│                       delegated to live-executor (TS) for Builder Code
│                       attribution.
├── manifold.py        Read-only alpha. Trading scaffold in place but
│                       returns NotImplementedError so accidental live
│                       calls cannot succeed.
└── kalshi.py          Scaffold only. Documents the boundary. SigForge is
                        EU-based; Kalshi requires US KYC. File exists so a
                        reviewer or future contributor can see exactly
                        where Kalshi plugs in.
```

## Usage

```python
from strategies.adapters import adapter_for

# polymarket — production
poly = adapter_for("polymarket")
for m in poly.fetch_markets(limit=100):
    if m.volume_24h_usd > 1000 and not m.closed:
        print(m.slug, m.question)

# manifold — read-only
mani = adapter_for("manifold")
for m in mani.fetch_markets(limit=50):
    print(m.id, m.outcomes)

# kalshi — scaffold; raises NotImplementedError on every call
```

## Design rules

1. **No platform-specific dicts leak past the boundary.** Adapters return
   normalized dataclasses (`Market`, `Book`, etc.) with the platform raw
   payload tucked in `.raw` for the rare case a strategy needs a field
   the abstraction does not surface yet.
2. **Adapter MVP scope is the four methods on `Platform`.** Anything more
   (portfolio polling, PnL accounting, order amendments) lives next to
   each adapter as platform-specific scaffolding, not in the base.
3. **Adapters that cannot trade raise NotImplementedError on
   `submit_order` with a clear message.** Silent failure is forbidden.
4. **Read paths are best-effort.** A flaky network or 5xx returns `None`
   from `fetch_market` / `fetch_book`; strategies decide whether that is
   transient (retry next cycle) or terminal (skip).

## Adding a new platform

1. Subclass `Platform` from `base`.
2. Implement `fetch_markets`, `fetch_market`, `fetch_book`,
   `submit_order` (or raise NotImplementedError if trading is out of
   scope).
3. Normalize results into `Market` / `Book` / `OrderResult`.
4. Register the class in `REGISTRY` in `__init__.py`.
5. Add a paragraph at the top of the adapter file explaining what is
   implemented and what is intentionally deferred. Future contributors
   read these first.

## Why this matters for grants

The "multi-platform support" claim in `docs/ROADMAP.md` is not aspirational
hand-waving. It is a concrete architecture: strategies call
`adapter.fetch_market(...)` rather than hitting Gamma directly, so
swapping in Manifold for backtesting or paper trading is a one-line
`adapter_for("manifold")` change. The Kalshi scaffold makes the
boundary explicit so a reviewer can see exactly what is missing and why.
