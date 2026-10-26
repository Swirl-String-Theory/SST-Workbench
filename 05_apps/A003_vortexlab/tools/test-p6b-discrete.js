'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'..','apps','web','src','legacy','discrete_bundle_kernel.js'),'utf8');
let sceneChildren=[];
const THREE={
 Group:class {constructor(){this.children=[];}add(o){this.children.push(o);}remove(o){this.children=this.children.filter(x=>x!==o);}},
 BufferGeometry:class {constructor(){this.attributes={};}setAttribute(k,v){this.attributes[k]=v;}dispose(){}},
 BufferAttribute:class {constructor(array){this.array=array;this.needsUpdate=false;}},
 LineBasicMaterial:class {dispose(){}},
 Line:class {constructor(g,m){this.geometry=g;this.material=m;}}
};
const NK=20,Y=new Float64Array(3*NK);
for(let j=0;j<NK;j++){
 const t=2*Math.PI*j/NK;
 Y[3*j]=0.085+0.015*Math.cos(t);
 Y[3*j+1]=0.012+0.015*Math.sin(t);
 Y[3*j+2]=0.025;
}
const fl=[{off:0,N:NK,carrier:'A'}];
const ctx={window:{__vlTwistFlowOverlayParticles:true},THREE,scene:{add:o=>sceneChildren.push(o)},P:{Hcyl:0.4,a:0.001},
 Y,fils:fl, K4:new Float64Array(Y.length),allFils:()=>fl,filamentGamma:()=>0.003,contactThresholdInfo:()=>({effective:0.003}),
 wrapFilamentCarriersZ:()=>{},enforceCenterLock:()=>{},constrainGhostRing:()=>{},
 maxStateDisplacement:(a,b)=>{let max=0;for(let i=0;i<a.length;i+=3)max=Math.max(max,Math.hypot(a[i]-b[i],a[i+1]-b[i+1],a[i+2]-b[i+2]));return max;},
 // Test contact in this harness uses the minimum endpoint distance lower bound;
 // production uses exact segment-to-segment distance from A003.
 segSegDist2:(...v)=>{let m=Infinity;for(const i of [0,3])for(const j of [6,9]){
   m=Math.min(m,(v[i]-v[j])**2+(v[i+1]-v[j+1])**2+(v[i+2]-v[j+2])**2);
 }return m;},
};
vm.createContext(ctx);vm.runInContext(source+'\n globalThis.vlDiscrete=vlDiscrete;',ctx,{filename:'discrete_addon.js'});
ctx.velAll=(pos,out)=>{out.fill(0);return ctx.vlDiscrete.knotDerivative(pos,fl,out);};
const api=ctx.window.__vlDiscreteBundleAPI;
let report=api.configure({mode:'discrete',omega:2,spacing:0.05,side:3,nodes:17});
assert.equal(report.filaments,9);assert.equal(report.vertices,153);
assert.ok(Math.abs(report.circulation-0.01)<1e-14);
assert.ok(Math.abs(report.omega-report.circulation/(2*report.spacing**2))<1e-13);
assert.ok(ctx.vlDiscrete.active());
assert.ok(ctx.vlDiscrete.isFinite());
const b0=ctx.vlDiscrete.fullSnapshot(),y0=Y.slice();
const uK=new Float64Array(Y.length),kSpeed=ctx.vlDiscrete.knotDerivative(Y,fl,uK);
assert.ok(kSpeed>1e-7,'nonzero background-induced knot velocity');
const flow=ctx.vlDiscrete.fieldVelocity(0.06,0.034,0.01);
assert.ok(Number.isFinite(flow.ux)&&Number.isFinite(flow.uy)&&Number.isFinite(flow.uz));
ctx.vlDiscrete.snapshot();
const stepSpeed=ctx.vlDiscrete.advance(1e-4);
assert.ok(stepSpeed>0&&Number.isFinite(stepSpeed));
assert.ok(ctx.vlDiscrete.isFinite());
const b1=ctx.vlDiscrete.fullSnapshot();
assert.ok(ctx.maxStateDisplacement(y0,Y)>0,'knot must react to background');
assert.ok(ctx.maxStateDisplacement(b0,b1)>0,'background must react to knot');
for(let i=0;i<9;i++)for(const k of [0,16]){
 let j=3*(i*17+k);assert.deepEqual(Array.from(b0.slice(j,j+3)),Array.from(b1.slice(j,j+3)),'endpoints pinned');
}
ctx.vlDiscrete.restore();
assert.deepEqual(Array.from(ctx.vlDiscrete.fullSnapshot()),Array.from(b0),'rollback restores background exactly');
assert.ok(ctx.vlDiscrete.minDistance(Y)>0);
assert.equal(ctx.vlDiscrete.contact(),null);
api.configure({mode:'discrete',omega:0,spacing:0.05,side:3,nodes:17});
assert.equal(ctx.vlDiscrete.active(),false,'zero circulation must be dynamically identical to absent bundle');
assert.equal(ctx.vlDiscrete.contact(),null,'zero circulation has no contact barrier');
const zFlow=ctx.vlDiscrete.fieldVelocity(0.02,0.03,0.04);
assert.ok(zFlow.ux===0&&zFlow.uy===0&&zFlow.uz===0,'zero background circulation produces zero additional knot/tracer flow');
api.configure({mode:'off'});
assert.equal(ctx.vlDiscrete.active(),false);
assert.equal(api.getSnapshot().vertices,0);
console.log('PASS P6b: Γ↔Ω conversion, two-way motion, zero-strength parity, finite state, pinned endpoints, rollback, off isolation.');
