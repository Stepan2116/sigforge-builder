# SigForge — Tools

Infrastructure tooling that supports the strategy validation lifecycle.
Each tool runs as an independent process; together they form the operational
backbone of the SigForge bot stack.

---

## `paper_watchdog.py` — Process health monitor

Detects silent failures across the bot stack:
- PM2 process down or stuck in restart loop
- Balance drained rapidly (configurable threshold)
- State file stale (no update for too long)
- HALT flag created (drawdown circuit breaker fired)

Sends Telegram alerts with deduplication. Falls back to log-only mode if
`SIGFORGE_TELEGRAM_BOT_TOKEN` is not set.

**Why this exists:** On 2026-05-06 we caught a stop-loss bug on the coldmath
bot only because of manual inspection — the patched function was the wrong
one (hourly scan instead of 10-minute monitor). The watchdog now monitors
silent failures across the entire stack so this class of bug cannot
accumulate undetected.

Run:
```
python3 paper_watchdog.py
```

Configure via environment (see module docstring for full list).

---

## `backtest.py` — Strategy variant replay

Reads archived market files (each containing position + resolution + snapshot
timeline) and replays hypothetical strategy variants against them. Computes
per-variant metrics (trades, win rate, total PnL, max drawdown, Sharpe).

**Philosophy:** Used for **falsification**, not pattern fishing. Running 50
random variants and picking the best is overfitting. Running one specific
variant proposed by the thesis and confirming the edge holds is validation.

See [`../docs/METHODOLOGY.md`](../docs/METHODOLOGY.md) section 6 for the
philosophical framing.

Run:
```
python3 backtest.py /path/to/markets [/path/to/markets2 ...]
python3 backtest.py --strategy combined_patches /path/to/markets
```

Adding a new strategy variant: define a function with signature
`(market: dict, position: dict) -> {"entry": bool, ...}`, register it in the
`STRATEGIES` dict, re-run.

---

## Why these are separate from `/strategies/`

The `/strategies/` directory contains **trade-generating** code — bots that
buy and sell. The `/tools/` directory contains **infrastructure** that
supports those strategies but does not itself trade. Separation matters for:

- **Capital risk attribution.** Tools cannot lose money. Strategies can.
- **Deployment cadence.** Tools update slowly; strategies iterate fast.
- **Testing surface.** Tool failure is operational; strategy failure is
  capital-impacting.

This mirrors the SigForge methodology: separate concerns, attribute outcomes.
