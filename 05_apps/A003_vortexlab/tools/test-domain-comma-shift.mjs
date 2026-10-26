import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(import.meta.url);
const q=require(path.join(root,'apps/web/src/legacy/fluid-qualification.js'));
const runtime=fs.readFileSync(path.join(root,'apps/web/src/legacy/vortexlab-runtime.js'),'utf8');
const html=fs.readFileSync(path.join(root,'apps/web/index.html'),'utf8');
let pass=0;
function test(label,fn){fn();pass++;console.log('PASS',label);}

test('UI exposes domain comma-shift control',()=>{
  assert.match(html,/id="bDomainCommaShift"/);
  assert.match(html,/Decimaalverschuiving domein/);
  assert.match(runtime,/function domainCommaShiftPlan\(/);
  assert.match(runtime,/function applyDomainCommaShift\(/);
  assert.match(runtime,/bDomainCommaShift/);
});

test('uniform length rescale leaves contact resolvability invariant',()=>{
  const a=1e-18,R=0.05,L=1e-12;
  const before=q.classifyCore({a,geometryScale:R,minimumEdge:1e-4});
  const after=q.classifyCore({a:a/L,geometryScale:R/L,minimumEdge:1e-4/L});
  assert.equal(before.coreContactResolvable,after.coreContactResolvable);
  assert.equal(before.regime,after.regime);
  assert.equal(before.coreContactResolvable,false);
});

test('shrinking domain at fixed a_sim can make 1e-18 contact resolvable',()=>{
  const a=1e-18;
  const macro=q.classifyCore({a,geometryScale:0.05,minimumEdge:1e-5});
  assert.equal(macro.regime,'SUB_PRECISION_CORE');
  const maxR=0.5*(3*a)/(64*Number.EPSILON);
  const micro=q.classifyCore({a,geometryScale:maxR,minimumEdge:maxR*1e-3});
  assert.equal(micro.coreContactResolvable,true);
  assert.notEqual(micro.regime,'SUB_PRECISION_CORE');
});

test('runtime plan factor matches 3a vs 64*eps*scale',()=>{
  const start=runtime.indexOf('function domainCommaShiftPlan(a=P.a){');
  const end=runtime.indexOf('\nfunction applyDomainCommaShift',start);
  assert(start>=0&&end>start);
  const snippet=runtime.slice(runtime.indexOf('function contactResolvableMaxGeometryScale'),end);
  const c={
    P:{a:1e-18},
    CONTACT_ULP_FACTOR:64,
    Number,
    geometryPrecisionScale:()=>0.05,
  };
  vm.createContext(c);
  vm.runInContext(snippet,c);
  const plan=vm.runInContext('domainCommaShiftPlan()',c);
  assert.equal(plan.needed,true);
  assert.ok(plan.factor>0&&plan.factor<1);
  const expect=0.5*(3e-18)/(64*Number.EPSILON)/0.05;
  assert.ok(Math.abs(plan.factor-expect)/expect<1e-12);
});

test('a_sim research floor remains 1e-18',()=>{
  assert.equal(q.A_SIM_RESEARCH_FLOOR,1e-18);
  assert.match(runtime,/A_SIM_INPUT_FLOOR=1e-18/);
});

console.log(`PASS domain comma-shift: ${pass} checks`);
