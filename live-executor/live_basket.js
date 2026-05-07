#!/usr/bin/env node
/**
 * live_basket.js — SigForge live execution layer for the BASKET strategy
 * (multi-leg weather arbitrage) with Polymarket Builder Code attribution.
 *
 * Architecture:
 *   - Python BASKET strategy (paper) writes a trade signal as a JSON file
 *     to /opt/sigforge/live-executor/queue/<id>.json.
 *   - This process polls the queue every 5 seconds.
 *   - For each signal, validates legs, signs each via ClobClient, submits
 *     to the Polymarket CLOB with `builderCode` attached.
 *   - Records outcome to /opt/sigforge/live-executor/log/<id>.json.
 *
 * The Python side never holds a private key. The JS side never decides
 * which trade to take. Clean separation.
 *
 * Modes:
 *   --dry-run    : print what would be sent, do not submit. Safe to run
 *                  without funding.
 *   (no flag)    : real execution. Requires PRIVATE_KEY + FUNDER_ADDRESS
 *                  + Polymarket API creds in env.
 *
 * Configuration via .env (same directory):
 *   PRIVATE_KEY         — wallet private key (hex, 0x-prefixed)
 *   FUNDER_ADDRESS      — wallet funder address (proxy wallet)
 *   POLYMARKET_API_KEY  — issued via createOrDeriveApiKey
 *   POLYMARKET_SECRET   — issued via createOrDeriveApiKey
 *   POLYMARKET_PASSPHRASE — issued via createOrDeriveApiKey
 *   BUILDER_CODE        — bytes32 builder code (default: SigForge's)
 *   CHAIN_ID            — 137 for Polygon mainnet (default)
 *   HOST                — https://clob.polymarket.com (default)
 *
 * Usage:
 *   node live_basket.js --dry-run
 *   node live_basket.js
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
const CHAIN_ID = parseInt(process.env.CHAIN_ID || '137', 10);
const BUILDER_CODE = process.env.BUILDER_CODE
  || '0x6a386ecc3a926b109e131d736ab0053cb6bb6745638ddefa2693247db62d8ba1';

const QUEUE_DIR = path.join(__dirname, 'queue');
const LOG_DIR = path.join(__dirname, 'log');
const PROCESSED_DIR = path.join(__dirname, 'queue/processed');

const POLL_INTERVAL_MS = 5_000;
const DRY_RUN = process.argv.includes('--dry-run');

// ─── Logging ────────────────────────────────────────────────────────────
function ts() { return new Date().toISOString(); }
function log(...args) { console.log(`${ts()} live_basket:`, ...args); }
function err(...args) { console.error(`${ts()} live_basket ERROR:`, ...args); }

// ─── Setup directories ──────────────────────────────────────────────────
async function ensureDirs() {
  for (const d of [QUEUE_DIR, LOG_DIR, PROCESSED_DIR]) {
    if (!existsSync(d)) {
      await mkdir(d, { recursive: true });
    }
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
    throw new Error('Polymarket API creds missing — run derive-api-key.js first');
  }

  const signer = new Wallet(pk);
  client = new ClobClient(HOST, CHAIN_ID, signer, {
    key: apiKey,
    secret: secret,
    passphrase: passphrase,
  }, 2, funder); // signatureType=2 for proxy wallet

  log(`client initialized · funder=${funder} · builder=${BUILDER_CODE.slice(0, 10)}…`);
}

// ─── Signal handling ────────────────────────────────────────────────────
/**
 * Trade signal shape (from Python):
 * {
 *   "id": "basket-1234567890",
 *   "strategy": "BASKET",
 *   "ts": "2026-05-07T15:00:00Z",
 *   "legs": [
 *     { "tokenID": "0x...", "price": 0.30, "size": 5, "side": "BUY" },
 *     { "tokenID": "0x...", "price": 0.25, "size": 5, "side": "BUY" },
 *     ...
 *   ],
 *   "tickSize": "0.01",
 *   "negRisk": false,
 *   "expected_profit_usd": 0.50
 * }
 */
function validateSignal(sig) {
  if (!sig || typeof sig !== 'object') throw new Error('signal not an object');
  if (!sig.id) throw new Error('signal missing id');
  if (!Array.isArray(sig.legs) || sig.legs.length < 2) {
    throw new Error('signal must have ≥2 legs');
  }
  for (const [i, leg] of sig.legs.entries()) {
    if (!leg.tokenID) throw new Error(`leg[${i}] missing tokenID`);
    if (typeof leg.price !== 'number') throw new Error(`leg[${i}] price not a number`);
    if (typeof leg.size !== 'number') throw new Error(`leg[${i}] size not a number`);
    if (!['BUY', 'SELL'].includes(leg.side)) {
      throw new Error(`leg[${i}] side must be BUY or SELL`);
    }
  }
  return true;
}

async function executeLeg(leg, tickSize, negRisk) {
  const orderArgs = {
    tokenID: leg.tokenID,
    price: leg.price,
    size: leg.size,
    side: leg.side === 'BUY' ? Side.BUY : Side.SELL,
    builderCode: BUILDER_CODE, // ← attribution
  };

  if (DRY_RUN) {
    log(`  [DRY-RUN] would submit:`, JSON.stringify(orderArgs));
    return { dryRun: true, orderArgs };
  }

  const response = await client.createAndPostOrder(
    orderArgs,
    { tickSize: tickSize || '0.01', negRisk: !!negRisk },
    OrderType.GTC,
  );
  return { dryRun: false, response };
}

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
    return;
  }

  const results = [];
  let allOk = true;

  for (const [i, leg] of sig.legs.entries()) {
    try {
      const r = await executeLeg(leg, sig.tickSize, sig.negRisk);
      results.push({ leg: i, ok: true, ...r });
      log(`  leg[${i}] OK`);
    } catch (e) {
      results.push({ leg: i, ok: false, error: e.message });
      err(`  leg[${i}] FAILED:`, e.message);
      allOk = false;
      // For arb safety: if any leg fails, stop. Production logic should
      // unwind already-filled legs; this MVP just halts and flags.
      break;
    }
  }

  const logEntry = {
    signal_id: sig.id,
    processed_at: ts(),
    dry_run: DRY_RUN,
    all_legs_ok: allOk,
    legs: results,
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

  log(`done ${filename} · all_ok=${allOk}`);
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
    }
  }
}

async function main() {
  await ensureDirs();
  await initClient();
  log(`starting · poll interval ${POLL_INTERVAL_MS}ms · dry_run=${DRY_RUN}`);

  while (true) {
    await poll();
    await new Promise(r => setTimeout(r, POLL_INTERVAL_MS));
  }
}

main().catch(e => {
  err('fatal:', e);
  process.exit(1);
});
