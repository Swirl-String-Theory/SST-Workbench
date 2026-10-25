/**
 * Companion Node physics server for VortexLab.
 * Wraps sst-core computeFilamentVelocity / rk4Step on 127.0.0.1:4174.
 * Browser cannot load the N-API .node addon; this process can.
 */
import { createServer } from 'node:http';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  PHYSICS_PROTOCOL_VERSION,
  PhysicsMethod,
  assertPhysicsRequest,
  assertPhysicsResponse
} from '../packages/contracts/src/index.js';

const require = createRequire(import.meta.url);
const __dirname = dirname(fileURLToPath(import.meta.url));
const port = Number(process.env.SSTCORE_PHYSICS_PORT ?? 4174);
const host = process.env.SSTCORE_PHYSICS_HOST ?? '127.0.0.1';

let sst = null;
let loadError = null;

function loadSstCore() {
  if (sst || loadError) return;
  const candidates = [
    'sst-core',
    join(__dirname, '..', 'node_modules', 'sst-core'),
    join(__dirname, '..', '..', '..', 'SSTcore')
  ];
  for (const id of candidates) {
    try {
      sst = require(id);
      loadError = null;
      return;
    } catch (err) {
      loadError = err;
    }
  }
}

function cors(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Cache-Control', 'no-store');
}

function readJson(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => {
      try {
        const raw = Buffer.concat(chunks).toString('utf8');
        resolve(raw ? JSON.parse(raw) : {});
      } catch (err) {
        reject(err);
      }
    });
    req.on('error', reject);
  });
}

function sendJson(res, status, body) {
  cors(res);
  const text = JSON.stringify(body);
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(text);
}

function engineMeta() {
  loadSstCore();
  if (!sst) {
    return {
      protocolVersion: PHYSICS_PROTOCOL_VERSION,
      ok: false,
      engine: 'unavailable',
      isNative: false,
      error: loadError ? String(loadError.message || loadError) : 'sst-core not loaded'
    };
  }
  const caps = typeof sst.getCapabilities === 'function' ? sst.getCapabilities() : {};
  return {
    protocolVersion: PHYSICS_PROTOCOL_VERSION,
    ok: true,
    engine: sst.isNative ? 'sst-core-native' : (sst.isWasm ? 'sst-core-wasm' : 'sst-core'),
    engineVersion: sst.version || sst.engineVersion || 'unknown',
    isNative: !!sst.isNative,
    capabilities: {
      filamentVelocity: !!caps.filamentVelocity && typeof sst.computeFilamentVelocity === 'function',
      filamentIntegrator: !!caps.filamentIntegrator && typeof sst.rk4Step === 'function'
    }
  };
}

function normalizeFilaments(filaments) {
  if (!Array.isArray(filaments)) throw new TypeError('filaments must be an array');
  return filaments.map((f, i) => {
    if (!f || typeof f !== 'object') throw new TypeError(`filament[${i}] must be an object`);
    if (!Array.isArray(f.points) && !(f.points && f.points.length != null)) {
      throw new TypeError(`filament[${i}].points required`);
    }
    return {
      id: f.id != null ? String(f.id) : `f${i}`,
      carrier: f.carrier != null ? String(f.carrier) : 'A',
      points: f.points,
      circulation: Number(f.circulation ?? 0),
      ghost: !!f.ghost,
      source: f.source !== undefined ? !!f.source : !f.ghost
    };
  });
}

function handleVelocity(body) {
  loadSstCore();
  if (!sst || typeof sst.computeFilamentVelocity !== 'function') {
    throw new Error(loadError ? String(loadError.message || loadError) : 'computeFilamentVelocity unavailable');
  }
  const filaments = normalizeFilaments(body.filaments);
  const options = body.options || {};
  const t0 = performance.now();
  const result = sst.computeFilamentVelocity(filaments, options);
  return {
    protocolVersion: PHYSICS_PROTOCOL_VERSION,
    requestId: body.requestId,
    ok: true,
    engine: sst.isNative ? 'sst-core-native' : 'sst-core',
    engineVersion: sst.version,
    isNative: !!sst.isNative,
    velocity: result.velocity,
    maximumSpeed: result.maximumSpeed,
    elapsedMs: performance.now() - t0
  };
}

function handleRk4(body) {
  loadSstCore();
  if (!sst || typeof sst.rk4Step !== 'function') {
    throw new Error(loadError ? String(loadError.message || loadError) : 'rk4Step unavailable');
  }
  const filaments = normalizeFilaments(body.filaments);
  const dt = Number(body.dt);
  if (!(Number.isFinite(dt) && dt !== 0)) throw new TypeError('dt must be a finite non-zero number');
  const options = body.options || {};
  const t0 = performance.now();
  const result = sst.rk4Step(filaments, dt, options);
  return {
    protocolVersion: PHYSICS_PROTOCOL_VERSION,
    requestId: body.requestId,
    ok: true,
    engine: sst.isNative ? 'sst-core-native' : 'sst-core',
    engineVersion: sst.version,
    isNative: !!sst.isNative,
    filaments: result.filaments,
    maximumStageSpeed: result.maximumStageSpeed,
    elapsedMs: performance.now() - t0
  };
}

function routePath(url) {
  try {
    return new URL(url, `http://${host}:${port}`).pathname.replace(/\/+$/, '') || '/';
  } catch {
    return '/';
  }
}

createServer(async (req, res) => {
  cors(res);
  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const path = routePath(req.url);

  try {
    if ((req.method === 'GET' || req.method === 'POST') && (path === '/health' || path === '/')) {
      const meta = engineMeta();
      sendJson(res, meta.ok ? 200 : 503, {
        ...meta,
        method: PhysicsMethod.HEALTH,
        requestId: undefined
      });
      return;
    }

    if (req.method !== 'POST') {
      sendJson(res, 405, {
        protocolVersion: PHYSICS_PROTOCOL_VERSION,
        ok: false,
        engine: 'physics-server',
        error: 'method not allowed'
      });
      return;
    }

    const body = await readJson(req);
    if (path === '/filament/velocity' || body.method === PhysicsMethod.FILAMENT_VELOCITY) {
      const reqBody = {
        protocolVersion: body.protocolVersion || PHYSICS_PROTOCOL_VERSION,
        requestId: body.requestId || `vel-${Date.now()}`,
        method: PhysicsMethod.FILAMENT_VELOCITY,
        filaments: body.filaments,
        options: body.options || {}
      };
      assertPhysicsRequest(reqBody);
      const out = handleVelocity(reqBody);
      assertPhysicsResponse(out);
      sendJson(res, 200, out);
      return;
    }

    if (path === '/filament/rk4' || body.method === PhysicsMethod.FILAMENT_RK4) {
      const reqBody = {
        protocolVersion: body.protocolVersion || PHYSICS_PROTOCOL_VERSION,
        requestId: body.requestId || `rk4-${Date.now()}`,
        method: PhysicsMethod.FILAMENT_RK4,
        filaments: body.filaments,
        dt: body.dt,
        options: body.options || {}
      };
      assertPhysicsRequest(reqBody);
      const out = handleRk4(reqBody);
      assertPhysicsResponse(out);
      sendJson(res, 200, out);
      return;
    }

    sendJson(res, 404, {
      protocolVersion: PHYSICS_PROTOCOL_VERSION,
      ok: false,
      engine: 'physics-server',
      error: `unknown path ${path}`
    });
  } catch (err) {
    sendJson(res, 500, {
      protocolVersion: PHYSICS_PROTOCOL_VERSION,
      ok: false,
      engine: 'physics-server',
      error: String(err && err.message ? err.message : err)
    });
  }
}).listen(port, host, () => {
  loadSstCore();
  const meta = engineMeta();
  console.log(`VortexLab physics-server: http://${host}:${port}`);
  console.log(`  sst-core: ${meta.ok ? meta.engineVersion : 'UNAVAILABLE'} · native=${meta.isNative}`);
  if (!meta.ok) console.warn(`  load error: ${meta.error}`);
});
