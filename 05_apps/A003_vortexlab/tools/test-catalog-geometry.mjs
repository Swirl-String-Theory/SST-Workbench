import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { access } from 'node:fs/promises';

const require = createRequire(import.meta.url);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const G = require(path.join(root, 'apps/web/src/catalog-geometry.js'));

let failed = 0;
function assert(cond, msg) {
  if (!cond) {
    failed += 1;
    console.error('FAIL', msg);
  } else {
    console.log('PASS', msg);
  }
}

const coeffs = G.unitCircleCoeffs();
const n = 64;
const raw = G.sampleFourierParametric(coeffs, n);
assert(raw.length === 3 * n, 'parametric length 3N');
let rErr = 0;
for (let k = 0; k < n; k++) {
  const x = raw[3 * k];
  const y = raw[3 * k + 1];
  const z = raw[3 * k + 2];
  rErr = Math.max(rErr, Math.abs(Math.hypot(x, y) - 1), Math.abs(z));
}
assert(rErr < 1e-9, 'unit circle radius ≈ 1, z ≈ 0 (err=' + rErr + ')');

const entry = {
  components: [{ I: 1, coeffs, pointCount: n }],
};
const thumb = G.sampleEntryThumb(entry, 'ideal', 48);
assert(thumb.points.length === 1, 'thumb one component');
assert(thumb.points[0].length === 3 * 48, 'thumb resampled to 48');
assert(Math.abs(thumb.radius - 1) < 1e-12, 'normalized radius 1');

const kpEntry = {
  sourceRole: 'a006-seed-N1024',
  resolutionN: 1024,
  components: [{ I: 1, coeffs, pointCount: 256 }],
};
const kp = G.sampleCatalogComponent(kpEntry, kpEntry.components[0], 80, 'knotplot');
assert(kp.length === 3 * 80, 'knotplot path resamples to thumb N');

const pages = [
  'apps/web/catalog.html',
  'apps/web/styles/catalog.css',
  'apps/web/src/catalog-geometry.js',
  'apps/web/src/catalog-viewer.js',
];
for (const rel of pages) {
  try {
    await access(path.join(root, rel));
    console.log('PASS', 'exists', rel);
  } catch {
    failed += 1;
    console.error('FAIL', 'missing', rel);
  }
}

if (failed) {
  console.error(failed + ' catalog-geometry checks failed');
  process.exitCode = 1;
} else {
  console.log('OK catalog-geometry');
}
