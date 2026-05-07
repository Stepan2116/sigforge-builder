"""Manifold adapter — read-only, alpha.

Manifold (manifold.markets) is a play-money prediction market with full
public REST. Read coverage in this adapter is sufficient for strategy
research and reproducibility — the YIELD-FARM and BASKET signals can be
backtested against Manifold history without modification.

Trading is intentionally deferred:

  - Manifold trading uses an internal play-money currency ("mana"), not
    crypto. The economic model differs from Polymarket — strategies tuned
    for real money do not transfer 1:1.
  - The auth path (API key tied to a user account) is straightforward to
    implement when needed; the scaffold is in place but `submit_order`
    raises NotImplementedError so accidental live calls cannot succeed.

To enable trading: implement `_post()` with `Authorization: Key <api_key>`
and uncomment the body of `submit_order`. A complete reference lives at
https://docs.manifold.markets/api.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Iterable

from .base import Book, Market, Order, OrderResult, Platform

API_BASE = "https://api.manifold.markets/v0"


class ManifoldAdapter(Platform):
    name = "manifold"
    supports_trading = False  # read-only until trading scaffold is wired up

    def __init__(
        self,
        api_base: str = API_BASE,
        api_key: str | None = None,
        timeout_sec: float = 15.0,
        user_agent: str = "sigforge-manifold-adapter/0.1",
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout_sec
        self.user_agent = user_agent

    def _get(self, path: str, params: dict | None = None) -> Any:
        url = f"{self.api_base}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read())

    def fetch_markets(self, *, limit: int = 500, **_) -> Iterable[Market]:
        # Manifold paginates with `before` (cursor on slug). For the MVP
        # we yield the first page only; production strategies that need
        # full enumeration call `fetch_markets` repeatedly with `before=`.
        data = self._get("/markets", {"limit": min(int(limit), 1000)})
        if not isinstance(data, list):
            return
        for m in data:
            yield self._normalize_market(m)

    def fetch_market(self, market_id: str) -> Market | None:
        try:
            d = self._get(f"/market/{market_id}")
        except Exception:
            return None
        if not isinstance(d, dict):
            return None
        return self._normalize_market(d)

    def fetch_book(self, market_id: str, outcome_idx: int) -> Book | None:
        # Binary markets expose `probability`; use it as both bid and ask
        # (no L2 depth in the public API). Multi-outcome markets expose
        # `answers` with per-answer probabilities.
        m = self.fetch_market(market_id)
        if not m:
            return None
        raw = m.raw
        prob: float | None = None
        if raw.get("outcomeType") == "BINARY":
            prob = float(raw.get("probability") or 0)
        else:
            answers = raw.get("answers") or []
            if 0 <= outcome_idx < len(answers):
                prob = float(answers[outcome_idx].get("probability") or 0)
        if prob is None or prob <= 0 or prob >= 1:
            return None
        return Book(
            market_id=market_id,
            outcome_idx=outcome_idx,
            bid=prob,
            ask=prob,
            bid_size=None,
            ask_size=None,
            ts_iso=raw.get("lastUpdatedTime") or "",
        )

    def submit_order(self, order: Order) -> OrderResult:
        raise NotImplementedError(
            "Manifold trading is not yet wired up. The scaffold is in "
            "place — provide an API key and implement _post() to enable. "
            "See strategies/adapters/manifold.py docstring for details."
        )

    @staticmethod
    def _normalize_market(m: dict[str, Any]) -> Market:
        outcome_type = m.get("outcomeType")
        if outcome_type == "BINARY":
            outcomes = ["YES", "NO"]
        else:
            answers = m.get("answers") or []
            outcomes = [str(a.get("text", a.get("id", ""))) for a in answers]
        return Market(
            id=str(m.get("id") or ""),
            slug=str(m.get("slug") or m.get("id") or ""),
            question=str(m.get("question") or ""),
            outcomes=outcomes,
            end_date=m.get("closeTime"),  # epoch ms; strategy code converts
            closed=bool(m.get("isResolved") or m.get("isClosed")),
            volume_24h_usd=float(m.get("volume24Hours") or m.get("volume") or 0),
            raw=m,
        )
