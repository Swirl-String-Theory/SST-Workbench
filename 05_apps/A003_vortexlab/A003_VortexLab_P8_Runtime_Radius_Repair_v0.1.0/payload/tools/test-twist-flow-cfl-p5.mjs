import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const q=require('../apps/web/src/legacy/fluid-qualification.js');
const source=fs.readFileSync('apps/web/src/legacy/vortexlab-runtime.js','utf8');
const ui=fs.readFileSync('apps/web/twist-flow/twist-flow.js','utf8');
let count=0;
const check=(name,fn)=>{fn();count++;console.log('PASS',name);};
check('user-reported 190 ns CFL step is allowed EXACTLY',()=>{
  const dt=1.9034355272012943e-7, p=q.safeStep(dt,{simTime:0});
  assert.equal(p.ok,true);assert.equal(p.dt,dt);assert.equal(p.nextTime,dt);
});
check('no unsupported hardcoded dt threshold in active gate',()=>{
  assert.doesNotMatch(source,/dtNext.*>=\s*1e-6|dtNext.*<\s*1e-6/);
  assert.match(source,/safeStep\(value,\s*\n\s*\{simTime:tPhys,direction:timeDir\}/);
  assert.doesNotMatch(source,/niet ondersteund \(<1e-6 s/);
});
check('extreme 1e-18 second is representable at startup',()=>{
  const p=q.safeStep(1e-18,{simTime:0});assert.equal(p.ok,true);
});
check('loss of time progress is rejected at large elapsed time',()=>{
  const p=q.safeStep(1e-18,{simTime:1});assert.equal(p.ok,false);
  assert.equal(p.reason,'TIME_RESOLUTION_EXHAUSTED');
});
check('invalid steps are refused rather than rounded',()=>{
  for(const x of [NaN,Infinity,-Infinity,-1,0])assert.equal(q.safeStep(x).ok,false);
});
check('reverse-time progress is checked symmetrically',()=>{
  assert.equal(q.safeStep(1e-7,{simTime:100,direction:-1}).ok,true);
  assert.equal(q.safeStep(1e-18,{simTime:100,direction:-1}).ok,false);
});
check('actual active dtCFL numerical value is not rounded',()=>{
  const start=source.indexOf('function dtCFL(){'),end=source.indexOf('function evalsPerStep(){',start);
  assert(start>=0&&end>start);
  const context={P:{stretchProfileApply:false,stretchProfileOnly:false,core:'vast',a:1e-18,Om:0,topologyGuard:false},
    vlDiscrete:{active:()=>false},
    Gamma:()=>1e9,lminAll:()=>1e-5,DELTA:{vast:0.25},C0:0.1395,lastUmax:1e-9,
    prescribedKinematicSpeedBound:()=>0,stretchProfileCharacteristicRate:()=>0,bgWallInSolver:()=>false,
    bundleMaxOmega:()=>0,acceptedStepTimeCap:()=>0.25,Math,Number};
  vm.createContext(context);vm.runInContext(source.slice(start,end),context);
  const dt=vm.runInContext('dtCFL()',context);
  assert(dt>0&&dt<1e-6);assert(q.safeStep(dt,{simTime:0}).ok);
});
check('RK4 finite state and topology guards retained',()=>{
  assert.match(source,/allFinitePositions\(Y\)/);
  assert.match(source,/transientContactWithinStep/);
  assert.match(source,/contactEvent\(lia\)/);
  assert.match(source,/Y\.set\(Ypre\)/);
});
check('UI warns about submicro time-step throughput, without fake motion',()=>{
  assert.match(ui,/MICROSTAP TOEGESTAAN/);
  assert.match(ui,/1\/dt/);
  assert.match(ui,/Geaccepteerde stappen/);
});
console.log(`PASS P5 adaptive-CFL: ${count} additional checks`);
