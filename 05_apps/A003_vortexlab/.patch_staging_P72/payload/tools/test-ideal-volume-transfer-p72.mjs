import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {readFileSync} from 'node:fs';
const require=createRequire(import.meta.url);
const A=require('../apps/web/src/legacy/model-a-ideal-stretch.js');
const rc=1.40897017e-15;
const near=(a,b,tol=1e-10)=>assert(Math.abs(a-b)<=tol*Math.max(1e-300,Math.abs(b)),`${a} != ${b}`);
const idealRop=16.371637;
const ref={ideal:true,L:idealRop,D:1,knotId:'3:1:1',topologyKey:'3_1',xyOverL:0.1};
const points=new Float64Array([1,0,0, 0,1,0, -1,0,0, 0,-1,0]);
let n=0;function check(name,fn){fn();n++;console.log('PASS',name);}
check('all explicitly named trefoil providers map to 3_1',()=>{
  for(const [source,key] of [['ideal','3:1:1'],['knotplot','knot_3.1'],['fseries','3_1'],['fseries','3_1p'],['fseries','3_1u'],['twist','KNOT_3_1_N1024_ORIG'],['twist','KNOT_3_1_N2048_MIRROR'],['twist','3_1_N1024']])assert.equal(A.topologyFromSource(source,key),'3_1');
  assert.equal(A.topologyFromSource('builtin','trefoil'),'3_1');
  for(const id of ['link_3.1','knot_13.1','knot_3.12','knot_3.1x','KNOT_3_1_EXTRA','NOT_3_1_N1024'])assert.notEqual(A.topologyFromSource('knotplot',id),'3_1');
});
check('nonideal trefoil derives core diameter from fixed ideal volume + equal XY anchor',()=>{
  const m=A.reset({points,source:'knotplot',metadata:{knotId:'knot_3.1',componentCount:1},reference:ref});
  assert.equal(m.status,'REFERENCE_TRANSFER');
  assert.equal(m.topologyKey,'3_1');
  assert.equal(m.referenceKnotId,'3:1:1');
  assert.equal(m.transferAssumption,'EQUAL_IDEAL_XY_FOOTPRINT');
  near(m.referenceContourMeters,2*rc*idealRop);
  near(m.physicalPerSimMeter,2*rc*idealRop*0.1);
  const expectedCore=rc*Math.sqrt(m.referenceContourMeters/m.initialContourMeters);
  near(m.meanCoreMeters,expectedCore);
  near(m.volumeMetersCubed, Math.PI*rc*rc*2*rc*idealRop);
  assert(m.volumeRelativeError<1e-12); // floating point volume balance
  const p=A.tubeProfile(points,80);assert.equal(p.source,'IDEAL_VOLUME_TRANSFER');
  near(p.referenceDiameterScene,2*m.initialCoreMeters/m.physicalPerSimMeter);
});
check('same XY footprint, longer contour -> smaller derived initial diameter',()=>{
  const square=A.reset({points,source:'knotplot',metadata:{knotId:'knot_3.1',componentCount:1},reference:ref});
  const elongated=new Float64Array([1,0,0,0,1,2,-1,0,0,0,-1,-2]);
  const longer=A.reset({points:elongated,source:'fseries',metadata:{knotId:'3_1p',componentCount:1},reference:ref});
  assert(longer.initialContourMeters>square.initialContourMeters);
  near(longer.initialCoreMeters/square.initialCoreMeters,Math.sqrt(square.initialContourMeters/longer.initialContourMeters));
});
check('uniform scene scaling must not change physical prediction with equal-XY normalization',()=>{
  const baseline=A.reset({points,source:'fseries',metadata:{knotId:'3_1u',componentCount:1},reference:ref});
  const double=A.reset({points:points.map(x=>2*x),source:'fseries',metadata:{knotId:'3_1u',componentCount:1},reference:ref});
  near(baseline.initialCoreMeters,double.initialCoreMeters);
  near(baseline.initialContourMeters,double.initialContourMeters);
  near(baseline.referenceXYRadiusMeters,double.referenceXYRadiusMeters);
});
check('material stretch changes local core and preserves original ideal reference volume',()=>{
  const m=A.reset({points,source:'twist',metadata:{knotId:'KNOT_3_1_N1024_ORIG',componentCount:1},reference:ref});
  const q=A.observe(points.map((x)=>x*2));
  near(q.lambda,2);near(q.meanCoreMeters,m.meanCoreMeters/Math.sqrt(2));
  near(q.volumeMetersCubed,m.referenceVolumeMetersCubed);
  const profile=A.tubeProfile(points.map(x=>2*x),64);
  near(profile.diameterSceneMean,2*(m.initialCoreMeters/m.physicalPerSimMeter)/Math.sqrt(2));
});
check('translation and rotation do not trigger physical stretching',()=>{
  const m=A.reset({points,source:'knotplot',metadata:{knotId:'knot_3.1',componentCount:1},reference:ref});
  const translated=points.map((v,i)=>v+(i%3===0?100:0));
  const q=A.observe(translated);near(q.lambda,1);near(q.meanCoreMeters,m.meanCoreMeters);
});
check('unmatched topology, missing ideal metadata, and unsupported linked objects refused',()=>{
  assert.equal(A.reset({points,source:'twist',metadata:{knotId:'KNOT_5_2_N1024_ORIG',componentCount:1},reference:ref}).status,'TOPOLOGY_LABEL_MISMATCH');
  assert.equal(A.reset({points,source:'knotplot',metadata:{knotId:'knot_3.1',componentCount:1}}).status,'NOT_ELIGIBLE_IDEAL_ONLY');
  assert.equal(A.reset({points,source:'knotplot',metadata:{knotId:'knot_3.1',componentCount:2},reference:ref}).status,'NOT_ELIGIBLE_SOLO_MATERIAL_REFERENCE');
  assert.equal(A.reset({points,source:'xyz',metadata:{knotId:'KNOT_3_1_N1024_ORIG',componentCount:1},reference:ref}).status,'UNSUPPORTED_SOURCE_NO_REFERENCE');
});
check('preview marked separately as unqualified; remains visual-only',()=>{
  const p=A.reset({points,source:'twist',metadata:{knotId:'KNOT_3_1_N1024_ORIG',componentCount:1},reference:ref,previewN:192});
  assert.equal(p.status,'REFERENCE_TRANSFER_PREVIEW');assert.equal(p.previewUnqualified,true);
  assert.equal(A.tubeProfile(points,4).previewUnqualified,true);
});
check('point-count changes block transfer material labels',()=>{
  A.reset({points,source:'fseries',metadata:{knotId:'3_1p',componentCount:1},reference:ref});
  assert.equal(A.observe(new Float64Array([...points,1,1,1])).status,'MATERIAL_LABELS_CHANGED_N');
});
check('source integration is visual-only and uses canonical ideal db per class',()=>{
  const runtime=readFileSync('apps/web/src/legacy/vortexlab-runtime.js','utf8');
  const ui=readFileSync('apps/web/twist-flow/twist-flow.js','utf8');
  assert.match(runtime,/const idealReference=idealKey\?getIdealKnotCatalog\(\)\?\.db\?\.\[idealKey\]/);
  assert.match(runtime,/sampleIdealComponent\(knotEntryComponents\(idealReference\)\[0\],512\)/);
  assert.match(runtime,/material\.tubeProfile\(Y\.subarray/);
  assert.match(runtime,/physicalCoreCoupled:false/);
  assert.match(ui,/EQUAL_IDEAL_XY_FOOTPRINT/);
});
console.log('PASS P7.2 ideal volume transfer:',n,'tests');
