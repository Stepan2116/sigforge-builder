# live-executor

> *Thin Node.js layer that reads strategy signals from the Python paper bots
> and submits real CLOB orders to Polymarket with Builder Code attribution.*

The Python side never holds a private key. The JS side never decides which
trade to take. Clean separation. Each side does one thing well.

---

## Why this exists

The Python `py-clob-client` (latest `0.34.6`) does not yet expose the
`builderCode` field. Only `@polymarket/clob-client` (TypeScript) and the
Rust client support attribution today. This service is the workaround:
keep the strategy logic in Python (where the validation framework lives)
and put the live execution layer in TypeScript (where attribution works).

---

## Architecture

```
┌────────────────────┐    file/queue    ┌──────────────────────┐
│  Python BASKET bot │ ────────────────▶│  live_basket.js      │
│  (decides trades)  │   queue/*.json   │  (submits orders)    │
└────────────────────┘                  └──────────┬───────────┘
                                                   │
                                                   ▼
                                        ┌──────────────────────┐
                                        │  Polymarket CLOB     │
                                        │  builderCode = ours  │
                                        └──────────────────────┘
```

Signal lifecycle:

1. Python writes `queue/<id>.json` with one or more order legs.
2. `live_basket.js` polls the queue every 5 seconds.
3. For each signal: validates legs, signs each via `ClobClient.createAndPostOrder`,
   submits with `builderCode` attached.
4. Records outcome to `log/<id>.json`.
5. Moves the signal to `queue/processed/<id>.json` (or `.failed`).

---

## Signal shape

```json
{
  "id": "basket-1234567890",
  "strategy": "BASKET",
  "ts": "2026-05-07T15:00:00Z",
  "legs": [
    { "tokenID": "0x...", "price": 0.30, "size": 5, "side": "BUY" },
    { "tokenID": "0x...", "price": 0.25, "size": 5, "side": "BUY" },
    { "tokenID": "0x...", "price": 0.20, "size": 5, "side": "BUY" }
  ],
  "tickSize": "0.01",
  "negRisk": false,
  "expected_profit_usd": 0.50
}
```

Every BASKET arbitrage opportunity becomes one signal with N legs (one
per bucket). The executor processes legs in sequence; if any leg fails,
it halts the signal and flags it `.failed`. Production logic should
then unwind already-filled legs at market — current MVP just stops and
requires manual review.

---

## Setup

### 1. Install dependencies

```bash
cd /opt/sigforge/live-executor
npm install
```

### 2. Configure credentials

Create `.env` in this directory (chmod 600 — never commit):

```
# required
PRIVATE_KEY=0xYOUR_HEX_PRIVATE_KEY
FUNDER_ADDRESS=0xYOUR_PROXY_WALLET_ADDRESS
POLYMARKET_API_KEY=...        # see "Derive API creds" below
POLYMARKET_SECRET=...
POLYMARKET_PASSPHRASE=...

# defaults — override only if you know why
BUILDER_CODE=0x6a386ecc3a926b109e131d736ab0053cb6bb6745638ddefa2693247db62d8ba1
CHAIN_ID=137
HOST=https://clob.polymarket.com
POLL_INTERVAL_MS=5000          # queue poll cadence
FILL_TIMEOUT_MS=30000          # how long to wait for an order to fill before failing
FILL_POLL_INTERVAL_MS=2000     # cadence for polling order status

# optional alerts
TELEGRAM_BOT_TOKEN=            # leave blank to disable
TELEGRAM_CHAT_ID=

# optional heartbeat (consumed by paper_watchdog.py)
HEARTBEAT_PATH=                # default: data/heartbeat.json
```

### 3. Derive API creds (one-time)

The Polymarket CLOB requires three API credentials derived from the wallet
private key. Run:

```bash
npm run derive
```

The script signs a derivation request and prints the API key, secret,
and passphrase. Paste them into `.env`.


### 4. Test in dry-run mode

```bash
npm run dryrun
```

Drop a sample signal into `queue/`:

```bash
echo '{"id":"test","strategy":"BASKET","ts":"2026-01-01T00:00:00Z","legs":[{"tokenID":"0xfoo","price":0.3,"size":5,"side":"BUY"}],"tickSize":"0.01","negRisk":false}' > queue/test.json
```

The executor logs what it would submit. No funds risked.

### 5. Go live

```bash
npm run live
```

---

## Safety properties

1. **Dry-run by default in development.** `--dry-run` flag prints all
   actions without submitting. Always test new signal formats this way first.
2. **Atomic per-leg.** Each leg is a separate signed order. If any fails
   (network, insufficient liquidity, etc.), processing halts and the signal
   is flagged `.failed` for manual review.
3. **Append-only logs.** `log/<id>.json` is created once per signal,
   immutable thereafter.
4. **Funder isolation.** Private key only ever in env file (chmod 600),
   never logged.
5. **Builder Code default.** Even if env var is missing, the default
   builder code (SigForge's) is hard-coded — orders never submit unattributed.

---

## Shipped

- ✅ One-time API credential derivation (`derive-api-key.js`).
- ✅ Per-leg fill confirmation polling — every order is polled to a
  terminal status before the next leg is submitted, so the basket cannot
  silently end up with un-confirmed fills.
- ✅ Leg-unwind logic — if any leg fails, every already-filled leg is
  reversed at the same price (best-effort exit). The signal is flagged
  `.failed` only after unwinding completes.
- ✅ Telegram alerts on rejected signals, halted baskets, and fatal
  errors (opt-in via `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`).
- ✅ Heartbeat file at `HEARTBEAT_PATH` updated each poll; consumed by
  `paper_watchdog.py` to detect a hung executor.
- ✅ Graceful `SIGTERM` handling so pm2 restarts emit a clean shutdown
  heartbeat.

## What is intentionally deferred

- **Smart-pricing on unwind.** Today unwind submits the opposite side at
  the same price as the original leg — guaranteed to cross the book in a
  liquid market, but suboptimal in thin late-resolve weather markets.
  Production logic should walk the book to find a tighter exit. Deferred
  until live trade volume justifies the complexity.
- **Multi-signal concurrency.** Signals are processed strictly in order;
  one slow basket blocks the queue. Acceptable while signal rate is
  <1/min. Will revisit when concurrent baskets become the norm.
- **Settlement-side accounting.** Realized PnL is computed by the Python
  side from on-chain redemption events, not by the executor. Keeps the
  separation of concerns clean.

---

## See also

- [`../strategies/BASKET.md`](../strategies/BASKET.md) — strategy spec.
- [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) — system layer.
- [`../docs/METHODOLOGY.md`](../docs/METHODOLOGY.md) — validation framework.
