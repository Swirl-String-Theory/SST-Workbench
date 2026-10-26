import assert from 'node:assert/strict';
import vm from 'node:vm';
import {createRequire} from 'node:module';
import {readFileSync} from 'node:fs';
const req=createRequire(import.meta.url);
const model=req('../apps/web/src/legacy/model-a-ideal-stretch.js');
const meta={ideal:true,L:16.371637,D:1,knotId:'3:1:1',componentCount:1};
const poly=new Float64Array([1,0,0, 0,1,0, -1,0,0, 0,-1,0]);
const near=(x,y)=>assert(Math.abs(x-y)<1e-11*Math.max(Math.abs(y),1e-300),`${x} != ${y}`);
let checks=0;const check=(name,fn)=>{fn();checks++;console.log('PASS',name);};
check('ideal rope diameter equals polygon length divided by 16.371637',()=>{
  const s=model.reset({points:poly,source:'ideal',metadata:meta});
  const p=model.tubeProfile(poly,4);
  near(p.referenceDiameterScene,s.simReferenceLengthMeters/meta.L);
  near(p.diameterSceneMean,p.referenceDiameterScene);
  p.radiiScene.forEach(x=>near(2*x,p.referenceDiameterScene));
});
check('local radius shrinks as sqrt of accepted segment stretch',()=>{
  const initial=model.tubeProfile(poly,4).referenceDiameterScene;
  const stretched=poly.map(x=>x*2);
  model.observe(stretched);
  const p=model.tubeProfile(stretched,4);
  near(p.diameterSceneMean,initial/Math.sqrt(2));
  p.radiiScene.forEach(x=>near(x,initial/(2*Math.sqrt(2))));
});
check('nonuniform material stretching has radius variation but still finite positive',()=>{
  model.reset({points:poly,source:'ideal',metadata:meta});
  const deformed=new Float64Array([2,0,0, 0,1,0, -1,0,0, 0,-1,0]);
  model.observe(deformed);
  const p=model.tubeProfile(deformed,64);
  assert(p.maxRadiusScene>p.minRadiusScene);
  p.radiiScene.forEach(x=>assert(Number.isFinite(x)&&x>0));
});
check('non-ideal and broken material labels never get an ideal tube',()=>{
  assert.equal(model.reset({points:poly,source:'knotplot',metadata:meta}).status,'NOT_ELIGIBLE_IDEAL_ONLY');
  assert.equal(model.tubeProfile(poly,4),null);
  model.reset({points:poly,source:'ideal',metadata:meta});
  assert.equal(model.tubeProfile(new Float64Array([...poly,1,1,1]),4),null);
});
check('pure translation cannot change derived visible diameter',()=>{
  model.reset({points:poly,source:'ideal',metadata:meta});
  const t=poly.map((x,i)=>x+(i%3===0?200:0));
  const ref=model.tubeProfile(poly,4),now=model.tubeProfile(t,4);
  near(ref.diameterSceneMean,now.diameterSceneMean);
});
check('actual Three.js TubeGeometry rings have the requested visible radius',()=>{
  const T=req('../apps/web/vendor/three.min.js');
  const src=readFileSync('apps/web/src/legacy/vortexlab-runtime.js','utf8');
  const from=src.indexOf('function vlRescaleTubeRings('),to=src.indexOf('window.__vlRefreshTubeVisualization',from);
  assert(from>0&&to>from);
  const adjust=vm.runInNewContext('('+src.slice(from,to).trim()+')',{THREE:T,Error,Number,Math});
  const curve=new T.CatmullRomCurve3([new T.Vector3(1,0,0),new T.Vector3(0,1,0),new T.Vector3(-1,0,0),new T.Vector3(0,-1,0)],true);
  const n=48,radial=12,scale=0.18;
  const geo=new T.TubeGeometry(curve,n,1,radial,true);
  adjust(geo,curve,Float64Array.from({length:n+1},()=>scale),n,radial);
  const a=geo.getAttribute('position');
  for(const i of [0,1,12,24,36,48]){
    const p=curve.getPointAt(i/n);
    for(let j=0;j<=radial;j++){
      const k=i*(radial+1)+j;
      assert(Math.abs(Math.hypot(a.getX(k)-p.x,a.getY(k)-p.y,a.getZ(k)-p.z)-scale)<2e-7);
    }
  }
});
check('rendering is opt-in and no regularization parameters assigned',()=>{
  const src=readFileSync('apps/web/src/legacy/vortexlab-runtime.js','utf8');
  const ui=readFileSync('apps/web/twist-flow/twist-flow.js','utf8');
  const html=readFileSync('apps/web/twist-flow/index.html','utf8');
  assert.match(src,/vlTwistIsTubeDisplay\(\)/);
  assert.match(src,/material\.tubeProfile\(Y\.subarray/);
  assert.match(src,/vlRescaleTubeRings\(/);
  assert.match(ui,/window\.__vlIdealTubeDisplayRequested=true/);
  assert.match(html,/id="tubeFallbackFraction"/);
  assert(!/P\.a\s*=/.test(src.slice(src.indexOf('function vlTwistFallbackRadius'),src.indexOf('function tubesWanted'))));
});
console.log('PASS P7 v0.7.1 ideal ropelength tube rendering:',checks,'tests');
