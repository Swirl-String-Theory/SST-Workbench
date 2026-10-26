(function(){'use strict';
const B=window.VortexLabBorromean,G=window.VortexLabCatalogGeometry,D=window.VLB_CATALOGS;
const notice=document.getElementById('notice'),slotRoot=document.getElementById('sources');
if(!B||!G||!D||!D.ideal?.db['L6a4']||typeof THREE==='undefined'){
notice.textContent='Catalogus of geometrische renderer ontbreekt: '+(window.VLB_CATALOG_LOAD_ERROR||'controleer de bestaande VortexLab-data');notice.className='bad';return;
}
const sources=['ideal','fseries','knotplot','twist'],names={ideal:'Gilbert Ideal/Tight',fseries:'Fourier-series',knotplot:'KnotPlot',twist:'A006 Twist/Torus'},rows=B.catalogRows(D);
const slots=[],colors=[0x5bb9ff,0x8defac,0xff91b5],view=document.getElementById('view3d');let result=null,geometryVisible=[];
function textOption(label,value){const opt=document.createElement('option');opt.value=value;opt.textContent=label;return opt;}
for(let i=0;i<3;i++){
 const outer=document.createElement('div');outer.className='slot';const lab=document.createElement('label');lab.textContent='Component '+String.fromCharCode(65+i);const wrapper=document.createElement('div');const s=document.createElement('select'),k=document.createElement('select');s.setAttribute('aria-label','Bron voor '+lab.textContent);k.setAttribute('aria-label','Knoop voor '+lab.textContent);
 for(let x of sources)s.add(textOption(names[x],x));wrapper.append(s,k);outer.append(lab,wrapper);slotRoot.append(outer);slots.push({s,k});
 s.addEventListener('change',()=>fill(i));k.addEventListener('change',clearExport);
}
function fill(i,want){const {s,k}=slots[i];k.replaceChildren();for(const r of rows.filter(x=>x.source===s.value))k.add(textOption(r.id+' · '+r.label+(r.sourceRole?' · '+r.sourceRole:''),r.id));if(want&&D[s.value].db[want])k.value=want;clearExport();}
function select(i,key){const bar=key.indexOf('|');let source=key.slice(0,bar),id=key.slice(bar+1);if(!D[source]?.db[id])return;slots[i].s.value=source;fill(i,id);}
for(let i=0;i<3;i++){slots[i].s.value='ideal';fill(i,'3:1:1');}select(1,'ideal|5:1:1');select(2,'ideal|7:1:1');
function clearExport(){result=null;document.getElementById('downloadXyz').disabled=true;document.getElementById('downloadJson').disabled=true;}
for(let btn of document.querySelectorAll('[data-preset]'))btn.addEventListener('click',()=>{btn.dataset.preset.split(',').forEach((v,i)=>select(i,v));run();});
const blob=document.getElementById('blob');blob.addEventListener('input',()=>document.getElementById('blobValue').textContent=blob.value+'%');
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));view.appendChild(renderer.domElement);
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(42,1,.01,1000),group=new THREE.Group();scene.add(group);scene.add(new THREE.AmbientLight(0xffffff,.72));const light=new THREE.DirectionalLight(0xffffff,.8);light.position.set(2,4,3);scene.add(light);
let distance=7,drag=null;group.rotation.set(.35,.25,0);
renderer.domElement.addEventListener('pointerdown',e=>{drag=[e.clientX,e.clientY];renderer.domElement.setPointerCapture(e.pointerId)});
renderer.domElement.addEventListener('pointermove',e=>{if(!drag)return;group.rotation.y+=(e.clientX-drag[0])*.009;group.rotation.x+=(e.clientY-drag[1])*.009;drag=[e.clientX,e.clientY]});renderer.domElement.addEventListener('pointerup',()=>drag=null);
renderer.domElement.addEventListener('wheel',e=>{e.preventDefault();distance*=Math.exp(e.deltaY*.001);distance=Math.max(1,Math.min(200,distance));},{passive:false});
function draw(parts){while(group.children.length){const m=group.children[0];group.remove(m);m.geometry?.dispose();m.material?.dispose();}let all=parts.flat(),min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];all.forEach(p=>p.forEach((v,i)=>{min[i]=Math.min(min[i],v);max[i]=Math.max(max[i],v)}));const center=min.map((v,i)=>(v+max[i])/2),extent=Math.max(...max.map((v,i)=>v-min[i]));distance=Math.max(2,extent*2.3);
parts.forEach((arr,i)=>{const pts=arr.map(p=>new THREE.Vector3(...p.map((v,j)=>v-center[j])));const curve=new THREE.CatmullRomCurve3(pts,true,'centripetal');const tube=new THREE.TubeGeometry(curve,Math.min(1600,Math.max(180,arr.length*2)),Math.max(extent*.0025,.001),6,true);group.add(new THREE.Mesh(tube,new THREE.MeshPhongMaterial({color:colors[i],shininess:95})));});}
function animate(){requestAnimationFrame(animate);const rect=view.getBoundingClientRect();const w=Math.max(1,Math.round(rect.width)),h=Math.max(1,Math.round(rect.height));if(renderer.domElement.width!==Math.round(w*renderer.getPixelRatio())||renderer.domElement.height!==Math.round(h*renderer.getPixelRatio())){renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();}camera.position.set(0,0,distance);camera.lookAt(0,0,0);renderer.render(scene,camera);}animate();
function run(){clearExport();try{
 const choices=slots.map(x=>({source:x.s.value,id:x.k.value,entry:D[x.s.value].db[x.k.value]}));
 result=B.build(G,D.ideal.db['L6a4'],choices,{n:Number(document.getElementById('resolution').value),blobFraction:Number(blob.value)/100});
 const {check}=result;draw(result.parts);notice.className=check.staticCandidate?'good':'bad';notice.textContent=result.status+(check.staticCandidate?' · export toegestaan':' · export geblokkeerd; kies kleinere knopen of andere seeds');
 const tb=document.getElementById('gates');tb.replaceChildren();for(let [key,val] of Object.entries(check.gates)){const tr=document.createElement('tr'),k=document.createElement('td'),v=document.createElement('td');k.textContent=key.replaceAll('_',' ');v.textContent=val;v.className=val==='PASS'?'ok':val==='FAIL'?'fail':'pending';tr.append(k,v);tb.append(tr);}
 document.getElementById('metrics').textContent='Component N: '+result.parts.map(p=>p.length).join(' / ')+'\n'+
 'Pairwise Lk (benadering): '+check.pairwiseLinkingMidpoint.map(x=>x.toFixed(5)).join(' / ')+'\n'+
 'Intercomponent min.: '+check.intercomponentClearance.map(x=>x.toFixed(5)).join(' / ')+'\n'+
 'Eigenafstand min.: '+check.selfClearance.map(x=>x.toFixed(5)).join(' / ')+'\n'+
 'Alle lengtewaarden zijn genormaliseerde broncoördinaten; niet automatisch SI.';
 document.getElementById('downloadXyz').disabled=!check.staticCandidate;document.getElementById('downloadJson').disabled=!check.staticCandidate;
}catch(err){result=null;notice.className='bad';notice.textContent='Afgewezen: '+err.message;document.getElementById('metrics').textContent=String(err.stack||err);}}
document.getElementById('build').addEventListener('click',run);
function dl(name,data,type){const url=URL.createObjectURL(new Blob([data],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);}
function stem(){return 'BORROMEAN_'+slots.map(x=>x.s.value+'-'+x.k.value.replaceAll(':','-').replaceAll('/','-')).join('__')+'_GEOMETRY_CANDIDATE';}
document.getElementById('downloadXyz').addEventListener('click',()=>{if(result?.check.staticCandidate)dl(stem()+'.xyz',B.xyz(result.parts),'text/plain')});
document.getElementById('downloadJson').addEventListener('click',()=>{if(result?.check.staticCandidate){const {parts,...rest}=result;dl(stem()+'.json',JSON.stringify({...rest,pointsPerComponent:parts.map(p=>p.length),exportedAt:new Date().toISOString()},null,2),'application/json')}});
run();
})();
