/* P2 field, extreme-core and runtime-wiring qualifications. No claims of Euler closure. */
import {createRequire} from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import vm from 'node:vm';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(import.meta.url);
const q=require(path.join(root,'apps/web/src/legacy/fluid-qualification.js'));
let count=0;
function check(label,condition){if(!condition)throw Error('FAIL '+label);count++;console.log('PASS',label);}
let extreme=q.classifyCore({a:1e-18,geometryScale:0.5,minimumEdge:0.0004});
check('1e-18 m accepted exactly, without silent clipping',extreme.a===1e-18&&extreme.inputValid);
check('sub-ULP contact at macroscopic scale is reported',extreme.regime==='SUB_PRECISION_CORE'&&!extreme.coreContactResolvable);
check('geometrical precision floor is explicit',Math.abs(extreme.precisionFloor-64*Number.EPSILON*0.5)<1e-30);
check('topological threshold is not falsely resolved',extreme.effectiveContactThreshold>extreme.physicalContactThreshold);
let candidate=q.classifyCore({a:1e-5,geometryScale:0.5,minimumEdge:0.0004});
check('well-separated thin filament remains candidate, not physical certification',candidate.regime==='CANDIDATE_ONLY'&&candidate.status==='NUMERICAL_QUALIFICATION_ONLY');
check('marginal discretization is disqualified',q.classifyCore({a:0.001,geometryScale:0.5,minimumEdge:0.001}).regime==='THIN_FILAMENT_UNQUALIFIED');
check('zero/NaN cores rejected',q.classifyCore({a:0,geometryScale:1,minimumEdge:1}).regime==='INVALID_CORE'&&!q.classifyCore({a:NaN,geometryScale:1,minimumEdge:1}).inputValid);
check('physical core is independent metadata',q.classifyCore({a:1e-4,geometryScale:0.5,minimumEdge:0.001,physicalRadius:1e-18}).physicalRadius===1e-18);
check('positive sub-microsecond CFL step is accepted without rounding',q.safeStep(1.9034355272012943e-7).ok&&q.safeStep(1.9034355272012943e-7).dt===1.9034355272012943e-7&&q.safeStep(1e-6).ok&&!q.safeStep(NaN).ok);
check('finite-state gate rejects invalid intermediate vector',q.allFinitePositions(new Float64Array([0,1,2]))&&!q.allFinitePositions([0,Infinity,1]));
const f=(x,y,z)=>({ux:x,uy:-y,uz:0}); // exactly divergence-free but nonzero wall flux
const d=q.divergenceDiagnostic(f,{x:.11,y:.04,z:.08,h:1e-5});
check('passive divergence diagnostic',d.valid&&Math.abs(d.value)<1e-10);
const w=q.wallNormalDiagnostic(f,{radius:0.25,halfHeight:0.5});
check('divergence-free flow still violates cylinder impermeability',w.valid&&w.samples===16&&w.maxAbsNormal>0.2&&!w.qualified);
check('no false Euler pressure/wall closure',extreme.pressureClosure==='NOT_IMPLEMENTED'&&extreme.wallClosure==='NOT_IMPLEMENTED');
const vol=q.coreVolumeDiagnostic({initialLength:1,currentLength:1.2,initialCoreRadius:1e-18});
check('uniform volume candidate has correct SI length dimension',vol.valid&&Math.abs(vol.proposedRadius/(1e-18)-1/Math.sqrt(1.2))<1e-13&&vol.status==='HYPOTHESIS_UNCOUPLED');
// Extract the actual runtime dtCFL function: a very high gamma and a=1e-18
// must generate dt below 1 microsecond, not falsely return 1 microsecond.
const runtime=fs.readFileSync(path.join(root,'apps/web/src/legacy/vortexlab-runtime.js'),'utf8');
const start=runtime.indexOf('function dtCFL(){'),end=runtime.indexOf('function evalsPerStep(){',start);
check('active runtime contains dynamic dtCFL',start>=0&&end>start);
const context={P:{stretchProfileApply:false,stretchProfileOnly:false,core:'vast',a:1e-18,Om:0,topologyGuard:false},
  Gamma:()=>1e9,lminAll:()=>1e-5,DELTA:{vast:0.25},C0:.1395,lastUmax:1e-9,
  prescribedKinematicSpeedBound:()=>0,stretchProfileCharacteristicRate:()=>0,bgWallInSolver:()=>false,
  bundleMaxOmega:()=>0,acceptedStepTimeCap:()=>0.25,Math,Number};
vm.createContext(context);vm.runInContext(runtime.slice(start,end),context);
const raw=vm.runInContext('dtCFL()',context);
check('actual runtime retains sub-microsecond dt',raw<1e-6&&raw>0);
check('actual sub-microsecond CFL remains accepted at t=0',q.safeStep(raw,{simTime:0}).ok);
check('actual runtime checks RK4-state finite before accepting candidate',runtime.includes('Y.set(Ypre);lastUmax=1e-9;stepDebt=0;'));
check('UI exposes dedicated numerical core state and wall warning',fs.readFileSync(path.join(root,'apps/web/index.html'),'utf8').includes('fluidCoreQualification')&&fs.readFileSync(path.join(root,'apps/web/index.html'),'utf8').includes('fluidFieldQualification'));
console.log(`${count} P2 fluid and 1e-18 m qualification tests PASS`);
