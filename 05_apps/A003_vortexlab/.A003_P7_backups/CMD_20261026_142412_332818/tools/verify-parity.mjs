import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';

const manifest = JSON.parse(await readFile('reference/source-hashes.json', 'utf8'));
const sha = data => createHash('sha256').update(data).digest('hex');
const checks = [
  ['runtime', 'apps/web/src/legacy/vortexlab-runtime.js', manifest.extractedRuntimeSha256],
  ['native-policy', 'apps/web/src/legacy/native-resolution-policy.js', manifest.patch?.nativeResolutionPolicySha256],
  ...(manifest.patch?.fluidQualificationSha256 ? [['fluid-qualification', 'apps/web/src/legacy/fluid-qualification.js', manifest.patch.fluidQualificationSha256]] : []),
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
if (manifest.patch?.id === 'native-xyz-resolution-tracer-budget-p1') {
  if (manifest.inlineRuntimeSha256 !== manifest.patch.baseRuntimeSha256 ||
      manifest.extractedRuntimeSha256 !== manifest.patch.patchedRuntimeSha256) {
    console.error('FAIL baseline provenance or patched runtime manifest mismatch'); failed = true;
  } else console.log('PASS M1 baseline preserved; patched runtime explicitly versioned');
} else if (manifest.patch?.id === 'fluid-qualification-extreme-core-safety-p2') {
  if (manifest.inlineRuntimeSha256 !== manifest.patch.originalP1BaseRuntimeSha256 ||
      manifest.extractedRuntimeSha256 !== manifest.patch.patchedRuntimeSha256 ||
      !manifest.patch.parentRuntimeSha256) {
    console.error('FAIL P2 source-provenance chain'); failed = true;
  } else console.log('PASS P2 source-provenance chain: original -> P1 -> P2 (P1 parent digest recorded)');
} else if (manifest.patch?.id === 'twist-flow-p4-motion-and-observability') {
  const p=manifest.patch;
  if (p.twistFlowP4ParentRuntimeSha256 !== '72845be8e6fc527982f0eb504349429b2a696e7b51490e53d4fcdab89f667088' ||
      manifest.extractedRuntimeSha256 !== p.patchedRuntimeSha256 ||
      p.parentPatchId !== 'fluid-qualification-extreme-core-safety-p2' ||
      !p.physicsKernelsUntouched || !p.legacyDefaultPreserved) {
    console.error('FAIL Twist Flow P4 versioned runtime and P2 provenance chain'); failed = true;
  } else console.log('PASS Twist Flow P4 versioned additive visual adapter; P2 provenance retained');
} else if (manifest.patch?.id === 'sstcore-native-accel-on-twistflow-p4') {
  const p = manifest.patch;
  if (manifest.inlineRuntimeSha256 !== p.originalP1BaseRuntimeSha256 ||
      manifest.extractedRuntimeSha256 !== p.patchedRuntimeSha256 ||
      p.parentPatchId !== 'twist-flow-p4-motion-and-observability' ||
      !p.parentRuntimeSha256 ||
      !p.twistFlowP4Preserved ||
      !p.physicsKernelsUntouchedExceptOptInNative) {
    console.error('FAIL combined Twist Flow P4 + SSTcore native-accel provenance'); failed = true;
  } else console.log('PASS combined Twist Flow P4 + SSTcore native-accel (JS fallback + opt-in native)');
} else if (manifest.patch?.id === 'twist-flow-p5-adaptive-cfl-precision-gate') {
  const p = manifest.patch;
  if (p.parentPatchId !== 'twist-flow-p4-motion-and-observability' ||
      p.p4RuntimeSha256 !== '13ccbb662a537c712610cc168d3903da64086af95e00dbebdcb31cb7404aa28b' ||
      p.p4FluidQualificationSha256 !== '4abcd1cafadbfa7b690deb06b96fac6b7623f8f2da9ac857f4c916554e40e907' ||
      !p.physicsKernelsUntouched ||
      manifest.extractedRuntimeSha256 !== p.patchedRuntimeSha256) {
    console.error('FAIL P5 source provenance or physics kernel preservation'); failed = true;
  } else console.log('PASS P5 source chain P4 -> P5 verified; physics kernel unchanged');
} else if (manifest.patch?.id === 'sstcore-native-accel-on-twistflow-p5') {
  const p = manifest.patch;
  if (manifest.inlineRuntimeSha256 !== p.originalP1BaseRuntimeSha256 ||
      manifest.extractedRuntimeSha256 !== p.patchedRuntimeSha256 ||
      p.parentPatchId !== 'twist-flow-p5-adaptive-cfl-precision-gate' ||
      p.p5RuntimeSha256 !== '2fde1306dd43675babc747c90a0feee133c66987d1d6681cbf701c8af56b30a7' ||
      p.fluidQualificationSha256 !== '313ed51a9b6fe95756c121f81b568e1f27d8a47876ffb6087ffae664e8e2ceb1' ||
      !p.twistFlowP5Preserved ||
      !p.physicsKernelsUntouchedExceptOptInNative ||
      !p.localCatalogPreserved) {
    console.error('FAIL combined P5 + SSTcore native-accel provenance'); failed = true;
  } else console.log('PASS combined Twist Flow P5 CFL/motion + SSTcore native-accel (catalog preserved)');
} else if (manifest.patch?.id === 'tube-probe-motion-p6') {
  const p = manifest.patch;
  if (manifest.inlineRuntimeSha256 !== p.originalP1BaseRuntimeSha256 ||
      manifest.extractedRuntimeSha256 !== p.patchedRuntimeSha256 ||
      !p.parentRuntimeSha256 ||
      p.fluidQualificationSha256 !== '313ed51a9b6fe95756c121f81b568e1f27d8a47876ffb6087ffae664e8e2ceb1' ||
      !p.localCatalogPreserved ||
      !p.twistFlowP5Preserved) {
    console.error('FAIL P6 tube/probe/motion provenance'); failed = true;
  } else console.log('PASS P6 tube thickness + a_probe UX + Twist Flow interactive motion');
} else if (manifest.inlineRuntimeSha256 !== manifest.extractedRuntimeSha256) {
  console.error('FAIL extracted runtime differs from original inline runtime'); failed = true;
}
if (manifest.inlineCssSha256 !== manifest.extractedCssSha256) {
  console.error('FAIL extracted CSS differs from original inline CSS'); failed = true;
}
process.exitCode = failed ? 1 : 0;
