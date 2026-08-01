import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';

const manifest = JSON.parse(await readFile('reference/source-hashes.json', 'utf8'));
const sha = data => createHash('sha256').update(data).digest('hex');
const checks = [
  ['runtime', 'apps/web/src/legacy/vortexlab-runtime.js', manifest.extractedRuntimeSha256],
  ['css', 'apps/web/styles/vortexlab.css', manifest.extractedCssSha256],
  ...Object.entries(manifest.catalogs).map(([name, expected]) => [`catalog:${name}`, `apps/web/data/${name}`, expected]),
  ...Object.entries(manifest.vendors).map(([name, expected]) => [`vendor:${name}`, `apps/web/vendor/${name}`, expected])
];
let failed = false;
for (const [label, path, expected] of checks) {
  const actual = sha(await readFile(path));
  const ok = actual === expected;
  console.log(`${ok ? 'PASS' : 'FAIL'} ${label} ${actual}`);
  failed ||= !ok;
}
if (manifest.inlineRuntimeSha256 !== manifest.extractedRuntimeSha256) {
  console.error('FAIL extracted runtime differs from original inline runtime'); failed = true;
}
if (manifest.inlineCssSha256 !== manifest.extractedCssSha256) {
  console.error('FAIL extracted CSS differs from original inline CSS'); failed = true;
}
process.exitCode = failed ? 1 : 0;
