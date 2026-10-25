import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const require = createRequire(import.meta.url);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const { parseXyzText, sampleXyzComponent } = require(path.join(root, 'apps/web/src/legacy/xyz-import.js'));

let failed = 0;
function assert(cond, msg) {
  if (!cond) {
    failed += 1;
    console.error('FAIL', msg);
  } else {
    console.log('PASS', msg);
  }
}

const single = parseXyzText(
  `0 0 0
1 0 0
1 1 0
0 1 0
`,
  'ring.xyz'
);
assert(single.ok, 'single component parses');
assert(single.entry?.componentCount === 1, 'single: one component');
assert(single.entry?.components?.[0]?.pointCount === 4, 'single: four vertices');

const multi = parseXyzText(
  `Component 0:
0 0 0
1 0 0
1 1 0
0 1 0

0 0 1
1 0 1
1 1 1
0 1 1
`,
  'link.xyz'
);
assert(multi.ok, 'multi-component with header parses');
assert(multi.entry?.componentCount === 2, 'multi: two components');
assert(multi.entry?.components?.[0]?.pointCount === 4 && multi.entry?.components?.[1]?.pointCount === 4, 'multi: 4+4 vertices');

const tooFew = parseXyzText(
  `0 0 0
1 0 0
0 1 0
`,
  'bad.xyz'
);
assert(!tooFew.ok && /minder dan vier/.test(tooFew.error || ''), 'rejects <4 vertices');

const empty = parseXyzText('Component only\n\n', 'empty.xyz');
assert(!empty.ok && /geen XYZ-componenten/.test(empty.error || ''), 'rejects empty geometry');

function resampleClosedCurve(raw, n) {
  const m = Math.floor(raw.length / 3);
  const out = new Float64Array(3 * n);
  for (let k = 0; k < n; k++) {
    const t = (k / n) * m;
    const i = Math.floor(t) % m;
    const j = (i + 1) % m;
    const u = t - Math.floor(t);
    out[3 * k] = raw[3 * i] + u * (raw[3 * j] - raw[3 * i]);
    out[3 * k + 1] = raw[3 * i + 1] + u * (raw[3 * j + 1] - raw[3 * i + 1]);
    out[3 * k + 2] = raw[3 * i + 2] + u * (raw[3 * j + 2] - raw[3 * i + 2]);
  }
  return out;
}

const sampled = sampleXyzComponent(single.entry.components[0], 8, resampleClosedCurve);
assert(sampled.length === 24, 'sampleXyzComponent resamples to N=8');

if (failed) {
  console.error(`\n${failed} test(s) failed`);
  process.exit(1);
}
console.log('\nAll xyz-import tests passed');
