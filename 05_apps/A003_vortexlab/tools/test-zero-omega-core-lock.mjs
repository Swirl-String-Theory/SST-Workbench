/**
 * Regression: Rankine core-flow lock must not silently replace Ω=0 by ±1 rad/s.
 * Bug: syncCoreFlowCoupling forced P.Om = ±1 under coreFlowLock when |Om|<1e-12,
 * while the FLOW UI could still show 0.
 */
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const policy = require(path.join(root, 'apps/web/src/legacy/zero-omega-core-lock-policy.js'));

let pass = 0;
function eq(a, b, msg) {
  if (a !== b) throw new Error(`${msg}: received ${JSON.stringify(a)}, expected ${JSON.stringify(b)}`);
  console.log('PASS', msg);
  pass++;
}
function approx(a, b, msg, eps = 1e-15) {
  if (!(Math.abs(a - b) <= eps)) throw new Error(`${msg}: received ${a}, expected ${b}`);
  console.log('PASS', msg);
  pass++;
}

// --- Document the pre-patch defect ---
{
  const P = { Om: 0, revOm: false, coreFlowLock: true };
  eq(policy.legacyForceUnitOmega(P), true, 'legacy: zero Ω triggers rewrite');
  approx(P.Om, 1, 'legacy: Om forced to +1');
  eq(P.coreFlowLock, true, 'legacy: lock stayed on');
}
{
  const P = { Om: 0, revOm: true, coreFlowLock: true };
  policy.legacyForceUnitOmega(P);
  approx(P.Om, -1, 'legacy: revOm forced Om to -1');
}

// --- Correct policy: unlock, keep Ω=0 ---
{
  let notice = '';
  const lockCheckbox = { checked: true };
  const P = { Om: 0, revOm: false, coreFlowLock: true };
  const r = policy.applyZeroOmegaUnderCoreLock(P, {
    lockCheckbox,
    setNotice: (s) => { notice = s; },
  });
  eq(r.handled, true, 'zero Ω under lock is handled');
  eq(r.unlocked, true, 'zero Ω unlocks Rankine lock');
  eq(P.coreFlowLock, false, 'coreFlowLock cleared');
  approx(P.Om, 0, 'Om remains 0 (never forced to ±1)');
  eq(lockCheckbox.checked, false, 'checkbox synced off');
  eq(notice, policy.ZERO_OMEGA_UNLOCK_NOTICE, 'user-visible unlock notice');
}

// Near-zero still counts as zero
{
  const P = { Om: 1e-13, revOm: false, coreFlowLock: true };
  const r = policy.applyZeroOmegaUnderCoreLock(P, {});
  eq(r.unlocked, true, 'sub-eps Om unlocks');
  approx(P.Om, 1e-13, 'sub-eps Om value preserved');
}

// Non-zero Ω: lock remains; coupling path may continue
{
  const P = { Om: 1.5, revOm: false, coreFlowLock: true };
  const r = policy.applyZeroOmegaUnderCoreLock(P, {});
  eq(r.handled, false, 'nonzero Om not handled by zero policy');
  eq(P.coreFlowLock, true, 'nonzero Om keeps lock');
  approx(P.Om, 1.5, 'nonzero Om unchanged');
}

// Lock already off: no-op
{
  const P = { Om: 0, revOm: false, coreFlowLock: false };
  const r = policy.applyZeroOmegaUnderCoreLock(P, {});
  eq(r.handled, false, 'no lock → policy idle');
  approx(P.Om, 0, 'idle path leaves Om=0');
}

// Runtime source must not contain the silent ±1 rewrite
{
  const runtime = fs.readFileSync(
    path.join(root, 'apps/web/src/legacy/vortexlab-runtime.js'),
    'utf8',
  );
  eq(
    runtime.includes('P.Om=P.revOm?-1:1'),
    false,
    'runtime no longer contains silent ±1 Om rewrite',
  );
  eq(
    runtime.includes('VortexLabZeroOmegaCoreLockPolicy'),
    true,
    'runtime calls shared zero-Ω policy',
  );
  const monolith = fs.readFileSync(
    path.join(root, 'reference/vortexring-lab-v7.6.25b.html'),
    'utf8',
  );
  eq(
    monolith.includes('P.Om=P.revOm?-1:1'),
    false,
    'monolith reference no longer contains silent ±1 Om rewrite',
  );
  eq(
    monolith.includes('Ω_wall=0 is niet verenigbaar'),
    true,
    'monolith reference unlocks with notice on Ω=0',
  );
}

console.log(`\n${pass} zero-Ω core-lock checks PASS`);
