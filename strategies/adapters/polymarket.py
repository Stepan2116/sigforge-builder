"""Polymarket adapter — production-tested.

Read paths use the public Gamma API (no auth). Trading is delegated to
the TypeScript live-executor (`live-executor/live_basket.js`) because the
Python `py-clob-client` does not yet expose the Builder Code field. This
adapter calls `submit_order` by writing a queue file the JS executor
picks up — see `../../live-executor/README.md`.

Most strategy code does not call `submit_order` directly; the paper
strategies stop at queueing the signal and let the executor handle the
network leg. That separation is what lets us keep the validation
framework and the live execution layer independently testable.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .base import Book, Market, Order, OrderResult, Platform

GAMMA_BASE = "https://gamma-api.polymarket.com/markets"
CLOB_HOST = "https://clob.polymarket.com"
DEFAULT_QUEUE_DIR = "/opt/sigforge/live-executor/queue"


class PolymarketAdapter(Platform):
    name = "polymarket"
    supports_trading = True   # via JS executor

    def __init__(
        self,
        gamma_url: str = GAMMA_BASE,
        clob_host: str = CLOB_HOST,
        timeout_sec: float = 15.0,
        user_agent: str = "sigforge-polymarket-adapter/1.0",
        queue_dir: str | None = None,
    ) -> None:
        self.gamma_url = gamma_url
        self.clob_host = clob_host
        self.timeout = timeout_sec
        self.user_agent = user_agent
        self.queue_dir = Path(queue_dir or os.environ.get("SF_QUEUE_DIR", DEFAULT_QUEUE_DIR))

    # ─── HTTP helper ────────────────────────────────────────────────────
    def _get(self, url: str) -> Any:
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read())

    # ─── Read paths ─────────────────────────────────────────────────────
    def fetch_markets(self, *, limit: int = 500, closed: bool = False,
                      order: str = "volume24hr", **_) -> Iterable[Market]:
        qs = urllib.parse.urlencode({
            "closed": "true" if closed else "false",
            "active": "true",
            "limit": limit,
            "order": order,
            "ascending": "false",
        })
        data = self._get(f"{self.gamma_url}?{qs}")
        if not isinstance(data, list):
            return
        for m in data:
            yield self._normalize_market(m)

    def fetch_market(self, market_id: str) -> Market | None:
        qs = urllib.parse.urlencode({"id": market_id})
        try:
            data = self._get(f"{self.gamma_url}?{qs}")
        except Exception:
            return None
        if isinstance(data, list) and data:
            return self._normalize_market(data[0])
        if isinstance(data, dict):
            return self._normalize_market(data)
        return None

    def fetch_book(self, market_id: str, outcome_idx: int) -> Book | None:
        # Gamma exposes outcomePrices (last-traded), not full book depth.
        # Full L2 depth requires the CLOB websocket — out of scope for the
        # adapter MVP; live-executor consumes that directly when needed.
        m = self.fetch_market(market_id)
        if not m:
            return None
        prices = self._parse_prices(m.raw.get("outcomePrices"))
        if not prices or outcome_idx >= len(prices):
            return None
        last = prices[outcome_idx]
        return Book(
            market_id=market_id,
            outcome_idx=outcome_idx,
            bid=last,
            ask=last,
            bid_size=None,
            ask_size=None,
            ts_iso=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    # ─── Write path (queue for JS executor) ─────────────────────────────
    def submit_order(self, order: Order) -> OrderResult:
        """Write a single-leg signal to the executor queue. Multi-leg
        signals (BASKET strategy) bypass this method and write the queue
        file directly with all legs at once — see strategies/arb_basket.py.
        """
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        signal_id = f"{order.side.lower()}-{uuid.uuid4().hex[:12]}"
        path = self.queue_dir / f"{signal_id}.json"
        path.write_text(json.dumps({
            "id": signal_id,
            "strategy": "ADAPTER_DIRECT",
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "legs": [{
                "tokenID": order.market_id,
                "price": order.price,
                "size": order.size,
                "side": order.side,
            }],
            "tickSize": "0.01",
            "negRisk": False,
        }, separators=(",", ":")))
        return OrderResult(
            order_id=signal_id,
            filled=False,
            pending=True,
            avg_fill_price=None,
            raw={"queue_path": str(path)},
        )

    # ─── Normalization helpers ──────────────────────────────────────────
    @staticmethod
    def _parse_prices(raw: Any) -> list[float] | None:
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                return None
        if not raw:
            return None
        try:
            return [float(p) for p in raw]
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_outcomes(raw: Any) -> list[str]:
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                return []
        return list(raw or [])

    def _normalize_market(self, m: dict[str, Any]) -> Market:
        return Market(
            id=str(m.get("id") or m.get("conditionId") or ""),
            slug=str(m.get("slug") or m.get("id") or ""),
            question=str(m.get("question") or ""),
            outcomes=self._parse_outcomes(m.get("outcomes")),
            end_date=m.get("endDate"),
            closed=bool(m.get("closed") or m.get("archived")),
            volume_24h_usd=float(m.get("volume24hr") or 0),
            raw=m,
        )
