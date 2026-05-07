"""Abstract platform interface for prediction-market adapters.

Every adapter implements the same four methods (fetch_markets, fetch_market,
fetch_book, submit_order) so strategy code is platform-agnostic. Returned
shapes are adapter-normalized into the dataclasses below — no platform-
specific dicts leak past this boundary.

The dataclasses below are deliberately minimal: only the fields every
strategy in the repo actually reads. New fields go through normalization
(adapter responsibility) rather than via free-form dict bleed-through.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass(frozen=True)
class Market:
    """A binary or multi-outcome prediction market, normalized across platforms.

    Identifiers vary per platform — `id` is whatever string the platform
    uses for its primary key. `slug` is a human-readable handle if the
    platform exposes one, else the same as `id`.
    """
    id: str
    slug: str
    question: str
    outcomes: list[str]
    end_date: str | None  # ISO-8601 UTC, or None if open-ended
    closed: bool
    volume_24h_usd: float
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class Book:
    """Top-of-book snapshot for one outcome of a market."""
    market_id: str
    outcome_idx: int
    bid: float | None
    ask: float | None
    bid_size: float | None
    ask_size: float | None
    ts_iso: str


@dataclass(frozen=True)
class Order:
    """A pending or submitted order. Side is BUY/SELL; price is in (0,1)."""
    market_id: str
    outcome_idx: int
    side: str         # "BUY" or "SELL"
    price: float
    size: float       # in shares (not USD); USD = price * size for BUY


@dataclass(frozen=True)
class OrderResult:
    """Outcome of `submit_order`. `filled` is True once the platform
    confirms an actual match; `pending` covers GTC limit orders that
    accepted on the book but have not crossed yet."""
    order_id: str
    filled: bool
    pending: bool
    avg_fill_price: float | None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


class Platform(ABC):
    """Interface every adapter must implement.

    The interface is small on purpose. Anything more — order amendments,
    portfolio polling, PnL accounting — is platform-specific scaffolding
    that lives next to each adapter, not in this base."""

    name: str = ""             # short id, e.g. "polymarket"
    supports_trading: bool = False

    @abstractmethod
    def fetch_markets(self, **filters) -> Iterable[Market]:
        """Yield Markets matching the filters. Filters are kwargs whose
        meaning is adapter-specific (e.g. tag, min_volume_24h, status).
        Adapters should return a generator for memory efficiency on large
        result sets."""
        raise NotImplementedError

    @abstractmethod
    def fetch_market(self, market_id: str) -> Market | None:
        """Return a single Market by id, or None if not found."""
        raise NotImplementedError

    @abstractmethod
    def fetch_book(self, market_id: str, outcome_idx: int) -> Book | None:
        """Top-of-book snapshot. Returns None if the market is closed or
        has no resting orders."""
        raise NotImplementedError

    @abstractmethod
    def submit_order(self, order: Order) -> OrderResult:
        """Submit an order. Adapters that do not yet support trading should
        raise NotImplementedError with a clear message — never silently
        succeed."""
        raise NotImplementedError
