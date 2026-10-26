import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFileSync} from 'node:fs';
const require=createRequire(import.meta.url);
const A=require('../apps/web/src/legacy/model-a-ideal-stretch.js');
const rc=1.40897017e-15;
const near=(x,y,tol=1e-12)=>assert(Math.abs(x-y)<=tol*Math.max(Math.abs(y),1e-300),`${x} != ${y}`);
const tests=[];const check=(name,fn)=>{fn();tests.push(name);};
const base=new Float64Array([1,0,0, 0,1,0, -1,0,0, 0,-1,0]);
const meta={ideal:true,L:16.371637,D:1,knotId:'3:1:1',componentCount:1};
check('source gate rejects non-ideal',()=>{assert.equal(A.reset({points:base,source:'twist',metadata:meta}).status,'NOT_ELIGIBLE_IDEAL_ONLY');});
check('preview, auto-relax, and multi component rejected',()=>{
  assert.equal(A.reset({points:base,source:'ideal',metadata:meta,previewN:192}).status,'NOT_ELIGIBLE_IDEAL_ONLY');
  assert.equal(A.reset({points:base,source:'ideal',metadata:meta,autoRelax:true}).status,'NOT_ELIGIBLE_IDEAL_ONLY');
  assert.equal(A.reset({points:base,source:'ideal',metadata:{...meta,componentCount:2}}).status,'NOT_ELIGIBLE_IDEAL_ONLY');
});
check('ideal reference exact volume/length/core and no fabricated steps',()=>{
  const s=A.reset({points:base,source:'ideal',metadata:meta});
  assert.equal(s.status,'REFERENCE_ONLY');assert.equal(s.steps,0);near(s.meanCoreMeters,rc);
  near(s.lambda,1);near(s.referenceContourMeters,2*rc*meta.L);near(s.contourMeters,s.referenceContourMeters);
  assert(s.volumeRelativeError<1e-12);
});
check('actual material stretch determines local core and global geometry separately',()=>{
  const stretched=base.map(x=>2*x);
  const s=A.observe(stretched);assert.equal(s.steps,1);near(s.lambda,2);
  near(s.meanCoreMeters,rc/Math.sqrt(2));near(s.minCoreMeters,rc/Math.sqrt(2));
  near(s.maxCoreMeters,rc/Math.sqrt(2));near(s.xyRadiusMeters,2*s.referenceXYRadiusMeters);
  assert(s.volumeRelativeError<1e-12);
});
check('anisotropic stretch produces distinct local core radii and conserves tube-volume algebra',()=>{
  A.reset({points:base,source:'ideal',metadata:meta});
  const deformed=new Float64Array([1.5,0,0,0,1,0,-1,0,0,0,-1,0]);
  const s=A.observe(deformed);
  assert(s.minimumSegmentStretch<s.maximumSegmentStretch);
  assert(s.minCoreMeters<s.maxCoreMeters);
  assert(s.volumeRelativeError<1e-13);
  assert(s.xyRadiusMeters>s.referenceXYRadiusMeters);
});
check('translation cannot fabricate stretch',()=>{
  A.reset({points:base,source:'ideal',metadata:meta});
  const shifted=base.map((x,i)=>x+(i%3===0?500:0));
  const s=A.observe(shifted);near(s.lambda,1);near(s.meanCoreMeters,rc);near(s.xyRadiusMeters,s.referenceXYRadiusMeters);
});
check('degenerate initial/final segments rejected',()=>{
  const degenerate=base.slice();degenerate.set(degenerate.subarray(0,3),3);
  assert.match(A.reset({points:degenerate,source:'ideal',metadata:meta}).status,/INVALID_REFERENCE_GEOMETRY/);
  A.reset({points:base,source:'ideal',metadata:meta});
  assert.match(A.observe(degenerate).status,/INVALID_EVOLVED_GEOMETRY/);
});
check('relabelled point count blocks material inference',()=>{
  A.reset({points:base,source:'ideal',metadata:meta});
  assert.equal(A.observe(new Float64Array([...base,...[0.5,0.5,0]])).status,'MATERIAL_LABELS_CHANGED_N');
});
const runtime=readFileSync('apps/web/src/legacy/vortexlab-runtime.js','utf8');
const legacyHtml=readFileSync('apps/web/index.html','utf8');
const twist=readFileSync('apps/web/twist-flow/twist-flow.js','utf8');
const ui=readFileSync('apps/web/twist-flow/index.html','utf8');
check('runtime uses real reset and accepted step but does not modify main numerical regularization',()=>{
  assert.match(legacyHtml,/src\/legacy\/model-a-ideal-stretch\.js/);
  assert(legacyHtml.indexOf('src/legacy/model-a-ideal-stretch.js')<legacyHtml.indexOf('src/legacy/vortexlab-runtime.js'));
  assert.match(runtime,/window\.VLModelAIdealStretch\.reset\(/);
  assert.match(runtime,/window\.VLModelAIdealStretch\.observe\(Y\.subarray\(/);
  assert(runtime.indexOf('window.VLModelAIdealStretch.observe(')>runtime.indexOf('updateStretchGateAcceptedStep(Ypre,Y,dtApplied)'));
  assert.match(runtime,/physicalCoreCoupled:false/);
});
check('Twist route gated, UI fields linked to engine diagnostics',()=>{
  assert.match(twist,/window\.__vlModelAIdealRequested=true/);
  assert.match(twist,/snap\?\.idealModelA/);
  for(const id of ['modelASection','modelAStatus','modelALambda','modelACore','modelACoreRange','modelARadius','modelAVolume','modelAL0','modelAExport'])
    assert(ui.includes(`id="${id}"`),`missing ${id}`);
});
console.log(`PASS P7 Ideal Reference & Material Stretching v0.7.0: ${tests.length} tests`);
