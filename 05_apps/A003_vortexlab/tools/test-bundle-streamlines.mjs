import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {createHash} from 'node:crypto';

const runtime=fs.readFileSync('apps/web/src/legacy/vortexlab-runtime.js','utf8');
const gui=fs.readFileSync('apps/web/twist-flow/twist-flow.js','utf8');
const html=fs.readFileSync('apps/web/twist-flow/index.html','utf8');
let pass=0;
function test(label,fn){fn();pass++;console.log('PASS',label);}

test('runtime exposes bundle-relative streamline velocity helper',()=>{
  assert.match(runtime,/function streamlineVelocityAt\(/);
  assert.match(runtime,/bundleVelocityProfileAt\(px,py,pz,true\)/);
  assert.match(runtime,/function traceStreamline\([\s\S]*?streamlineVelocityAt\(/);
  assert.doesNotMatch(runtime,/function traceStreamline\([\s\S]*?const v1=fieldVelocityAt\(/);
});

test('bundle UI refresh forces streamlines after lattice rebuild',()=>{
  assert.match(runtime,/rebuildLattice\(\);rebuildStreamlines\(true\);syncBundleUi\(\);/);
  assert.match(runtime,/cBundleFlow[\s\S]*?rebuildStreamlines\(true\)/);
});

test('TwistFlow documents relative streamlines under parallel bundle',()=>{
  assert.match(html,/ten opzichte van[\s\S]*?continuumrotatie/);
  assert.match(gui,/Stroomlijnen: knoopperturbatie t\.o\.v\. opgelegde Ω×r/);
});

test('relative field subtracts only continuum profile (keeps BS+BEM)',()=>{
  const start=runtime.indexOf('function streamlineVelocityAt(px,py,pz,segs){');
  const end=runtime.indexOf('\n}',start);
  assert(start>=0&&end>start);
  const snippet=runtime.slice(start,end+2);
  const c={
    fieldVelocityAt:(x,y,z)=>({ux:3,uy:4,uz:5,speed:Math.hypot(3,4,5)}),
    bundleFlowActive:()=>true,
    bundleVelocityProfileAt:()=>({ux:1,uy:2,uz:0}),
  };
  vm.createContext(c);
  vm.runInContext(snippet,c);
  const v=vm.runInContext('streamlineVelocityAt(0.1,0,0,[])',c);
  assert.equal(v.ux,2);
  assert.equal(v.uy,2);
  assert.equal(v.uz,5);
  assert.ok(Math.abs(v.speed-Math.hypot(2,2,5))<1e-12);
});

test('without bundle flow, streamline velocity equals lab field',()=>{
  const start=runtime.indexOf('function streamlineVelocityAt(px,py,pz,segs){');
  const end=runtime.indexOf('\n}',start);
  const snippet=runtime.slice(start,end+2);
  const lab={ux:0.5,uy:-0.25,uz:0.1,speed:Math.hypot(0.5,0.25,0.1)};
  const c={
    fieldVelocityAt:()=>lab,
    bundleFlowActive:()=>false,
    bundleVelocityProfileAt:()=>{throw new Error('profile must not run when bundle off');},
  };
  vm.createContext(c);
  vm.runInContext(snippet,c);
  const v=vm.runInContext('streamlineVelocityAt(0,0,0,[])',c);
  assert.equal(v,lab);
});

test('runtime sha256 is tracked for verify-parity',()=>{
  const digest=createHash('sha256').update(runtime).digest('hex');
  assert.match(digest,/^[0-9a-f]{64}$/);
  console.log('INFO runtime sha256',digest);
});

console.log(`PASS bundle streamlines: ${pass} checks`);
