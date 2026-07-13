/**
 * Regressietests A–F voor Vortexlab v6.1 modules.
 * Run: node tests/vortexlab-regression.mjs
 */

import { gaussIntegral, writheOfFilament, linkingFilaments } from '../physics/topology.js';
import {
  segmentSegmentDistance,
  minGapBetweenFilaments,
  dminSelf,
  minGapNodes,
} from '../physics/contact.js';
import { dtCFL, DELTA, lminFromY } from '../physics/timestep.js';
import {
  GAMMA0_SST,
  rankineCoreSpeed,
  displaySimilarityRatio,
  similarityRadiusFromGamma,
} from '../physics/sst-similarity.js';
import { bodyFrameOmega, chiHatFromFilament } from '../physics/body-frame.js';
import { filamentResolutionMetrics, minBoundaryRatio } from '../diagnostics/stability.js';
import {
  kelvinSpeed,
  ringMeanRadius,
  hashFloat64Array,
  arcLength,
} from '../diagnostics/conservation.js';
import { vec3 } from '../physics/vec3.js';

const PASS = [];
const FAIL = [];

function assert(name, cond, detail = '') {
  if (cond) PASS.push(name);
  else FAIL.push({ name, detail });
}

function ringY(R, N, z = 0, off = 0) {
  const Y = new Float64Array(off + 3 * N);
  for (let k = 0; k < N; k++) {
    const th = (2 * Math.PI * k) / N;
    Y[off + 3 * k] = R * Math.cos(th);
    Y[off + 3 * k + 1] = R * Math.sin(th);
    Y[off + 3 * k + 2] = z;
  }
  return Y;
}

function fil(off, N, carrier = 'A') {
  return { off, N, carrier };
}

// ——— Test B: ringconvergentie (Kelvin + geometrie) ———
function testB() {
  const gamma = 2e-3;
  const a = 1.5e-3;
  const R = 0.07;
  const Ukelvin = kelvinSpeed(R, gamma, a, DELTA.hol);
  for (const N of [48, 96, 144, 192, 288]) {
    const Y = ringY(R, N);
    const f = fil(0, N);
    const Wr = writheOfFilament(Y, f);
    const L = arcLength(Y, f);
    const Rm = ringMeanRadius(Y, f);
    assert(`B writhe≈0 N=${N}`, Math.abs(Wr) < 0.02, `Wr=${Wr}`);
    assert(`B L stable N=${N}`, Math.abs(L - 2 * Math.PI * R) / L < 0.02, `L=${L}`);
    assert(`B R stable N=${N}`, Math.abs(Rm - R) / R < 0.02, `Rm=${Rm}`);
    // Kelvin formula sanity (analytic target, not integrated speed)
    const err = Math.abs(Ukelvin - gamma / (4 * Math.PI * R) * (Math.log((8 * R) / a) - DELTA.hol)) / Ukelvin;
    assert(`B Kelvin formula N=${N}`, err < 1e-6, `err=${err}`);
  }
}

// ——— Test C: topologische integer (unlinked + ring writhe) ———
function testC() {
  const N = 128;
  const R = 1;
  // Unlinked parallel rings (y offset avoids intersection)
  const Y = new Float64Array(6 * N);
  for (let k = 0; k < N; k++) {
    const th = (2 * Math.PI * k) / N;
    Y[3 * k] = R * Math.cos(th);
    Y[3 * k + 1] = R * Math.sin(th);
    Y[3 * k + 2] = 0;
    const o = 3 * N;
    Y[o + 3 * k] = R * Math.cos(th);
    Y[o + 3 * k + 1] = 2;
    Y[o + 3 * k + 2] = R * Math.sin(th);
  }
  const fA = fil(0, N);
  const fB = fil(3 * N, N);
  let Lk = linkingFilaments(Y, fA, fB);
  assert('C unlinked Lk≈0', Math.abs(Lk) < 0.05, `Lk=${Lk}`);

  // Scale invariance of linking (uniform scale cancels in Gauss integral)
  const Y2 = Float64Array.from(Y, (x) => 2 * x);
  Lk = linkingFilaments(Y2, fA, fB);
  assert('C scale Lk stable', Math.abs(Lk) < 0.05, `Lk2=${Lk}`);

  // Ring writhe = 0
  const Yr = ringY(0.5, 64);
  const fr = fil(0, 64);
  const Wr = writheOfFilament(Yr, fr);
  assert('C ring Wr≈0', Math.abs(Wr) < 0.02, `Wr=${Wr}`);

  // Chi PCA finite
  const chi = chiHatFromFilament(Yr, fr, { isRing: false });
  assert('C chi PCA', chi && isFinite(chi.phi), JSON.stringify(chi));
}

// ——— Test D: segment vs node contact ———
function testD() {
  const p1 = vec3(0, 0, 0);
  const p2 = vec3(1, 0, 0);
  const p3 = vec3(0.5, 0.02, 0);
  const p4 = vec3(0.5, -0.02, 0);
  const dSeg = segmentSegmentDistance(p1, p2, p3, p4);
  const dNode = Math.min(
    Math.hypot(0.5, 0.02, 0),
    Math.hypot(0.5, -0.02, 0),
    Math.hypot(0.5, 0.02, 0),
    Math.hypot(0.5, -0.02, 0),
  );
  assert('D seg < node', dSeg < dNode, `dSeg=${dSeg} dNode=${dNode}`);
  const a = 0.05;
  assert('D seg < 3a', dSeg < 3 * a, `dSeg=${dSeg}`);
  assert('D node > 3a', dNode > 3 * a, `dNode=${dNode}`);
}

// ——— Test E: passieve diagnose (hash stabiel) ———
function testE() {
  const Y = ringY(0.07, 96);
  const fils = [fil(0, 96)];
  const P = { a: 0.0015, core: 'hol', Rcyl: 0.25, Hcyl: 0.5 };
  const hBefore = hashFloat64Array(Y);
  const m = filamentResolutionMetrics(Y, fils[0], { a: P.a, core: P.core, deltaTable: DELTA, c0: 0.1395 });
  const bnd = minBoundaryRatio(Y, fils, { Rcyl: P.Rcyl, zMin: -P.Hcyl, zMax: P.Hcyl, a: P.a });
  const hAfter = hashFloat64Array(Y);
  assert('E Y hash unchanged', hBefore === hAfter, `${hBefore} vs ${hAfter}`);
  assert('E metrics finite', isFinite(m.q) && isFinite(bnd), `q=${m.q} bnd=${bnd}`);
}

// ——— Test A: stap-debet determinisme (mock) ———
function testA() {
  const dt = 0.01;
  const targets = [0.1, 0.5, 1.0];
  const trajectories = targets.map((T) => {
    let t = 0;
    let debt = 0;
    const steps = [];
    while (t < T - 1e-12) {
      debt += dt * 0.016; // one frame worth at 60fps
      while (debt >= dt) {
        steps.push(t);
        t += dt;
        debt -= dt;
      }
    }
    return steps;
  });
  for (let i = 1; i < trajectories.length; i++) {
    const a = trajectories[0];
    const b = trajectories[i];
    const n = Math.min(a.length, b.length);
    let maxDiff = 0;
    for (let k = 0; k < n; k++) maxDiff = Math.max(maxDiff, Math.abs(a[k] - b[k]));
    assert(`A step order i=${i}`, maxDiff < 1e-15, `maxDiff=${maxDiff} len ${a.length}/${b.length}`);
  }
}

// ——— Test F: CFL + RK stage max (component) ———
function testF() {
  const Y = ringY(0.07, 48);
  const fils = [fil(0, 48)];
  const lm = lminFromY(Y, fils);
  const base = { lm, gammaMax: 2e-3, a: 1.5e-3, core: 'hol' };
  const dtKelvin = dtCFL({ ...base, lastUmax: 1e6 });
  const dtAdvLow = dtCFL({ ...base, lastUmax: 0.001 });
  const dtAdvHigh = dtCFL({ ...base, lastUmax: 1.0 });
  assert('F advective cap binds', dtAdvHigh < dtAdvLow, `low=${dtAdvLow} high=${dtAdvHigh}`);
  assert('F Kelvin limit < huge u', dtKelvin < dtAdvLow, `kelvin=${dtKelvin}`);
}

// ——— SST similarity label sanity ———
function testSST() {
  const a = similarityRadiusFromGamma(10 * GAMMA0_SST, 1);
  const ratio = displaySimilarityRatio(a, 1);
  assert('SST display ratio ≪ 1', ratio < 1e-8, `ratio=${ratio}`);
  assert('SST u_core', rankineCoreSpeed(a, 1) > 0);
}

// ——— Body frame centroid subtraction ———
function testBodyFrame() {
  const N = 32;
  const Y = ringY(0.05, N);
  const f = fil(0, N);
  const V = new Float64Array(3 * N);
  const vz = 0.02;
  for (let k = 0; k < N; k++) V[3 * k + 2] = vz;
  const om = bodyFrameOmega(Y, f, V);
  assert('B body Ω≈0 pure translation', Math.abs(om) < 1e-6, `om=${om}`);
}

function testSelfGap() {
  const Y = ringY(0.07, 64);
  const f = fil(0, 64);
  const ds = dminSelf(Y, f);
  assert('self gap ring > 0', ds > 0.005, `ds=${ds}`);
}

// ——— Run ———
testA();
testB();
testC();
testD();
testE();
testF();
testSST();
testBodyFrame();
testSelfGap();

console.log(`\nVortexlab regression: ${PASS.length} passed, ${FAIL.length} failed`);
if (FAIL.length) {
  for (const f of FAIL) console.error(`  FAIL ${f.name}: ${f.detail}`);
  process.exit(1);
}
console.log('All tests passed.');
