#!/usr/bin/env python3
"""
paper_watchdog.py — Process health monitor for the SigForge bot stack.

Detects silent failures that would otherwise accumulate losses unnoticed:
    1. PM2 process down or stuck restarting
    2. Balance drained rapidly ($50+ drop in 5 minutes)
    3. State file stale (no update for > 2 hours when activity expected)
    4. HALT flag created (drawdown circuit breaker fired)
    5. Restart loops (3+ restarts within one check window)

Sends Telegram alerts (deduplicated; same key suppressed for 30 minutes).
Logs all observations to disk regardless of alert delivery.

Usage:
    python3 paper_watchdog.py

Configuration via environment (defaults shown):
    SIGFORGE_TELEGRAM_BOT_TOKEN   — Telegram bot token. Empty = log-only mode.
    SIGFORGE_TELEGRAM_CHAT_ID     — Target chat. Empty = log-only mode.
    SIGFORGE_DATA_DIR             — /opt/sigforge/weather/data
    SIGFORGE_CHECK_INTERVAL_SEC   — 300
    SIGFORGE_ALERT_COOLDOWN_SEC   — 1800
    SIGFORGE_BALANCE_DROP_USD     — 50
    SIGFORGE_STATE_STALE_HOURS    — 2
    SIGFORGE_WATCHED_PROCESSES    — comma-separated PM2 names

Architecture: single-process, non-blocking. Each check pass is bounded by the
PM2 jlist timeout (15s) plus filesystem reads. The loop sleeps the full check
interval between passes — there is no thread pool, no async machinery.
Simplicity beats throughput for monitoring workloads.

Output:
    /opt/sigforge/weather/data/paper_watchdog.log         — append-only log
    /opt/sigforge/weather/data/paper_watchdog_state.json  — alert dedup state
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ─── Configuration ──────────────────────────────────────────────────────

BOT_TOKEN: str = os.environ.get("SIGFORGE_TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID: str = os.environ.get("SIGFORGE_TELEGRAM_CHAT_ID", "").strip()

DATA_DIR = Path(os.environ.get("SIGFORGE_DATA_DIR", "/opt/sigforge/weather/data"))
LOG_PATH = DATA_DIR / "paper_watchdog.log"
STATE_PATH = DATA_DIR / "paper_watchdog_state.json"

CHECK_INTERVAL_SEC: int = int(os.environ.get("SIGFORGE_CHECK_INTERVAL_SEC", "300"))
ALERT_COOLDOWN_SEC: int = int(os.environ.get("SIGFORGE_ALERT_COOLDOWN_SEC", "1800"))
BALANCE_DROP_USD: float = float(os.environ.get("SIGFORGE_BALANCE_DROP_USD", "50"))
STATE_STALE_HOURS: float = float(os.environ.get("SIGFORGE_STATE_STALE_HOURS", "2"))
RESTART_LOOP_THRESHOLD: int = int(os.environ.get("SIGFORGE_RESTART_LOOP_THRESHOLD", "3"))

_DEFAULT_PROCESSES = (
    "coldmath-bot,coldmath-safety,"
    "arb-paper,cointrick-paper,sport-sniper,esports-copy,weather-copy,"
    "weather-arb,weather-mkt,weather-resolver,weather-redeem,"
    "master-node"
)
WATCHED_PROCESSES: list[str] = [
    name.strip() for name in
    os.environ.get("SIGFORGE_WATCHED_PROCESSES", _DEFAULT_PROCESSES).split(",")
    if name.strip()
]

# Maps PM2 process name → file path whose `balance` field is monitored.
BALANCE_PATHS: dict[str, str] = {
    "coldmath-bot": "/opt/sigforge/weather/coldmath_bot/data/state.json",
}

# Maps PM2 process name → HALT flag path. Presence triggers HALT alert.
HALT_PATHS: dict[str, str] = {
    "coldmath-bot": "/opt/sigforge/weather/coldmath_bot/data/HALTED.flag",
}


# ─── Utilities ──────────────────────────────────────────────────────────

def utc_now_str() -> str:
    """ISO-8601 UTC timestamp with second precision."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(message: str) -> None:
    """Write a line to stdout and the log file. Never raises."""
    line = f"{utc_now_str()} {message}"
    print(line, flush=True)
    try:
        with LOG_PATH.open("a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def telegram_send(text: str) -> bool:
    """Send a Telegram message. Returns True on success, False otherwise.
    No-op (returns True) if BOT_TOKEN or CHAT_ID is unset (log-only mode)."""
    if not BOT_TOKEN or not CHAT_ID:
        return True
    try:
        payload = urllib.parse.urlencode({
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data=payload,
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as exc:  # network/HTTP errors are expected; never crash watchdog
        log(f"telegram_send_error: {exc}")
        return False


def load_state() -> dict[str, Any]:
    """Read the dedup state file. Returns empty dict on first run or read error."""
    try:
        return json.loads(STATE_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state: dict[str, Any]) -> None:
    """Persist the dedup state. Writes are best-effort; logged on failure."""
    try:
        STATE_PATH.write_text(json.dumps(state, indent=2))
    except OSError as exc:
        log(f"save_state_error: {exc}")


def pm2_list() -> list[dict[str, Any]]:
    """Run `pm2 jlist`. Returns parsed JSON or empty list on failure."""
    try:
        out = subprocess.check_output(["pm2", "jlist"], timeout=15)
        return json.loads(out.decode())
    except Exception as exc:
        log(f"pm2_jlist_error: {exc}")
        return []


def now_epoch() -> int:
    return int(time.time())


def alert(state: dict[str, Any], key: str, message: str) -> None:
    """Send an alert with cooldown deduplication.

    Same `key` will not re-fire within ALERT_COOLDOWN_SEC. Each fire is logged
    regardless of Telegram delivery — log is the source of truth."""
    last_at = state.setdefault("alerts", {}).get(key, 0)
    now = now_epoch()
    if now - last_at < ALERT_COOLDOWN_SEC:
        log(f"alert_suppressed[{key}] {message}")
        return
    log(f"ALERT[{key}] {message}")
    if telegram_send(message):
        state["alerts"][key] = now


# ─── Health checks ──────────────────────────────────────────────────────

def check_processes(state: dict[str, Any], procs: list[dict[str, Any]]) -> None:
    """Detect missing processes, non-online status, and restart loops."""
    proc_by_name = {p["name"]: p for p in procs}
    last_restarts: dict[str, int] = state.setdefault("restarts", {})

    for name in WATCHED_PROCESSES:
        proc = proc_by_name.get(name)
        if proc is None:
            alert(state, f"missing:{name}",
                  f"⚠️ <b>{name}</b> NOT FOUND in pm2 list")
            continue

        env = proc.get("pm2_env", {})
        status = env.get("status", "?")
        restart_count = env.get("restart_time", 0)

        if status != "online":
            alert(state, f"down:{name}",
                  f"🔴 <b>{name}</b> status={status} (pid={proc.get('pid')})")

        previous = last_restarts.get(name, restart_count)
        delta = restart_count - previous
        last_restarts[name] = restart_count
        if delta >= RESTART_LOOP_THRESHOLD:
            alert(state, f"loop:{name}",
                  f"⚠️ <b>{name}</b> restart loop: {delta} restarts in last {CHECK_INTERVAL_SEC // 60}min")


def check_balances(state: dict[str, Any]) -> None:
    """Detect rapid balance drops in tracked state files."""
    last_balances: dict[str, float] = state.setdefault("balances", {})

    for bot, path in BALANCE_PATHS.items():
        try:
            data = json.loads(Path(path).read_text())
            balance = float(data.get("balance", 0))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            alert(state, f"state_err:{bot}",
                  f"🔴 <b>{bot}</b>: cannot read state.json — {exc}")
            continue

        previous = last_balances.get(bot)
        last_balances[bot] = balance
        if previous is None:
            continue
        drop = previous - balance
        if drop >= BALANCE_DROP_USD:
            alert(state, f"drain:{bot}",
                  f"💸 <b>{bot}</b> balance ${previous:.2f} → ${balance:.2f} "
                  f"(-${drop:.2f}) in last {CHECK_INTERVAL_SEC // 60}min")


def check_state_freshness(state: dict[str, Any]) -> None:
    """Detect bots whose state file has not been touched for too long."""
    threshold = STATE_STALE_HOURS * 3600
    now = now_epoch()
    for bot, path in BALANCE_PATHS.items():
        try:
            mtime = int(Path(path).stat().st_mtime)
        except OSError:
            continue
        age_seconds = now - mtime
        if age_seconds > threshold:
            hours = age_seconds / 3600
            alert(state, f"silent:{bot}",
                  f"🌚 <b>{bot}</b> state silent for {hours:.1f}h (no updates)")


def check_halt_flags(state: dict[str, Any]) -> None:
    """Detect newly-created HALT flags."""
    halts_seen: dict[str, int] = state.setdefault("halts_seen", {})

    for bot, path in HALT_PATHS.items():
        flag_path = Path(path)
        if flag_path.exists():
            try:
                mtime = int(flag_path.stat().st_mtime)
            except OSError:
                mtime = now_epoch()
            if halts_seen.get(bot) != mtime:
                try:
                    info = flag_path.read_text()
                except OSError:
                    info = "(could not read)"
                alert(state, f"halted:{bot}:{mtime}",
                      f"🚨 <b>{bot}</b> HALTED\n<pre>{info[:500]}</pre>")
                halts_seen[bot] = mtime
        elif bot in halts_seen:
            del halts_seen[bot]  # halt was cleared


# ─── Main loop ──────────────────────────────────────────────────────────

def run_pass(state: dict[str, Any]) -> None:
    """Execute one full health-check pass."""
    procs = pm2_list()
    if not procs:
        alert(state, "pm2_unreachable",
              "🆘 paper_watchdog: pm2 jlist returned empty/error")
        return
    check_processes(state, procs)
    check_balances(state)
    check_state_freshness(state)
    check_halt_flags(state)


def main() -> None:
    log("paper_watchdog starting")
    log(f"watching {len(WATCHED_PROCESSES)} processes, "
        f"{len(BALANCE_PATHS)} balances, "
        f"telegram_enabled={bool(BOT_TOKEN and CHAT_ID)}")

    if BOT_TOKEN and CHAT_ID:
        telegram_send("🟢 <b>paper_watchdog</b> started — monitoring paper bot stack")

    while True:
        state = load_state()
        try:
            run_pass(state)
        except Exception as exc:
            log(f"main_loop_error: {exc}")
        save_state(state)
        time.sleep(CHECK_INTERVAL_SEC)


if __name__ == "__main__":
    main()
