"""Kalshi adapter — auth scaffold only.

Kalshi (kalshi.com) is a CFTC-regulated US prediction-market exchange.
The trading interface is documented at https://trading-api.readme.io/.

Why this is scaffold-only:

  - Trading requires a US-resident KYC-verified account. SigForge is an
    EU-based research project; we cannot legally trade on Kalshi without
    a different operating entity.
  - Read-only data is available behind login but Kalshi rate-limits
    aggressively for unauthenticated polling.
  - The auth path (RSA-PSS signature over a timestamp + method + path) is
    non-trivial and not worth implementing speculatively. The structure
    below documents the contract and stops there.

Use case for keeping this file in the tree: it documents the boundary.
A reviewer or future contributor can see exactly where Kalshi support
will plug in, what it requires, and why it is currently inert.
"""
from __future__ import annotations

from typing import Iterable

from .base import Book, Market, Order, OrderResult, Platform

API_BASE = "https://trading-api.kalshi.com/trade-api/v2"


class KalshiAdapter(Platform):
    name = "kalshi"
    supports_trading = False

    def __init__(
        self,
        api_base: str = API_BASE,
        api_key_id: str | None = None,
        rsa_private_key_pem: str | None = None,
        timeout_sec: float = 15.0,
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.api_key_id = api_key_id
        self.rsa_private_key_pem = rsa_private_key_pem
        self.timeout = timeout_sec
        # Auth flow (when implemented):
        #   1. For each request, build a string-to-sign:
        #        f"{ts_ms}{method.upper()}{path}"
        #   2. Sign with RSA-PSS-SHA256, base64-encode the signature.
        #   3. Send headers:
        #        KALSHI-ACCESS-KEY: <api_key_id>
        #        KALSHI-ACCESS-TIMESTAMP: <ts_ms>
        #        KALSHI-ACCESS-SIGNATURE: <base64 signature>
        #   See trading-api.readme.io for full spec including key rotation.

    def _not_implemented(self, what: str) -> NotImplementedError:
        return NotImplementedError(
            f"Kalshi {what} is not implemented. SigForge is EU-based and "
            f"cannot operate on Kalshi without a US-resident entity. The "
            f"adapter exists as a scaffold so the boundary is explicit; "
            f"populate api_key_id + RSA private key and implement the "
            f"_signed_get/_signed_post helpers to enable."
        )

    def fetch_markets(self, **_) -> Iterable[Market]:
        raise self._not_implemented("market enumeration")

    def fetch_market(self, market_id: str) -> Market | None:  # noqa: ARG002
        raise self._not_implemented("single-market fetch")

    def fetch_book(self, market_id: str, outcome_idx: int) -> Book | None:  # noqa: ARG002
        raise self._not_implemented("order-book fetch")

    def submit_order(self, order: Order) -> OrderResult:  # noqa: ARG002
        raise self._not_implemented("order submission")
