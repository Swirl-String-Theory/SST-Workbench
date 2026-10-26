'use strict';
const fs=require('fs'),vm=require('vm'),path=require('path'),assert=require('node:assert/strict');
const base=process.env.VL_SOURCE||path.resolve(__dirname,'../../work/vortex/A003_vortexlab/apps/web');
const G=require(path.join(base,'src/catalog-geometry.js'));
const B=require(path.join(base,'src/borromean-builder.js'));
const catalogs={};
for (const [source,prefix] of [['ideal','IDEAL'],['fseries','FSERIES'],['knotplot','KNOTPLOT'],['twist','TWIST']]){
 const pathTo=path.join(base,'data',source==='fseries'?'fourier_knots_data.js':source==='ideal'?'ideal_knots_data.js':source==='knotplot'?'knotplot_knots_data.js':'twist_knot_data.js');
 const s=fs.readFileSync(pathTo,'utf8');const script=s+`\n;({ids: ${prefix}_KNOT_IDS,db:${prefix}_KNOT_DB})`;
 catalogs[source]=vm.runInNewContext(script,Object.create(null),{timeout:10000});
}
const get=(source,id)=>({source,id,entry:catalogs[source].db[id]});
const entries=B.catalogRows(catalogs);assert(entries.some(x=>x.key==='ideal|3:1:1'));assert(!entries.some(x=>x.key==='ideal|L6a4'));
console.log('Source catalogs',Object.fromEntries(Object.entries(catalogs).map(([k,v])=>[k,v.ids.length])),'eligible',entries.length);
const carrier=catalogs.ideal.db['L6a4'];assert.equal(carrier.components.length,3);
for(const ids of [['0:1:1','0:1:1','0:1:1'],['3:1:1','3:1:1','3:1:1'],['3:1:1','5:1:1','7:1:1']]){
 let st=Date.now(),r=B.build(G,carrier,ids.map(id=>get('ideal',id)),{n:256,blobFraction:.08});
 console.log(JSON.stringify({ids,status:r.status,gates:r.check.gates,base:r.check.pairwiseLinkingBase,lks:r.check.pairwiseLinkingMidpoint,self:r.check.selfClearance,inter:r.check.intercomponentClearance,n:r.parts.map(p=>p.length),ms:Date.now()-st},null,2));
 assert.equal(B.xyz(r.parts).trim().split(/\n\s*\n/).length,3);
}
for(const [source,id] of [['fseries','5_1'],['knotplot','knot_7.1'],['twist','KNOT_5_2_N1024_ORIG']]){
const e=catalogs[source].db[id];if(!e){console.log('OPTIONAL missing',source,id);continue;}const r=B.build(G,carrier,[get('ideal','3:1:1'),get(source,id),get('ideal','0:1:1')],{n:256,blobFraction:.08});
console.log('MIXED',source,id,r.status,r.check.pairwiseLinkingMidpoint);assert(r.parts.length===3);
}
const broken=Array.from({length:64},(_,i)=>[i/64,0,0]).flat();broken[broken.length-3]=20;let rejected=false;try{B.knotQuality(B.asPoints(broken)).degenerate===true&&(rejected=true);}catch(e){rejected=true;}assert(rejected,'degenerate geometry must be detectable');
console.log('BUILDER_STATIC_TESTS_PASS');
