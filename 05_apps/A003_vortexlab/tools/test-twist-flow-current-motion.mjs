import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createRequire} from 'node:module';
import vm from 'node:vm';
const require=createRequire(import.meta.url);
const q=require('../apps/web/src/legacy/fluid-qualification.js');
const ui=fs.readFileSync('apps/web/twist-flow/twist-flow.js','utf8');
const runtime=fs.readFileSync('apps/web/src/legacy/vortexlab-runtime.js','utf8');
const html=fs.readFileSync('apps/web/twist-flow/index.html','utf8');
let n=0;const test=(name,fn)=>{fn();console.log('PASS',name);n++;};
test('reported dt=1.9034355272012943e-7 is accepted unchanged',()=>{
  const v=1.9034355272012943e-7, ans=q.safeStep(v,{simTime:0});
  assert.equal(ans.ok,true);assert.equal(ans.dt,v);
});
test('very small but clock-representable dt works without raising dt',()=>{
  const a=q.safeStep(1e-18,{simTime:0}),b=q.safeStep(1e-18,{simTime:1});
  assert.equal(a.ok,true);assert.equal(b.ok,false);
});
test('all source families available only through original engine selectors',()=>{
  for(const x of ['twistSelect','knotplotSelect','knotSelect'])assert.ok(ui.includes(x),x);
  assert.match(ui,/KNOTPLOT RELAXED KNOT CANDIDATES/);
  assert.match(ui,/GILBERT IDEAL/);
  assert.match(ui,/const sourceSelector=\{twist:/);
  assert.match(html,/KnotPlot of ideal-catalogus/);
});
test('UI excludes explicit link groups',()=>{
  assert.ok(ui.includes('GILBERT IDEAL')); 
  assert.match(ui,/RELAXED KNOT CANDIDATES/);
  assert.doesNotMatch(ui,/RELAXED LINK CANDIDATES/);
});
test('observation is after RK4 and contact rollback, before accepted time update',()=>{
  const i=runtime.indexOf('twistFlowLastStepDisplacement=Math.hypot(');
  assert(i>runtime.indexOf('function loop(now)'));
  assert(i<runtime.indexOf('tPhys+=dtApplied;',i));
  assert.match(runtime,/maxStateDisplacement\(Ypre,Y\)/);
  assert.match(runtime,/twistFlowReferenceTravel\+=twistFlowLastStepDisplacement/);
});
test('reset clears motion accumulators',()=>{
  for(const word of ['twistFlowReferenceTravel=0','twistFlowLastStepDisplacement=0','twistFlowLastStepMaxDisplacement=0'])
    assert.ok(runtime.includes(word),word);
});
test('genuine runtime diagnostics exposed, without fake renderer displacement',()=>{
  for(const key of ['referenceTravelMeters','referenceNetDisplacementMeters','lastStepMaximumDisplacementMeters','effectivePlaybackSpeed'])
    assert.ok(runtime.includes(key),key);
  assert.match(ui,/Punt 0 afgelegd/);
  assert.match(ui,/simulatietempo/);
  assert.doesNotMatch(ui,/requestAnimationFrame\(\s*\(\)\s*=>\s*.*pos/);
});
test('CFL fixed 1us gate is removed and contact rollback preserved',()=>{
  assert.doesNotMatch(runtime,/niet ondersteund \(<1e-6 s/);
  assert.match(runtime,/transientContactWithinStep/);
  assert.match(runtime,/Y\.set\(Ypre\)/);
});
test('no double engine created',()=>{
  assert.match(ui,/const sourceUrl=new URL\('\.\.\/index\.html'/);
  assert.doesNotMatch(html,/<iframe/i);
});
test('explicit reduced-N preview leaves source geometry and root lab unmodified',()=>{
  assert.match(runtime,/window\.__vlTwistFlowOverlayParticles===true&&\[96,192,288,512\]\.includes\(previewN\)/);
  assert.match(runtime,/Knoopklasse bij resampling NIET gecertificeerd/);
  assert.match(ui,/window\.__vlTwistFlowPreviewN=activate\?192:0/);
  assert.match(ui,/click\('bReset'\)/);
  assert.match(ui,/\$\('runMotionDemo'\)\.click\(\)/);
  assert.ok(html.includes('id="fastPreview"'));
});
test('actual native/preview sampling resolves N from original and explicit demo',()=>{
  const lo=runtime.indexOf('function sampledComponentN(');
  const hi=runtime.indexOf('function updateNativeResolutionUi(){',lo);
  assert(lo>0&&hi>lo);
  const ctx={proxyDecompResolutionOverride:0,
    window:{__vlTwistFlowOverlayParticles:true,__vlTwistFlowPreviewN:0,
      VortexLabResolutionPolicy:{nativeComponentPoints:()=>1024}},
    P:{knotSource:'twist'},Number};
  vm.createContext(ctx);vm.runInContext(runtime.slice(lo,hi),ctx);
  assert.equal(vm.runInContext('sampledComponentN({}, {}, 0, 288)',ctx),1024);
  ctx.window.__vlTwistFlowPreviewN=192;
  assert.equal(vm.runInContext('sampledComponentN({}, {}, 0, 288)',ctx),192);
  ctx.window.__vlTwistFlowOverlayParticles=false;
  assert.equal(vm.runInContext('sampledComponentN({}, {}, 0, 288)',ctx),1024);
  ctx.window.__vlTwistFlowOverlayParticles=true;
  ctx.proxyDecompResolutionOverride=512;
  assert.equal(vm.runInContext('sampledComponentN({}, {}, 0, 512)',ctx),512);
});
console.log('PASS user-upload motion/CFL: '+n+' checks');
