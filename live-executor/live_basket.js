#!/usr/bin/env node
/**
 * live_basket.js — SigForge live execution layer for the BASKET strategy
 * (multi-leg weather arbitrage) with Polymarket Builder Code attribution.
 *
 * Architecture:
 *   Python BASKET strategy writes a signal as queue/<id>.json. This process
 *   polls the queue every 5s; for each signal it submits each leg, polls
 *   for fill confirmation, and unwinds already-filled legs if any later leg
 *   fails (so a basket arb cannot leave partial exposure).
 *
 *   Python decides which trade to take — JS never decides. Python never
 *   holds a key — JS handles all signing. This separation is intentional.
 *
 * Modes:
 *   --dry-run    print what would be sent, do not submit. Safe to run
 *                without funding or API creds.
 *   (no flag)    real execution. Requires PRIVATE_KEY + FUNDER_ADDRESS
 *                + Polymarket API creds in .env.
 *
 * Configuration via .env (same directory):
 *   PRIVATE_KEY            wallet private key (hex, 0x-prefixed)
 *   FUNDER_ADDRESS         proxy wallet address
 *   POLYMARKET_API_KEY     issued via `npm run derive`
 *   POLYMARKET_SECRET      issued via `npm run derive`
 *   POLYMARKET_PASSPHRASE  issued via `npm run derive`
 *   BUILDER_CODE           bytes32 builder code (default: SigForge's)
 *   CHAIN_ID               137 for Polygon mainnet (default)
 *   HOST                   https://clob.polymarket.com (default)
 *   POLL_INTERVAL_MS       queue poll cadence in ms (default: 5000)
 *   FILL_TIMEOUT_MS        how long to wait for an order to fill before
 *                          treating it as failed (default: 30000)
 *   FILL_POLL_INTERVAL_MS  cadence for polling order status (default: 2000)
 *   TELEGRAM_BOT_TOKEN     opt-in alerts for failed/halted signals
 *   TELEGRAM_CHAT_ID       target chat for the above
 *   HEARTBEAT_PATH         absolute path to liveness file watched by
 *                          paper_watchdog.py (default: data/heartbeat.json)
 */
import 'dotenv/config';
import { readFile, writeFile, readdir, mkdir, rename } from 'node:fs/promises';
import { existsSync, statSync } from 'node:fs';
import path from 'node:path';
import url from 'node:url';
import { Wallet } from 'ethers';
import { ClobClient, OrderType, Side } from '@polymarket/clob-client';

const __dirname = path.dirname(url.fileURLToPath(import.meta.url));

// ─── Config ─────────────────────────────────────────────────────────────
const HOST = process.env.HOST || 'https://clob.polymarket.com';
const CHAIN_ID = Number.parseInt(process.env.CHAIN_ID || '137', 10);
const BUILDER_CODE = process.env.BUILDER_CODE
  || '0x6a386ecc3a926b109e131d736ab0053cb6bb6745638ddefa2693247db62d8ba1';

const POLL_INTERVAL_MS = Number.parseInt(process.env.POLL_INTERVAL_MS || '5000', 10);
const FILL_TIMEOUT_MS = Number.parseInt(process.env.FILL_TIMEOUT_MS || '30000', 10);
const FILL_POLL_INTERVAL_MS = Number.parseInt(process.env.FILL_POLL_INTERVAL_MS || '2000', 10);

const QUEUE_DIR = path.join(__dirname, 'queue');
const LOG_DIR = path.join(__dirname, 'log');
const PROCESSED_DIR = path.join(__dirname, 'queue/processed');
const DATA_DIR = path.join(__dirname, 'data');
const HEARTBEAT_PATH = process.env.HEARTBEAT_PATH || path.join(DATA_DIR, 'heartbeat.json');

const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || '';
const TELEGRAM_CHAT_ID = process.env.TELEGRAM_CHAT_ID || '';

const DRY_RUN = process.argv.includes('--dry-run');

// Order statuses surfaced by the CLOB
const STATUS_FILLED = ['MATCHED', 'FILLED'];
const STATUS_PENDING = ['LIVE', 'PENDING'];
const STATUS_FAILED = ['CANCELED', 'CANCELLED', 'EXPIRED', 'REJECTED'];

// ─── Logging ────────────────────────────────────────────────────────────
const ts = () => new Date().toISOString();
const log = (...a) => console.log(`${ts()} live_basket:`, ...a);
const err = (...a) => console.error(`${ts()} live_basket ERROR:`, ...a);
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

// ─── Setup ──────────────────────────────────────────────────────────────
async function ensureDirs() {
  for (const d of [QUEUE_DIR, LOG_DIR, PROCESSED_DIR, DATA_DIR]) {
    if (!existsSync(d)) await mkdir(d, { recursive: true });
  }
}

// ─── Telegram (opt-in) ──────────────────────────────────────────────────
async function notify(message) {
  if (!TELEGRAM_BOT_TOKEN || !TELEGRAM_CHAT_ID) return;
  try {
    const res = await fetch(
      `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: TELEGRAM_CHAT_ID,
          text: message,
          parse_mode: 'HTML',
        }),
      },
    );
    if (!res.ok) {
      err('telegram non-2xx:', res.status, await res.text().catch(() => ''));
    }
  } catch (e) {
    err('telegram send failed:', e.message);
  }
}

// ─── Heartbeat for paper_watchdog ───────────────────────────────────────
async function writeHeartbeat(extra = {}) {
  try {
    await writeFile(HEARTBEAT_PATH, JSON.stringify({
      ts: ts(),
      pid: process.pid,
      dry_run: DRY_RUN,
      ...extra,
    }));
  } catch (e) {
    err('heartbeat write failed:', e.message);
  }
}

// ─── Client init ────────────────────────────────────────────────────────
let client = null;

async function initClient() {
  if (DRY_RUN) {
    log('DRY-RUN mode — client will not actually submit orders.');
    return;
  }
  const pk = process.env.PRIVATE_KEY;
  const funder = process.env.FUNDER_ADDRESS;
  const apiKey = process.env.POLYMARKET_API_KEY;
  const secret = process.env.POLYMARKET_SECRET;
  const passphrase = process.env.POLYMARKET_PASSPHRASE;

  if (!pk) throw new Error('PRIVATE_KEY missing in env');
  if (!funder) throw new Error('FUNDER_ADDRESS missing in env');
  if (!apiKey || !secret || !passphrase) {
    throw new Error('Polymarket API creds missing — run `npm run derive` first');
  }

  const signer = new Wallet(pk);
  client = new ClobClient(
    HOST,
    CHAIN_ID,
    signer,
    { key: apiKey, secret, passphrase },
    2, // signatureType=2 for proxy/funder wallet
    funder,
  );

  log(`client initialized · funder=${funder} · builder=${BUILDER_CODE.slice(0, 10)}…`);
}

// ─── Signal validation ──────────────────────────────────────────────────
function validateSignal(sig) {
  if (!sig || typeof sig !== 'object') throw new Error('signal not an object');
  if (!sig.id) throw new Error('signal missing id');
  if (!Array.isArray(sig.legs) || sig.legs.length < 1) {
    throw new Error('signal must have ≥1 leg');
  }
  for (const [i, leg] of sig.legs.entries()) {
    if (!leg.tokenID) throw new Error(`leg[${i}] missing tokenID`);
    if (typeof leg.price !== 'number' || leg.price <= 0 || leg.price >= 1) {
      throw new Error(`leg[${i}] price must be a number in (0,1)`);
    }
    if (typeof leg.size !== 'number' || leg.size <= 0) {
      throw new Error(`leg[${i}] size must be a positive number`);
    }
    if (!['BUY', 'SELL'].includes(leg.side)) {
      throw new Error(`leg[${i}] side must be BUY or SELL`);
    }
  }
}

// ─── Per-leg execution ──────────────────────────────────────────────────
function buildOrderArgs(leg) {
  return {
    tokenID: leg.tokenID,
    price: leg.price,
    size: leg.size,
    side: leg.side === 'BUY' ? Side.BUY : Side.SELL,
    builderCode: BUILDER_CODE,
  };
}

async function submitLeg(leg, tickSize, negRisk) {
  const orderArgs = buildOrderArgs(leg);
  if (DRY_RUN) {
    log('  [DRY-RUN] would submit:', JSON.stringify(orderArgs));
    return { dryRun: true, orderID: `dry-${Date.now()}-${Math.random().toString(36).slice(2, 8)}` };
  }
  const resp = await client.createAndPostOrder(
    orderArgs,
    { tickSize: tickSize || '0.01', negRisk: !!negRisk },
    OrderType.GTC,
  );
  if (!resp || resp.success === false) {
    throw new Error(`CLOB rejected order: ${JSON.stringify(resp)}`);
  }
  return { dryRun: false, orderID: resp.orderID || resp.orderId, response: resp };
}

/**
 * Poll the order status until it transitions to a terminal state or the
 * timeout elapses. Returns {filled, status, lastPoll} — `filled` is true
 * iff the CLOB confirmed a match.
 */
async function pollOrderFill(orderID) {
  if (DRY_RUN) return { filled: true, status: 'DRY_RUN' };
  const deadline = Date.now() + FILL_TIMEOUT_MS;
  let lastStatus = 'UNKNOWN';
  while (Date.now() < deadline) {
    try {
      const order = await client.getOrder(orderID);
      lastStatus = (order?.status || 'UNKNOWN').toUpperCase();
      if (STATUS_FILLED.includes(lastStatus)) return { filled: true, status: lastStatus };
      if (STATUS_FAILED.includes(lastStatus)) return { filled: false, status: lastStatus };
      // else still pending / live — keep polling
    } catch (e) {
      err(`  getOrder(${orderID}) failed:`, e.message);
    }
    await sleep(FILL_POLL_INTERVAL_MS);
  }
  return { filled: false, status: `TIMEOUT_${lastStatus}` };
}

/**
 * Unwind already-filled legs by issuing the opposite side at the same size
 * and price. For BASKET (all BUYs at $0.20-$0.40), the unwind is SELL at
 * the same price — which crosses the book aggressively and exits fast in
 * thin late-resolve weather markets. Better to take small loss than carry
 * uncovered partial exposure.
 *
 * NOTE: This is a defensive primitive. Production-grade unwind needs more
 * nuance (sell at midprice with retry, halt if slippage too wide). For MVP
 * we prefer correctness over price optimization.
 */
async function unwindFilledLegs(filledLegs, sig) {
  if (filledLegs.length === 0) return [];
  log(`  UNWINDING ${filledLegs.length} filled leg(s) — opposite side at same price`);
  const results = [];
  for (const filled of filledLegs) {
    const orig = sig.legs[filled.leg];
    const opposite = {
      tokenID: orig.tokenID,
      price: orig.price,
      size: orig.size,
      side: orig.side === 'BUY' ? 'SELL' : 'BUY',
    };
    try {
      const submitted = await submitLeg(opposite, sig.tickSize, sig.negRisk);
      const fill = await pollOrderFill(submitted.orderID);
      results.push({ leg: filled.leg, unwindOrderID: submitted.orderID, ...fill });
      log(`  unwound leg[${filled.leg}] · status=${fill.status}`);
    } catch (e) {
      err(`  unwind leg[${filled.leg}] FAILED:`, e.message);
      results.push({ leg: filled.leg, unwindOk: false, error: e.message });
    }
  }
  return results;
}

// ─── Signal lifecycle ───────────────────────────────────────────────────
async function processSignal(filename) {
  const filepath = path.join(QUEUE_DIR, filename);
  log(`processing ${filename}`);

  let sig;
  try {
    sig = JSON.parse(await readFile(filepath, 'utf-8'));
    validateSignal(sig);
  } catch (e) {
    err(`invalid signal ${filename}:`, e.message);
    await rename(filepath, path.join(PROCESSED_DIR, filename + '.invalid'));
    await notify(`🔴 <b>SigForge</b> rejected signal <code>${filename}</code>: ${e.message}`);
    return;
  }

  const legResults = [];
  const filledForUnwind = [];
  let allOk = true;
  let haltReason = null;

  for (const [i, leg] of sig.legs.entries()) {
    try {
      const submitted = await submitLeg(leg, sig.tickSize, sig.negRisk);
      const fill = await pollOrderFill(submitted.orderID);
      const entry = {
        leg: i,
        ok: fill.filled,
        orderID: submitted.orderID,
        status: fill.status,
        leg_spec: leg,
      };
      legResults.push(entry);
      if (fill.filled) {
        filledForUnwind.push(entry);
        log(`  leg[${i}] FILLED · order=${submitted.orderID} · status=${fill.status}`);
      } else {
        allOk = false;
        haltReason = `leg[${i}] did not fill (status=${fill.status})`;
        err(`  leg[${i}] DID NOT FILL · status=${fill.status} — halting basket`);
        break;
      }
    } catch (e) {
      allOk = false;
      haltReason = `leg[${i}] submit failed: ${e.message}`;
      legResults.push({ leg: i, ok: false, error: e.message, leg_spec: leg });
      err(`  leg[${i}] SUBMIT FAILED:`, e.message);
      break;
    }
  }

  let unwindResults = [];
  if (!allOk && filledForUnwind.length > 0) {
    unwindResults = await unwindFilledLegs(filledForUnwind, sig);
  }

  const logEntry = {
    signal_id: sig.id,
    processed_at: ts(),
    dry_run: DRY_RUN,
    all_legs_ok: allOk,
    halt_reason: haltReason,
    legs: legResults,
    unwind: unwindResults,
    signal: sig,
  };

  await writeFile(
    path.join(LOG_DIR, sig.id + '.json'),
    JSON.stringify(logEntry, null, 2),
  );

  await rename(
    filepath,
    path.join(PROCESSED_DIR, allOk ? filename : filename + '.failed'),
  );

  log(`done ${filename} · all_ok=${allOk}${haltReason ? ` · ${haltReason}` : ''}`);

  if (!allOk) {
    const unwindMsg = unwindResults.length > 0
      ? `\nUnwound ${unwindResults.length} filled leg(s).`
      : '';
    await notify(
      `🔴 <b>SigForge BASKET halted</b>\n` +
      `signal: <code>${sig.id}</code>\n` +
      `reason: ${haltReason}${unwindMsg}`,
    );
  }
}

// ─── Poll loop ──────────────────────────────────────────────────────────
async function poll() {
  let entries;
  try {
    entries = await readdir(QUEUE_DIR);
  } catch (e) {
    err('cannot read queue:', e.message);
    return;
  }

  const signals = entries
    .filter(f => f.endsWith('.json'))
    .filter(f => statSync(path.join(QUEUE_DIR, f)).isFile())
    .sort();

  for (const f of signals) {
    try {
      await processSignal(f);
    } catch (e) {
      err(`unhandled error on ${f}:`, e.message);
      await notify(`🔴 <b>SigForge</b> unhandled error on <code>${f}</code>: ${e.message}`);
    }
  }

  await writeHeartbeat({ last_poll: ts(), queue_size: signals.length });
}

async function main() {
  await ensureDirs();
  await initClient();
  log(`starting · poll=${POLL_INTERVAL_MS}ms · fillTimeout=${FILL_TIMEOUT_MS}ms · dry_run=${DRY_RUN}`);
  await writeHeartbeat({ event: 'startup' });

  while (true) {
    await poll();
    await sleep(POLL_INTERVAL_MS);
  }
}

process.on('SIGTERM', async () => {
  log('SIGTERM received, exiting cleanly');
  await writeHeartbeat({ event: 'shutdown' });
  process.exit(0);
});

main().catch(async (e) => {
  err('fatal:', e);
  await notify(`🔴 <b>SigForge</b> live_basket FATAL: ${e?.message || e}`);
  process.exit(1);
});
