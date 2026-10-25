/**
 * Parity smoke: JS reference Biot–Savart/LIA vs sst-core filament kernels.
 * Also exercises the HTTP physics-server contract when sst-core loads.
 */
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
import {
  PHYSICS_PROTOCOL_VERSION,
  PhysicsMethod,
  assertPhysicsRequest,
  assertPhysicsResponse,
  makePhysicsRequest
} from '../packages/contracts/src/index.js';

const require = createRequire(import.meta.url);
const __dirname = dirname(fileURLToPath(import.meta.url));
const C0 = 0.1395;
const DELTA = { hol: 0.5, vast: 0.25, gp: 0.615 };

function circle(n, R = 0.07, z = 0) {
  const pts = [];
  for (let i = 0; i < n; i++) {
    const t = (2 * Math.PI * i) / n;
    pts.push([R * Math.cos(t), R * Math.sin(t), z]);
  }
  return pts;
}

/** Minimal VL-parity velocityCore (no external overlays, one filament). */
function jsVelocity(points, circulation, options) {
  const N = points.length;
  const a = options.aSim;
  const a2 = a * a;
  const eD = Math.exp(options.coreDelta);
  const liaOnly = !!options.liaOnly;
  const pref = circulation / (4 * Math.PI);
  const mid = new Float64Array(3 * N);
  const dl = new Float64Array(3 * N);
  for (let k = 0; k < N; k++) {
    const k2 = (k + 1) % N;
    for (let d = 0; d < 3; d++) {
      mid[3 * k + d] = 0.5 * (points[k][d] + points[k2][d]);
      dl[3 * k + d] = points[k2][d] - points[k][d];
    }
  }
  const V = [];
  let umax = 0;
  for (let i = 0; i < N; i++) {
    const im = (i - 1 + N) % N;
    const ip = i;
    const px = points[i][0];
    const py = points[i][1];
    const pz = points[i][2];
    const dmx = dl[3 * im];
    const dmy = dl[3 * im + 1];
    const dmz = dl[3 * im + 2];
    const dpx = dl[3 * ip];
    const dpy = dl[3 * ip + 1];
    const dpz = dl[3 * ip + 2];
    const lm = Math.hypot(dmx, dmy, dmz);
    const lp = Math.hypot(dpx, dpy, dpz);
    const cxv = dmy * dpz - dmz * dpy;
    const cyv = dmz * dpx - dmx * dpz;
    const czv = dmx * dpy - dmy * dpx;
    const lf = pref * (Math.log(2 * Math.sqrt(lm * lp) / (eD * a)) + options.liaConstant) * 2 / (lm * lp * (lm + lp));
    let ux = lf * cxv;
    let uy = lf * cyv;
    let uz = lf * czv;
    if (!liaOnly) {
      for (let j = 0; j < N; j++) {
        if (j === im || j === ip) continue;
        const rx = px - mid[3 * j];
        const ry = py - mid[3 * j + 1];
        const rz = pz - mid[3 * j + 2];
        const r2 = rx * rx + ry * ry + rz * rz; // self filament: reg=0
        const inv = pref / (r2 * Math.sqrt(r2));
        ux += (dl[3 * j + 1] * rz - dl[3 * j + 2] * ry) * inv;
        uy += (dl[3 * j + 2] * rx - dl[3 * j] * rz) * inv;
        uz += (dl[3 * j] * ry - dl[3 * j + 1] * rx) * inv;
      }
    }
    V.push([ux, uy, uz]);
    const um = ux * ux + uy * uy + uz * uz;
    if (um > umax) umax = um;
  }
  return { velocity: [V], maximumSpeed: Math.sqrt(umax) };
}

function maxAbsDelta(a, b) {
  let m = 0;
  for (let i = 0; i < a.length; i++) {
    for (let k = 0; k < a[i].length; k++) {
      for (let d = 0; d < 3; d++) {
        m = Math.max(m, Math.abs(a[i][k][d] - b[i][k][d]));
      }
    }
  }
  return m;
}

function loadSst() {
  const candidates = [
    'sst-core',
    join(__dirname, '..', 'node_modules', 'sst-core'),
    join(__dirname, '..', '..', '..', 'SSTcore')
  ];
  let last;
  for (const id of candidates) {
    try {
      return require(id);
    } catch (err) {
      last = err;
    }
  }
  throw last || new Error('sst-core not found');
}

function assert(cond, msg) {
  if (!cond) throw new Error(msg);
}

// --- contract unit checks (no native required) ---
{
  const req = makePhysicsRequest({
    method: PhysicsMethod.FILAMENT_VELOCITY,
    filaments: [{ points: circle(8), circulation: 1 }],
    options: { liaOnly: true, aSim: 1e-3 }
  });
  assertPhysicsRequest(req);
  assert(req.protocolVersion === PHYSICS_PROTOCOL_VERSION, 'protocol version');
  const bad = { ...req, protocolVersion: 'nope' };
  let threw = false;
  try {
    assertPhysicsRequest(bad);
  } catch {
    threw = true;
  }
  assert(threw, 'bad protocol must throw');
  console.log('ok contracts');
}

const sst = loadSst();
assert(sst.isNative, 'sst-core must be native for this parity test');
assert(typeof sst.computeFilamentVelocity === 'function', 'computeFilamentVelocity missing');
assert(typeof sst.rk4Step === 'function', 'rk4Step missing');

const opts = {
  liaOnly: false,
  aSim: 1.5e-3,
  coreRadius: 1.5e-3,
  coreDelta: DELTA.vast,
  liaConstant: C0
};
const points = circle(64);
const circulation = 0.002;
const fils = [{
  id: 'A',
  carrier: 'A',
  points,
  circulation,
  ghost: false,
  source: true
}];

const js = jsVelocity(points, circulation, opts);
const native = sst.computeFilamentVelocity(fils, opts);
const dVel = maxAbsDelta(js.velocity, native.velocity);
const dSpeed = Math.abs(js.maximumSpeed - native.maximumSpeed);
console.log(`velocity max|Δ|=${dVel} speed|Δ|=${dSpeed}`);
assert(dVel < 1e-9, `velocity parity too large: ${dVel}`);
assert(dSpeed < 1e-9, `speed parity too large: ${dSpeed}`);

const dt = 1e-4;
const stepped = sst.rk4Step(fils, dt, opts);
assert(Array.isArray(stepped.filaments) && stepped.filaments[0].points.length === 64, 'rk4 points');
assert(Number.isFinite(stepped.maximumStageSpeed) && stepped.maximumStageSpeed > 0, 'rk4 stage speed');

// LIA-only smoke
const liaOpts = { ...opts, liaOnly: true };
const jsLia = jsVelocity(points, circulation, liaOpts);
const nLia = sst.computeFilamentVelocity(fils, liaOpts);
const dLia = maxAbsDelta(jsLia.velocity, nLia.velocity);
console.log(`lia max|Δ|=${dLia}`);
assert(dLia < 1e-9, `lia parity too large: ${dLia}`);

console.log('ok sst-core parity', sst.version, 'native=' + sst.isNative);

// HTTP smoke against physics-server (spawn briefly)
const physicsPort = 41749;
const child = spawn(process.execPath, [join(__dirname, 'physics-server.mjs')], {
  cwd: join(__dirname, '..'),
  env: { ...process.env, SSTCORE_PHYSICS_PORT: String(physicsPort) },
  stdio: ['ignore', 'pipe', 'pipe'],
  windowsHide: true
});

function waitReady(ms = 8000) {
  return new Promise((resolve, reject) => {
    const t0 = Date.now();
    const timer = setInterval(async () => {
      if (Date.now() - t0 > ms) {
        clearInterval(timer);
        reject(new Error('physics-server startup timeout'));
        return;
      }
      try {
        const res = await fetch(`http://127.0.0.1:${physicsPort}/health`);
        if (res.ok) {
          clearInterval(timer);
          resolve(await res.json());
        }
      } catch {
        /* retry */
      }
    }, 100);
  });
}

try {
  const health = await waitReady();
  assertPhysicsResponse(health);
  assert(health.ok && health.isNative, 'health must report native ok');

  const velBody = makePhysicsRequest({
    method: PhysicsMethod.FILAMENT_VELOCITY,
    filaments: fils,
    options: opts
  });
  const velRes = await fetch(`http://127.0.0.1:${physicsPort}/filament/velocity`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(velBody)
  }).then((r) => r.json());
  assertPhysicsResponse(velRes);
  assert(velRes.ok, 'velocity HTTP ok');
  const dHttp = maxAbsDelta(js.velocity, velRes.velocity);
  assert(dHttp < 1e-9, `HTTP velocity parity ${dHttp}`);

  const rkBody = makePhysicsRequest({
    method: PhysicsMethod.FILAMENT_RK4,
    filaments: fils,
    dt,
    options: opts
  });
  const rkRes = await fetch(`http://127.0.0.1:${physicsPort}/filament/rk4`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(rkBody)
  }).then((r) => r.json());
  assertPhysicsResponse(rkRes);
  assert(rkRes.ok && rkRes.filaments[0].points.length === 64, 'rk4 HTTP');

  console.log('ok physics-server HTTP', `elapsedMs≈${velRes.elapsedMs}`);
} finally {
  child.kill();
}

console.log('test-physics-parity: PASS');
