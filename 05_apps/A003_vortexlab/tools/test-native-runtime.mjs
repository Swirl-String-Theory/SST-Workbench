/* Structural integration of the *actual runtime functions* in a DOM-free VM context.
   This validates the path from XYZ/A006 counts through topologyRawComponents to
   makeCarrierComponents, without requiring WebGL or a browser. */
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';
const require=createRequire(import.meta.url),root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const policy=require(path.join(root,'apps/web/src/legacy/native-resolution-policy.js'));
const xyz=require(path.join(root,'apps/web/src/legacy/xyz-import.js'));
const runtime=readFileSync(path.join(root,'apps/web/src/legacy/vortexlab-runtime.js'),'utf8');
function section(begin,end){let i=runtime.indexOf(begin),j=runtime.indexOf(end,i+begin.length);if(i<0||j<0)throw Error(`missing source section: ${begin} ... ${end}`);return runtime.slice(i,j);}
function equal(actual,expected,desc){if(JSON.stringify(actual)!==JSON.stringify(expected))throw Error(`${desc}: ${JSON.stringify(actual)} instead of ${JSON.stringify(expected)}`);console.log('PASS',desc);}
function ring(n,z=0){return Array.from({length:n},(_,i)=>{const t=i*2*Math.PI/n;return `${Math.cos(t)} ${Math.sin(t)} ${z}`;}).join('\n');}
const parsed=xyz.parseXyzText(ring(512)+'\n\n'+ring(1024,0.3),'link-N512-N1024.xyz');
if(!parsed.ok)throw Error(parsed.error);
const P={mode:'solo',knotSource:'xyz',qual:'laag',R0:0.07,compA:1,compB:1,idealComponentMode:'all',mirrorB:false};
const context={P,window:{VortexLabResolutionPolicy:policy,VortexLabXyzImport:xyz},proxyDecompResolutionOverride:0,
  activeKnotEntry:()=>parsed.entry,knotEntryComponents:e=>e.components,isRingTopo:()=>false,
  QUAL_N:{solo:{laag:96,mid:192,hoog:288},botsing:{laag:64,mid:96,hoog:128}},RING_QUAL:{laag:48,mid:96,hoog:144},
  sampleFourierParametric:(_coeffs,n)=>new Float64Array(n*3),sampleIdealComponent:(_c,n)=>new Float64Array(n*3),
  sampleKnotPlotComponent:(_e,_c,n)=>new Float64Array(n*3),
  resampleClosedCurve:(_raw,n)=>new Float64Array(n*3),
  finiteMetaNumber:v=>Number.isFinite(Number(v))?Number(v):NaN,
  topologyComponentCount:()=>1,sampleBuiltinRaw:(_t,n)=>new Float64Array(n*3),sampleFourierKnot:(_c,n)=>new Float64Array(n*3),
  carrierMeanSelfVz:()=>1};
const snippets=[
  ['function nativeSourcePointCounts(){','function carrierN(){'],
  ['function carrierN(){','function sampledComponentN('],
  ['function sampledComponentN(','function updateNativeResolutionUi(){'],
  ['function sampleCatalogComponent(','function sampleBuiltinRaw('],
  ['function topologyRawComponents(','function reverseTraversal('],
  ['function reverseTraversal(','function signedAreaXY('],
  ['function signedAreaXY(','function makeCarrierComponents('],
  ['function makeCarrierComponents(','// ================= fysica:']
].map(([a,b])=>section(a,b)).join('\n');
vm.createContext(context);
vm.runInContext(snippets,context,{timeout:4000});
equal(vm.runInContext('nativeSourcePointCounts()',context),[512,1024],'per-component XYZ source N');
equal(vm.runInContext('carrierN()',context),1024,'carrierN reports native maximum');
equal(vm.runInContext('topologyRawComponents(carrierN(),"A").map(c=>c.length/3)',context),[512,1024],'topology uses native separate N');
equal(vm.runInContext('makeCarrierComponents(carrierN(),0,0,1,"A").map(c=>c.length/3)',context),[512,1024],'real geometry placement preserves unequal component counts');
context.proxyDecompResolutionOverride=256;P.mode='botsing';
equal(vm.runInContext('carrierN()',context),256,'benchmark explicit N override preserved');
equal(vm.runInContext('topologyRawComponents(carrierN(),"A").map(c=>c.length/3)',context),[256,256],'benchmark override stays uniform by design');
context.proxyDecompResolutionOverride=0;P.mode='solo';P.knotSource='twist';
context.activeKnotEntry=()=>({components:[{I:1,pointCount:1024,coeffs:[{I:0,A:[0,0,0],B:[0,0,0]}]}],pointsPerComponent:[1024]});
equal(vm.runInContext('topologyRawComponents(carrierN(),"A").map(c=>c.length/3)',context),[1024],'A006 converted XYZ uses native N1024');
console.log('7 runtime native-N structural checks PASS');
