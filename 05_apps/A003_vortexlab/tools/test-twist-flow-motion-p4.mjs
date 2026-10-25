import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {createHash} from 'node:crypto';
const read = p=>fs.readFileSync(p,'utf8');
const runtime=read('apps/web/src/legacy/vortexlab-runtime.js');
const gui=read('apps/web/twist-flow/twist-flow.js');
const ui=read('apps/web/twist-flow/index.html');
const original=JSON.parse(read('reference/source-hashes.json'));
let pass=0;
function test(label,fn){fn();pass++;console.log('PASS',label);}
test('source integrity: P2 runtime parent remains frozen',()=>{
 assert.equal(original.patch.twistFlowP4ParentRuntimeSha256,'72845be8e6fc527982f0eb504349429b2a696e7b51490e53d4fcdab89f667088');
 assert.equal(original.extractedRuntimeSha256,createHash('sha256').update(runtime).digest('hex'));
});
test('dedicated route opts in; full VortexLab leaves overlay disabled',()=>{
 assert.match(gui,/window\.__vlTwistFlowOverlayParticles=true/);
 assert.match(runtime,/window\.__vlTwistFlowOverlayParticles===true/);
 assert.doesNotMatch(read('apps/web/index.html'),/__vlTwistFlowOverlayParticles/);
});
test('shared engine supports simultaneous tracer geometry and streamlines',()=>{
 assert.match(runtime,/trPts\.visible=P\.showTracers&&\(!P\.showStreamlines\|\|window\.__vlTwistFlowOverlayParticles===true\)/);
 assert.match(runtime,/if\(!P\.showTracers\|\|\(P\.showStreamlines&&window\.__vlTwistFlowOverlayParticles!==true\)\|\|!Y\|\|!fils\.length\|\|dtSim===0\)return/);
 assert.match(gui,/checkbox\('cTracers',which!=='displayKnot'\)/);
 assert.match(gui,/checkbox\('cStreamlines',which==='displayStreamlines'\)/);
});
test('actual legacy tracer step returns early WITHOUT opt-in but not WITH opt-in',()=>{
 const start=runtime.indexOf('function stepTracers(dtSim){');
 const end=runtime.indexOf('  const n=tracerCount();',start);
 assert(start>=0&&end>start);
 const snippet=runtime.slice(start,end)+'  return "steps-may-advance";\n}';
 const run=(overlay)=>{
   const c={trPts:{visible:false},P:{showTracers:true,showStreamlines:true},
     window:{__vlTwistFlowOverlayParticles:overlay},Y:new Float64Array([0,1,2]),fils:[{N:4}],};
   vm.createContext(c);
   vm.runInContext(snippet,c);
   const value=vm.runInContext('stepTracers(0.05)',c);
   return {value,visible:c.trPts.visible};
 };
 assert.equal(run(false).value,undefined);
 assert.equal(run(false).visible,false);
 assert.equal(run(true).value,'steps-may-advance');
 assert.equal(run(true).visible,true);
});
test('accepted-step diagnostic increments ONLY after accepted transport',()=>{
 assert.match(runtime,/twistFlowAcceptedSteps\+\+;\s*ModelLog\.logStep/);
 assert.match(runtime,/window\.__vlTwistFlowDiagnostics=\(\)=>\(\{/);
 assert.match(runtime,/paused:!!paused, halted:!!flagged/);
 assert.match(runtime,/timeSeconds:Number\(tPhys\), acceptedSteps:twistFlowAcceptedSteps/);
 assert.match(gui,/VEILIGHEIDSSTOP/);
 assert.match(gui,/Geen geaccepteerde tijdstappen in 3 s/);
});
test('no faked motion: UI changes acceleration and demo Gamma through existing controls',()=>{
 assert.match(gui,/dispatch\('sAcc',Number\(e\.target\.value\),'input'\)/);
 assert.match(gui,/chooseSegment\('medSeg','med',demo\?'demo':'sst'\)/);
 assert.match(gui,/dispatch\('sGa',gamma\*1000,'input'\)/);
 assert.match(gui,/chooseSegment\('interSeg','inter','lia'\)/);
 assert.doesNotMatch(gui,/requestAnimationFrame\(\s*\(\)\s*=>\s*.*pos/);
});
test('all new controls exist, and user sees physical-vs-demo distinction',()=>{
 for(const id of ['motionMedium','demoGamma','playbackSpeed','motionDiagnostics','runMotionDemo'])
   assert(ui.includes(`id="${id}"`),id+' missing');
 assert.match(ui,/niet SST-gevalideerd/);
 assert.match(ui,/Stroomlijnen zijn instantane veldlijnen/);
});
test('unchanged solver law remains structurally present',()=>{
 for(const name of ['function velocityCore(','function dtCFL(){','function rk4Step(','function contactEvent('])
   assert(runtime.includes(name),name+' missing');
});
console.log(`PASS Twist Flow P4: ${pass} additional motion/diagnostic tests`);
