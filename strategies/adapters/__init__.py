"""SigForge platform adapters — uniform interface over prediction-market APIs.

The adapter layer is what makes SigForge platform-agnostic. Strategy code
talks to the abstract `Platform` interface; only the adapter knows about
each platform's REST quirks, signing scheme, fee model, and resolution
semantics.

Platforms covered:
    polymarket — production-tested (the four shipped strategies all use it)
    manifold   — read-only adapter implemented; trading deferred to v0.2
    kalshi     — auth-scaffold only; trading deferred (KYC required)

To add a new platform: subclass `Platform` from `base`, implement the four
required methods, and register the class in `REGISTRY` below.
"""
from .base import Platform, Market, Book, Order, OrderResult
from .polymarket import PolymarketAdapter
from .manifold import ManifoldAdapter
from .kalshi import KalshiAdapter

REGISTRY: dict[str, type[Platform]] = {
    "polymarket": PolymarketAdapter,
    "manifold": ManifoldAdapter,
    "kalshi": KalshiAdapter,
}


def adapter_for(name: str, **kwargs) -> Platform:
    """Instantiate an adapter by short name.

    Raises KeyError if the platform is not registered. Unknown kwargs are
    forwarded to the adapter constructor; each adapter validates its own
    required configuration.
    """
    cls = REGISTRY[name.lower()]
    return cls(**kwargs)


__all__ = [
    "Platform", "Market", "Book", "Order", "OrderResult",
    "PolymarketAdapter", "ManifoldAdapter", "KalshiAdapter",
    "REGISTRY", "adapter_for",
]
