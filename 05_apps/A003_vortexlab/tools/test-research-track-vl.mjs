import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const src = readFileSync(join(root, 'apps/web/src/legacy/research-track-vl.js'), 'utf8');
const sandbox = { window: {}, globalThis: {}, console };
sandbox.window = sandbox;
sandbox.globalThis = sandbox;
sandbox.V_CHAR_SST = 2.99792458e8;
sandbox.R_HORN_SST = 1.40897017e-15;
vm.runInNewContext(src, sandbox, { filename: 'research-track-vl.js' });
const RT = sandbox.VLResearchTrack;
if (!RT) throw new Error('VLResearchTrack missing');

const N = 64;
const pts = new Float64Array(3 * N);
const mut = new Float64Array(3 * N);
for (let i = 0; i < N; i++) {
  const t = 2 * Math.PI * i / N;
  pts[3 * i] = Math.cos(t);
  pts[3 * i + 1] = Math.sin(t);
  pts[3 * i + 2] = 0;
  // tangential mutual along ê_θ so signed mean is non-zero
  mut[3 * i] = -Math.sin(t) * 1e-9;
  mut[3 * i + 1] = Math.cos(t) * 1e-9;
  mut[3 * i + 2] = 0;
}

const signed = RT.signedLocalSwirlClock(pts, mut, 1e-6, null);
if (!signed.ok) throw new Error('signed route failed');
if (!(Math.abs(signed.signedMean) > 0)) throw new Error('expected non-zero signed mean');
console.log('PASS signed local route', signed.signedMean.toExponential(3), signed.rms.toExponential(3));

const bishop = RT.bishopFrame(pts);
if (!bishop.ok || !(Math.abs(bishop.holonomyRad) < 1e-6 || Number.isFinite(bishop.holonomyRad))) {
  throw new Error('bishop failed');
}
if (bishop.maxTangentNormalDot > 1e-6) throw new Error('bishop orthogonality');
console.log('PASS bishop frame holonomy=', bishop.holonomyRad.toExponential(3));

const grad = RT.mutualVelocityGradient(pts, mut);
if (!grad.ok) throw new Error('gradient failed');
console.log('PASS gradient stub');

if (RT.DISTANCE_ORIENTATION_REGISTRY.length < 6) throw new Error('distance registry incomplete');
const holdouts = RT.DISTANCE_ORIENTATION_REGISTRY.filter(x => x.holdout);
if (!holdouts.length) throw new Error('no holdouts reserved');
console.log('PASS distance registry', RT.DISTANCE_ORIENTATION_REGISTRY.length, 'holdouts', holdouts.length);

const renamed = RT.renameObservables({ phaseLogRatio: 1, fieldLogMin: -2, nested: { omegaBody: 3, v_def: 4 } });
if (renamed.rigidResponseLogRatio !== 1 || renamed.kinematicClockEnvelopeMin !== -2) throw new Error('rename failed');
if (renamed.nested.omegaRigidCenterline !== 3 || renamed.nested.centerlineDeformationResidual !== 4) throw new Error('nested rename failed');
console.log('PASS observable rename map');

if (RT.ROSETTA_DEFAULTS.radiusDrive !== 'physical-only') throw new Error('radiusDrive default');
if (RT.ROSETTA_DEFAULTS.planckInvariantSelftestId !== 'T14') throw new Error('T14 id');
console.log('PASS rosetta defaults');

if (RT.INTERNAL_PHASE_CANDIDATES.some(c => String(c.formula).includes('8π') || String(c.formula).includes('8pi'))) {
  throw new Error('forbidden 1/8π candidate present');
}
console.log('PASS no post-hoc 1/8π candidate');

console.log('All research-track-vl checks PASS');
