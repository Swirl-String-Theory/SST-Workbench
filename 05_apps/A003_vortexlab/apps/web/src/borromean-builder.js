/** Universal Borromean component builder v0.1.0.
 * Geometric candidate only. Three closed single-knot sources are attached by local
 * connected-sum splices to the THREE-component Gilbert L6a4 carrier.
 * Does NOT certify component isotopy, Milnor mu123, or Euler equilibria.
 */
(function(root,factory){ const api=factory(); if(typeof module==='object'&&module.exports)module.exports=api; root.VortexLabBorromean=api; })(typeof globalThis!=='undefined'?globalThis:this,function(){
'use strict';
const V=(x,y,z)=>[x,y,z],add=(a,b)=>V(a[0]+b[0],a[1]+b[1],a[2]+b[2]),sub=(a,b)=>V(a[0]-b[0],a[1]-b[1],a[2]-b[2]),mul=(a,s)=>V(a[0]*s,a[1]*s,a[2]*s),dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2],cross=(a,b)=>V(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]),norm=a=>Math.hypot(...a), unit=a=>mul(a,1/Math.max(norm(a),1e-30)),mix=(a,b,t)=>add(mul(a,1-t),mul(b,t));
function asPoints(flat){ if(!flat||flat.length%3)throw Error('Invalid 3-column geometry');const x=[];for(let i=0;i<flat.length;i+=3){const p=V(+flat[i],+flat[i+1],+flat[i+2]);if(!p.every(Number.isFinite))throw Error('Nonfinite XYZ');x.push(p);}if(x.length<16)throw Error('At least 16 points required');return x;}
function fromPoints(p){const f=new Float64Array(p.length*3);p.forEach((v,i)=>f.set(v,3*i));return f;}
function sample(geometry,entry,source,n){if(!entry||!Array.isArray(entry.components)||entry.components.length!==1)throw Error('Selection must be a one-component closed knot');return asPoints(geometry.sampleCatalogComponent(entry,entry.components[0],n,source));}
function catalogRows(data){const rows=[];for(const [source,p] of Object.entries(data)){if(!p||!Array.isArray(p.ids)||!p.db)continue;for(const id of p.ids){const e=p.db[id];if(!e||!Array.isArray(e.components)||e.components.length!==1)continue;
  if(e.kind&&String(e.kind).toUpperCase()==='LINK')continue;
  rows.push({key:source+'|'+id,source,id,label:e.selectorLabel||e.label||e.knotId||id,topology:e.topology||e.conway||'',sourceRole:e.sourceRole||'',status:e.status||'UNCERTIFIED'});
}}return rows;}
function segDist(a,b,c,d){ // squared distance of finite 3D segments, Ericson's robust clamp
const u=sub(b,a),v=sub(d,c),w=sub(a,c),A=dot(u,u),B=dot(u,v),C=dot(v,v),D=dot(u,w),E=dot(v,w),DEN=A*C-B*B;
if(A<1e-24||C<1e-24)return Infinity;
let sn,sd=DEN,tn,td=DEN;if(DEN<1e-20){sn=0;sd=1;tn=E;td=C;}else{sn=B*E-C*D;tn=A*E-B*D;if(sn<0){sn=0;tn=E;td=C;}else if(sn>sd){sn=sd;tn=E+B;td=C;}}
if(tn<0){tn=0;if(-D<0)sn=0;else if(-D>A)sn=sd;else {sn=-D;sd=A;}}else if(tn>td){tn=td;if(-D+B<0)sn=0;else if(-D+B>A)sn=sd;else{sn=-D+B;sd=A;}}
const s=Math.abs(sn)<1e-20?0:sn/sd,t=Math.abs(tn)<1e-20?0:tn/td;
return norm(sub(add(w,mul(u,s)),mul(v,t)));
}
function minDistance(a,b,own=false,skip=3){let min=Infinity;for(let i=0;i<a.length;i++){const j=(i+1)%a.length;for(let k=0;k<b.length;k++){if(own){let t=Math.abs(i-k);t=Math.min(t,a.length-t);if(t<=skip)continue;}min=Math.min(min,segDist(a[i],a[j],b[k],b[(k+1)%b.length]));}}return min;}
function length(p){let x=0;for(let j=0;j<p.length;j++)x+=norm(sub(p[(j+1)%p.length],p[j]));return x;}
function edgeStats(p){let mn=Infinity,mx=0,edges=[];for(let i=0;i<p.length;i++){const x=norm(sub(p[(i+1)%p.length],p[i]));mn=Math.min(mn,x);mx=Math.max(mx,x);edges.push(x);}const median=edges.sort((a,b)=>a-b)[Math.floor(edges.length/2)];return {min:mn,max:mx,median,ratio:mx/Math.max(mn,1e-30),longestOverMedian:mx/Math.max(median,1e-30)};}
function knotQuality(p){const L=length(p),E=edgeStats(p);return {length:L,edge:E,closedByPeriodicIndexing:true,degenerate:!(L>1e-8&&E.min>1e-9&&E.longestOverMedian<6)};}
function isolatedAnchor(carriers,i){const a=carriers[i],skip=Math.max(8,Math.floor(a.length/14));let best={j:0,clearance:-1};
for(let j=0;j<a.length;j+=3){const pos=a[j];
// point-segment clearance (avoids point-point biased estimates)
let q=Infinity;for(let b=0;b<carriers.length;b++){const p=carriers[b];for(let k=0;k<p.length;k+=2){if(b===i){let h=Math.abs(j-k);h=Math.min(h,p.length-h);if(h<skip)continue;}const x=sub(p[(k+1)%p.length],p[k]);q=Math.min(q,norm(sub(pos,add(p[k],mul(x,Math.min(1,Math.max(0,dot(sub(pos,p[k]),x)/Math.max(dot(x,x),1e-20))))))));}}
if(q>best.clearance)best={j,clearance:q};
}return best;
}
function candidateNormals(base,j,others){const x=unit(sub(base[(j+1)%base.length],base[(j-1+base.length)%base.length]));const global=[0,0,1],refs=[V(0,1,0),V(1,0,0),global];let candidates=[];
for(let r of refs){let n=sub(r,mul(x,dot(r,x)));if(norm(n)<.15)continue;n=unit(n);candidates.push(n,mul(n,-1));}
// Choose a free direction by distance to other carriers and nonlocal own edges
function freedom(n){let score=Infinity;const c=base[j];for(let t of [0.15,0.25,0.4]){const p=add(c,mul(n,t));for(let b=0;b<others.length;b++){const curve=others[b];for(let k=0;k<curve.length;k+=4){if(b===0){let idx=Math.abs(j-k);idx=Math.min(idx,curve.length-idx);if(idx<curve.length/14)continue;}const u=sub(curve[(k+1)%curve.length],curve[k]);const q=add(curve[k],mul(u,Math.min(1,Math.max(0,dot(sub(p,curve[k]),u)/Math.max(dot(u,u),1e-20)))));score=Math.min(score,norm(sub(p,q)));}}}return score;}
return candidates.sort((a,b)=>freedom(b)-freedom(a))[0]||V(0,0,1);
}
function cutAndAttach(carriers,i,knot,blobFraction){const base=carriers[i],{j,clearance}=isolatedAnchor(carriers,i);
if(!(clearance>1e-4))throw Error('No isolated attachment position on carrier '+i);
let idx=0;for(let k=1;k<knot.length;k++)if(knot[k][1]<knot[idx][1])idx=k;
const P=knot[idx],prior=knot[(idx-1+knot.length)%knot.length],next=knot[(idx+1)%knot.length];
const localX=unit(sub(next,prior));const Y=V(0,1,0),localZ=unit(cross(localX,Y));if(norm(localZ)<.5)throw Error('Knot extremum tangent is poorly resolved');
const T=unit(sub(base[(j+1)%base.length],base[(j-1+base.length)%base.length]));let N=candidateNormals(base,j,[base,...carriers.filter((_,k)=>k!==i)]);N=unit(sub(N,mul(T,dot(N,T))));const B=unit(cross(T,N));
const rMax=Math.max(...knot.map(q=>norm(sub(q,P))));const R=clearance*blobFraction;const scale=R/Math.max(rMax,1e-20),height=R*1.45;
const c=base[j];const knotWorld=knot.map(q=>{const d=sub(q,P);return add(add(add(c,mul(T,dot(d,localX)*scale)),mul(N,height+dot(d,Y)*scale)),mul(B,dot(d,localZ)*scale));});
const path=[];for(let k=(idx-1+knot.length)%knot.length;k!==(idx+1)%knot.length;k=(k-1+knot.length)%knot.length)path.push(knotWorld[k]);path.push(knotWorld[(idx+1)%knot.length]);
const output=[];for(let k=0;k<base.length;k++){
if(k===j){const a=base[(j-1+base.length)%base.length],b=base[(j+1)%base.length];
for(let t=1;t<=8;t++)output.push(mix(a,path[0],t/9));
for(let t of path)output.push(t);
for(let t=1;t<=8;t++)output.push(mix(path[path.length-1],b,t/9));
}else output.push(base[k]);}
return {points:output,attachment:{index:j,sourceCutIndex:idx,localBallRadius:R,offset:height,anchorClearance:clearance,scale,construction:'local polygonal connected-sum splice',provedAmbientIsotopy:false}};
}
function gaussLink(a,b){ // midpoint discretization of Gauss integral, round integer only with margin
let s=0;for(let i=0;i<a.length;i++){const da=sub(a[(i+1)%a.length],a[i]),ca=mix(a[i],a[(i+1)%a.length],.5);for(let k=0;k<b.length;k++){const db=sub(b[(k+1)%b.length],b[k]),r=sub(ca,mix(b[k],b[(k+1)%b.length],.5)),nr=norm(r);if(nr>1e-9)s+=dot(r,cross(da,db))/(nr*nr*nr);}}
return s/(4*Math.PI);
}
function downsample(p,max=140){const stride=Math.max(1,Math.ceil(p.length/max));return p.filter((_,i)=>i%stride===0);}
function validate(parts,sourceQuality,baseLink,attachments){const pairs=[[0,1],[0,2],[1,2]],lk=pairs.map(([a,b])=>gaussLink(downsample(parts[a]),downsample(parts[b]))),minInter=pairs.map(([a,b])=>minDistance(parts[a],parts[b])),self=parts.map(p=>minDistance(p,p,true,4)),qualities=parts.map(knotQuality);
const gates={three_closed_polygonal_components:parts.length===3&&qualities.every(q=>!q.degenerate)?'PASS':'FAIL',source_geometry_numeric_quality:sourceQuality.every(q=>!q.degenerate)?'PASS':'FAIL',source_knot_identity:'UNRESOLVED',nonadjacent_self_separation:self.every(x=>x>1e-5)?'PASS':'FAIL',pairwise_nonintersection:minInter.every(x=>x>1e-5)?'PASS':'FAIL',pairwise_linking_near_base:lk.every((x,i)=>Math.abs(x-baseLink[i])<.13)?'PASS':'FAIL',component_knot_isotopy:'UNRESOLVED',Milnor_mu123:'UNRESOLVED',finite_core_reach:'UNRESOLVED',Euler_dynamics:'NOT_RUN'};
return {gates,components:qualities,selfClearance:self,intercomponentClearance:minInter,pairwiseLinkingMidpoint:lk,pairwiseLinkingBase:baseLink,attachments,staticCandidate:Object.values(gates).every(v=>v!=='FAIL')};}
function build(geometry,carrierEntry,selected,{n=256,blobFraction=.10}={}){
if(!Array.isArray(carrierEntry?.components)||carrierEntry.components.length!==3)throw Error('Carrier must have exactly 3 components');if(!Array.isArray(selected)||selected.length!==3)throw Error('Select 3 single knots');
const carriers=carrierEntry.components.map(c=>asPoints(geometry.sampleIdealComponent(c,n)));
const sourceGeometry=selected.map(x=>sample(geometry,x.entry,x.source,n));const sourceQuality=sourceGeometry.map(knotQuality);
if(sourceQuality.some(q=>q.degenerate))throw Error('Rejected degenerate knot geometry');
const baseLink=[[0,1],[0,2],[1,2]].map(([a,b])=>gaussLink(downsample(carriers[a]),downsample(carriers[b])));
const attachments=[];
for(let i=0;i<3;i++){if(selected[i].id==='0:1:1'&&selected[i].source==='ideal'){attachments.push({construction:'identity (unknot carrier)',provedAmbientIsotopy:true});continue;}
const one=cutAndAttach(carriers,i,sourceGeometry[i],blobFraction);carriers[i]=one.points;attachments.push(one.attachment);}
const check=validate(carriers,sourceQuality,baseLink,attachments);
return {parts:carriers,check,provenance:selected.map(x=>({source:x.source,id:x.id,label:x.entry.label||x.id,sourceRole:x.entry.sourceRole||null,kind:x.entry.kind||null})),carrier:'Gilbert Ideal/Tight L6a4',builder:'Universal_Borromean_VortexLab_v0.1.0',status:check.staticCandidate?'STATIC_GEOMETRY_CANDIDATE':'REJECTED_GEOMETRY',topology:'Decorated Borromean-pattern link, NOT certified strict Brunnian',limits:['No certified Milnor triple invariant','No knot equivalence certificate','No finite-core reach certificate','No Euler dynamics']};
}
function xyz(parts){return parts.map(p=>p.map(v=>v.map(x=>Number(x).toPrecision(17)).join(' ')).join('\n')).join('\n\n')+'\n';}
return {catalogRows,build,xyz,asPoints,fromPoints,knotQuality,gaussLink,minDistance,segDist};
});
