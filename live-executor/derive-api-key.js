// derive-api-key.js
//
// One-time helper: derive Polymarket CLOB API credentials from a wallet
// private key. The CLOB requires a triplet (key, secret, passphrase) that
// is bound to the signing wallet. This script signs an EIP-712 request,
// receives the credentials from the API, and prints them in .env format.
//
// Usage:
//   1. Populate PRIVATE_KEY (and optionally FUNDER_ADDRESS) in .env.
//   2. Run: node derive-api-key.js
//   3. Copy the three POLYMARKET_* lines into .env.
//   4. Done — credentials persist server-side, you only do this once
//      per wallet (running again returns the same triplet).

import 'dotenv/config';
import { ClobClient } from '@polymarket/clob-client';
import { Wallet } from 'ethers';

const HOST = process.env.HOST || 'https://clob.polymarket.com';
const CHAIN_ID = Number.parseInt(process.env.CHAIN_ID || '137', 10);
const PRIVATE_KEY = process.env.PRIVATE_KEY;
const FUNDER = process.env.FUNDER_ADDRESS || null;

function fail(msg, code = 1) {
  console.error(`[derive-api-key] ERROR: ${msg}`);
  process.exit(code);
}

if (!PRIVATE_KEY) {
  fail('PRIVATE_KEY env var is required (set it in .env first)');
}
if (!/^0x[0-9a-fA-F]{64}$/.test(PRIVATE_KEY)) {
  fail('PRIVATE_KEY must be 0x-prefixed 32-byte hex (64 hex chars)');
}
if (!Number.isFinite(CHAIN_ID) || CHAIN_ID <= 0) {
  fail(`CHAIN_ID invalid: ${process.env.CHAIN_ID}`);
}

const wallet = new Wallet(PRIVATE_KEY);

console.log('--- derive-api-key ---');
console.log(`signer  : ${wallet.address}`);
console.log(`funder  : ${FUNDER ?? '(unset — signer acts as own funder)'}`);
console.log(`host    : ${HOST}`);
console.log(`chainId : ${CHAIN_ID}`);
console.log('');
console.log('Signing EIP-712 derivation request and contacting CLOB...');

let creds;
try {
  const client = new ClobClient(HOST, CHAIN_ID, wallet);
  // createOrDeriveApiKey returns the existing triplet if one already exists
  // for this wallet, otherwise creates a new one. Idempotent — safe to rerun.
  creds = await client.createOrDeriveApiKey();
} catch (err) {
  const detail = err?.response?.data
    ? JSON.stringify(err.response.data)
    : err?.message || String(err);
  fail(`derivation failed: ${detail}`, 2);
}

if (!creds || !creds.key || !creds.secret || !creds.passphrase) {
  fail(`unexpected response shape: ${JSON.stringify(creds)}`, 3);
}

console.log('');
console.log('=== API CREDENTIALS ===');
console.log('Paste these three lines into live-executor/.env (chmod 600):');
console.log('');
console.log(`POLYMARKET_API_KEY=${creds.key}`);
console.log(`POLYMARKET_SECRET=${creds.secret}`);
console.log(`POLYMARKET_PASSPHRASE=${creds.passphrase}`);
console.log('');
console.log('Credentials are now persisted server-side and tied to the');
console.log('signing wallet. Re-running this script returns the same triplet.');
