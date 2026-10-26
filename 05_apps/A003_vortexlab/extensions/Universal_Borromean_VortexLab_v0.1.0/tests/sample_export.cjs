'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),crypto=require('crypto');
const web=process.env.VL_SOURCE;
if(!web)throw Error('Set VL_SOURCE to existing VortexLab/apps/web directory');
const G=require(path.join(web,'src/catalog-geometry.js')),B=require(path.join(web,'src/borromean-builder.js'));
const catalogs={};let sourceHashes={};for(const [source,file,prefix] of [['ideal','ideal_knots_data.js','IDEAL'],['fseries','fourier_knots_data.js','FSERIES'],['knotplot','knotplot_knots_data.js','KNOTPLOT'],['twist','twist_knot_data.js','TWIST']]){
const bytes=fs.readFileSync(path.join(web,'data',file));sourceHashes[file]=crypto.createHash('sha256').update(bytes).digest('hex');catalogs[source]=vm.runInNewContext(bytes.toString()+`;({ids:${prefix}_KNOT_IDS,db:${prefix}_KNOT_DB})`);}
const specimens=[['3_1-3_1-3_1',['ideal|3:1:1','ideal|3:1:1','ideal|3:1:1']],['3_1-5_1-7_1',['ideal|3:1:1','ideal|5:1:1','ideal|7:1:1']],['mixed',['ideal|3:1:1','fseries|5_1','knotplot|knot_7.1']]];
for(const [name,keys] of specimens){let s=keys.map(key=>{const j=key.indexOf('|'),source=key.slice(0,j),id=key.slice(j+1);return {source,id,entry:catalogs[source].db[id]}});let r=B.build(G,catalogs.ideal.db['L6a4'],s,{n:256,blobFraction:.08});if(!r.check.staticCandidate)throw Error(name+' rejected '+JSON.stringify(r.check.gates));const p=path.resolve(__dirname,'../examples/'+name);fs.mkdirSync(path.dirname(p),{recursive:true});let xyz=B.xyz(r.parts);fs.writeFileSync(p+'.xyz',xyz);
const {parts,...noParts}=r;fs.writeFileSync(p+'.json',JSON.stringify({...noParts,sourceFileSha256:sourceHashes,xyzSha256:crypto.createHash('sha256').update(xyz).digest('hex'),pointCounts:parts.map(x=>x.length)},null,2)+'\n');console.log(name,r.status,r.parts.map(p=>p.length),r.check.pairwiseLinkingMidpoint,r.check.selfClearance);}
