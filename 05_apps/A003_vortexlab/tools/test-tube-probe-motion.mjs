/**
 * Structural checks: tube thickness from a_sim/nQ/r_kern, passive a_probe UX,
 * Twist Flow interactive high-N policy (LIA+N192, no fake velocities).
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const runtime = fs.readFileSync('apps/web/src/legacy/vortexlab-runtime.js', 'utf8');
const html = fs.readFileSync('apps/web/index.html', 'utf8');
const twistUi = fs.readFileSync('apps/web/twist-flow/twist-flow.js', 'utf8');
let n = 0;
const test = (name, fn) => { fn(); console.log('PASS', name); n++; };

test('displayTubeRadii helper exists and ignores a_probe', () => {
  assert.match(runtime, /function displayTubeRadii\(\)\{/);
  assert.match(runtime, /a_probe never enters this path/);
  assert.match(runtime, /floorMeters=1e-5/);
  assert.doesNotMatch(runtime, /Math\.max\(P\.a,0\.00035\)/);
});

test('tubesWanted respects showTubeThickness or vis=tube', () => {
  assert.match(runtime, /function tubesWanted\(\)\{return P\.vis==='tube'\|\|!!P\.showTubeThickness;\}/);
  assert.match(runtime, /showTubeThickness:false/);
  assert.ok(html.includes('id="cShowTubeThickness"'));
  assert.ok(html.includes('id="tubeThicknessInfo"'));
});

test('rebuildTubes uses display radii and optional r_kern shell', () => {
  assert.match(runtime, /const radii=displayTubeRadii\(\)/);
  assert.match(runtime, /coreTubeObjs\.push\(new THREE\.Mesh\(new THREE\.TubeGeometry\(curve,f\.N,radii\.rKern/);
  assert.match(runtime, /updateTubeThicknessHud\(\)/);
});

test('nQ and r_kern rebuild tubes', () => {
  assert.match(runtime, /bindRange\('Nq'[\s\S]*?rebuildTubes\(true\)/);
  assert.match(runtime, /rCorePhysical[\s\S]*?rebuildTubes\(true\)/);
});

test('a_probe sync is focus-safe and status is visible', () => {
  assert.match(runtime, /syncInputUnlessEditing\(sp,fmtLengthSI\(P\.scaleProbe\)\)/);
  assert.match(runtime, /function updateScaleProbeStatus\(\)/);
  assert.ok(html.includes('id="scaleProbeStatus"'));
  assert.match(runtime, /a_probe=\$\{fmtLengthSI\(P\.scaleProbe\)\} \(passief · geen solver\)/);
  assert.match(runtime, /fluidCoreQualification[\s\S]*?core\.appendChild\(fluidQual\)/);
});

test('displayTubeRadii numeric behavior in isolation', () => {
  const start = runtime.indexOf('function displayTubeRadii(){');
  const end = runtime.indexOf('function tubesWanted(){', start);
  assert(start > 0 && end > start);
  const ctx = {
    P: { a: 1.5e-3, nQ: 10, rCorePhysical: null },
    Number,
    R_HORN_SST: 1.40897017e-15,
    resolvedFixedCoreRadius() {
      const r = Number(ctx.P.rCorePhysical);
      return Number.isFinite(r) && r > 0 && r < ctx.R_HORN_SST ? r : NaN;
    }
  };
  // Inject the real helper body but stub resolvedFixedCoreRadius in the slice.
  const body = runtime.slice(start, end).replace(
    /resolvedFixedCoreRadius\(\)/g,
    'resolvedFixedCoreRadius()'
  );
  vm.createContext(ctx);
  vm.runInContext(body, ctx);
  const r = vm.runInContext('displayTubeRadii()', ctx);
  assert.equal(r.aSim, 1.5e-3);
  assert.equal(r.aDisplay, 1.5e-3);
  assert.equal(r.floorActive, false);
  ctx.P.a = 1e-7;
  const tiny = vm.runInContext('displayTubeRadii()', ctx);
  assert.equal(tiny.floorActive, true);
  assert.equal(tiny.aDisplay, 1e-5);
  assert.equal(tiny.aSim, 1e-7);
  // r_kern must be < R_horn in the real gate; use a tiny research value.
  ctx.P.rCorePhysical = 1e-16;
  const withCore = vm.runInContext('displayTubeRadii()', ctx);
  assert.equal(withCore.rKern, 1e-16);
});

test('Twist Flow applies LIA+N192+demo-Γ policy for KnotPlot/A006 without faking velocity', () => {
  assert.match(twistUi, /function applyInteractiveMotionPolicy\(/);
  assert.match(twistUi, /function needsInteractiveDemoPath\(/);
  assert.match(twistUi, /family==='twist'\|\|family==='knotplot'/);
  assert.match(twistUi, /function applyDemoMediumForMotion\(/);
  assert.match(twistUi, /chooseSegment\('medSeg','med','demo'\)/);
  assert.match(twistUi, /__vlTwistFlowPreviewN=192/);
  assert.match(twistUi, /chooseSegment\('interSeg','inter','lia'\)/);
  assert.match(twistUi, /click\('bResetParticles'\)/);
  assert.match(twistUi, /checkbox\('cTracers',true\)/);
  assert.match(twistUi, /selectKnot[\s\S]*?applyInteractiveMotionPolicy\(value\)/);
  assert.doesNotMatch(twistUi, /velocity\s*\*=|Y\[i\]\s*\+=.*fake|lerp.*filament/i);
  assert.match(twistUi, /Kelvin-snelheid \(SST Γ\) is te klein/);
  assert.match(twistUi, /demo-Γ \(niet gecertificeerd\)/);
});

test('Twist Flow enables tube thickness checkbox by default on bootstrap', () => {
  assert.match(twistUi, /checkbox\('cShowTubeThickness',true\)/);
  assert.match(twistUi, /chooseSegment\('visSeg','vis','tube'\)/);
});

test('Runtime steps tracers once per frame over Σdt and exposes budget diagnostics', () => {
  assert.match(runtime, /function tracerEvalsEstimate\(\)/);
  assert.match(runtime, /let tracerDtAccum=0/);
  assert.match(runtime, /tracerDtAccum\+=dtApplied/);
  assert.match(runtime, /if\(tracerDtAccum!==0\)\{\s*stepTracers\(tracerDtAccum\)/);
  assert.match(runtime, /evals\+=tracerEvalsEstimate\(\)/);
  assert.match(runtime, /evalsPerStep:Number\(evalsPerStep\(\)\)/);
  assert.match(runtime, /stepsPerFrameEstimate:/);
  assert.match(runtime, /full Biot–Savart op deze N overschrijdt het framebudget/);
  // Per-step tracer integration removed from the CFL body (only Σdt after the loop).
  assert.doesNotMatch(runtime, /updateSpecClockAcceptedStep\(dtApplied,K4\);\s*\/\/ v7\.2[\s\S]*?stepTracers\(dtApplied\)/);
});

console.log(`PASS tube/probe/motion: ${n} checks`);
