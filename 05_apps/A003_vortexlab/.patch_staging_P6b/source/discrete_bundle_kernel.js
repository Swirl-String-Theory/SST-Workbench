// A003 Twist Flow P6b: finite open, endpoint-pinned discrete filament bundle.
// EXPERIMENTAL: two-way regularized Biot-Savart, NOT an Euler closure.
const vlDiscrete=(()=>{
  const cfg={mode:'off',omega:1,spacing:0.06,side:3,nodes:17};
  let X=new Float64Array(0),initial=new Float64Array(0),before=new Float64Array(0);
  let trial=null,descs=[],meshes=[],drawGroup=null,lastGap=Infinity,fieldCache=null;
  const active=()=>window.__vlTwistFlowOverlayParticles===true&&cfg.mode==='discrete'&&cfg.omega!==0&&X.length>0;
  const gamm=()=>2*cfg.omega*cfg.spacing*cfg.spacing;
  const valid=(v,lo,hi)=>Number.isFinite(v)&&v>=lo&&v<=hi;
  function setup(){
    clearVisual();descs=[];lastGap=Infinity;trial=null;fieldCache=null;
    if(cfg.mode!=='discrete'||!Y||!fils.length){X=new Float64Array(0);initial=X;before=X;return;}
    const N=cfg.nodes,side=cfg.side,d=cfg.spacing;
    // Finite straight strands, pinned endpoints. No artificial closure across z.
    const halfHeight=Math.max(2*d,Math.min(P.Hcyl,0.36));
    X=new Float64Array(3*side*side*N);let count=0;
    for(let iy=0;iy<side;iy++)for(let ix=0;ix<side;ix++){
      const x=(ix-(side-1)/2)*d,y=(iy-(side-1)/2)*d;
      const off=3*N*count;descs.push({off,N,ix,iy});count++;
      for(let k=0;k<N;k++){
        X[off+3*k]=x;X[off+3*k+1]=y;
        X[off+3*k+2]=-halfHeight+2*halfHeight*k/(N-1);
      }
    }
    initial=X.slice();before=X.slice();
    render();
  }
  function setConfig(opts){
    const c={...cfg,...opts};
    if(!['off','discrete'].includes(c.mode)||!valid(c.omega,0,1000)||!valid(c.spacing,0.002,0.5)||
      ![1,3,5].includes(c.side)||![9,17,25].includes(c.nodes))throw new Error('P6b ongeldige configuratie');
    Object.assign(cfg,c);setup();
    return report();
  }
  function segments(A,ds,open){
    const result=[];
    for(let j=0;j<ds.length;j++){
      const f=ds[j],len=open?f.N-1:f.N,off=f.off;
      for(let k=0;k<len;k++){
        const a=off+3*k,b=off+3*((k+1)%f.N);
        result.push({fil:j,seg:k,
          ax:A[a],ay:A[a+1],az:A[a+2],bx:A[b],by:A[b+1],bz:A[b+2],
          mx:(A[a]+A[b])/2,my:(A[a+1]+A[b+1])/2,mz:(A[a+2]+A[b+2])/2,
          dx:A[b]-A[a],dy:A[b+1]-A[a+1],dz:A[b+2]-A[a+2]});
      }
    }
    return result;
  }
  function addVelocity(px,py,pz,source,pref,a2,dest,o){
    for(const s of source){
      const rx=px-s.mx,ry=py-s.my,rz=pz-s.mz;
      const den=rx*rx+ry*ry+rz*rz+a2;
      const w=pref/(den*Math.sqrt(den));
      dest[o]+=(s.dy*rz-s.dz*ry)*w;
      dest[o+1]+=(s.dz*rx-s.dx*rz)*w;
      dest[o+2]+=(s.dx*ry-s.dy*rx)*w;
    }
  }
  function knotDerivative(Yk,fl,OUT){
    if(!active())return 0;
    const bg=segments(trial||X,descs,true),pref=gamm()/(4*Math.PI),a2=P.a*P.a;
    let peak=0;
    for(const f of fl){if(f.ghost)continue;for(let k=0;k<f.N;k++){
      const o=f.off+3*k;
      addVelocity(Yk[o],Yk[o+1],Yk[o+2],bg,pref,a2,OUT,o);
      peak=Math.max(peak,Math.hypot(OUT[o],OUT[o+1],OUT[o+2]));
    }}
    return peak;
  }
  function backgroundDerivative(Yk,fl,B){
    const out=new Float64Array(B.length);
    const bs=segments(B,descs,true),nonGhost=fl.filter(f=>!f.ghost);
    const ks=segments(Yk,nonGhost,false);
    const knotGroups=nonGhost.map((f,idx)=>ks.filter(s=>s.fil===idx));
    const bgPref=gamm()/(4*Math.PI),a2=P.a*P.a;
    for(const d of descs){for(let k=1;k<d.N-1;k++){
      const o=d.off+3*k,px=B[o],py=B[o+1],pz=B[o+2];
      // Consistent finite-core smoothing also for local background self-action.
      addVelocity(px,py,pz,bs,bgPref,a2,out,o);
      for(let fi=0;fi<nonGhost.length;fi++){
        addVelocity(px,py,pz,knotGroups[fi],filamentGamma(nonGhost[fi])/(4*Math.PI),a2,out,o);
      }
    }}
    return out; // endpoints are exactly pinned: derivative zero.
  }
  function advance(dt){
    // Coupled RK4: all four stages share the same instantaneous knot/background geometry.
    const b0=X.slice(),n=Y.length;
    const bK=[],kStages=[];
    const deriv=(Yk,B)=>{
      trial=B;
      const kv=new Float64Array(n);
      const speed=velAll(Yk,kv);
      const bv=backgroundDerivative(Yk,allFils(),B);
      return {kv,bv,speed:Math.max(speed,maxSpeed(bv))};
    };
    const p1=deriv(Y,b0);kStages.push(p1.kv);bK.push(p1.bv);
    const sK1=addScaled(Y,p1.kv,dt/2),sB1=addScaled(b0,p1.bv,dt/2);
    const p2=deriv(sK1,sB1);kStages.push(p2.kv);bK.push(p2.bv);
    const sK2=addScaled(Y,p2.kv,dt/2),sB2=addScaled(b0,p2.bv,dt/2);
    const p3=deriv(sK2,sB2);kStages.push(p3.kv);bK.push(p3.bv);
    const sK3=addScaled(Y,p3.kv,dt),sB3=addScaled(b0,p3.bv,dt);
    const p4=deriv(sK3,sB3);kStages.push(p4.kv);bK.push(p4.bv);
    for(let i=0;i<n;i++)Y[i]+=dt*(p1.kv[i]+2*p2.kv[i]+2*p3.kv[i]+p4.kv[i])/6;
    for(let i=0;i<X.length;i++)X[i]=b0[i]+dt*(p1.bv[i]+2*p2.bv[i]+2*p3.bv[i]+p4.bv[i])/6;
    for(const d of descs)for(const i of [d.off,d.off+3*(d.N-1)]){
      X[i]=initial[i];X[i+1]=initial[i+1];X[i+2]=initial[i+2];
    }
    K4.set(p4.kv);trial=null;fieldCache=null;
    wrapFilamentCarriersZ();enforceCenterLock();constrainGhostRing();
    return Math.max(p1.speed,p2.speed,p3.speed,p4.speed);
  }
  const addScaled=(A,V,f)=>{const z=new Float64Array(A.length);for(let i=0;i<A.length;i++)z[i]=A[i]+f*V[i];return z;};
  const maxSpeed=V=>{let max=0;for(let i=0;i<V.length;i+=3)max=Math.max(max,Math.hypot(V[i],V[i+1],V[i+2]));return max;};
  function minDistance(Yk){
    if(!active())return Infinity;
    const bs=segments(X,descs,true),ks=segments(Yk,fils.filter(f=>!f.ghost),false);
    let g2=Infinity;
    for(const a of bs){for(const b of ks){
      g2=Math.min(g2,segSegDist2(a.ax,a.ay,a.az,a.bx,a.by,a.bz,b.ax,b.ay,b.az,b.bx,b.by,b.bz));
    }}
    for(let i=0;i<bs.length;i++)for(let j=i+1;j<bs.length;j++){
      const a=bs[i],b=bs[j];if(a.fil===b.fil&&Math.abs(a.seg-b.seg)<=2)continue;
      g2=Math.min(g2,segSegDist2(a.ax,a.ay,a.az,a.bx,a.by,a.bz,b.ax,b.ay,b.az,b.bx,b.by,b.bz));
    }
    lastGap=Math.sqrt(g2);return lastGap;
  }
  function fieldVelocity(px,py,pz){
    if(!active())return {ux:0,uy:0,uz:0};
    if(!fieldCache)fieldCache=segments(X,descs,true);
    const u=new Float64Array(3);
    addVelocity(px,py,pz,fieldCache,gamm()/(4*Math.PI),P.a*P.a,u,0);
    return {ux:u[0],uy:u[1],uz:u[2]};
  }
  function allFinite(){for(const x of X)if(!Number.isFinite(x))return false;return true;}
  function contact(){
    if(!active())return null;
    if(minSegment()<Math.max(1e-12,1e-3*P.a))
      return {warn:false,msg:'⛔ P6b: ingestorte achtergrondsegmentlengte; integratie geweigerd.'};
    const gap=minDistance(Y);
    // This gate uses the same numerical a_sim, not a claimed physical core.
    if(gap<contactThresholdInfo().effective)return {warn:false,msg:'⛔ P6b: contact onder effectieve contactdrempel; geen reconnectie toegestaan.'};
    return null;
  }
  function snapshot(){if(active())before=X.slice();}
  function restore(){if(active()&&before.length===X.length){X.set(before);trial=null;fieldCache=null;}}
  function fullSnapshot(){return active()?X.slice():null;}
  function restoreFull(v){if(v&&v.length===X.length){X.set(v);trial=null;fieldCache=null;}}
  function maxDisplacementFromBefore(){return before.length===X.length?maxStateDisplacement(before,X):0;}
  function minSegment(){let m=Infinity;for(const d of descs)for(let k=0;k<d.N-1;k++){
    const a=d.off+3*k,b=a+3;m=Math.min(m,Math.hypot(X[b]-X[a],X[b+1]-X[a+1],X[b+2]-X[a+2]));
  }return m;}
  function clearVisual(){
    if(!drawGroup)return;
    for(const obj of meshes){obj.geometry.dispose();obj.material.dispose();drawGroup.remove(obj);}meshes=[];
  }
  function render(){
    if(!active()&&!drawGroup)return;
    if(!drawGroup){drawGroup=new THREE.Group();scene.add(drawGroup);}
    if(!active()){clearVisual();drawGroup.visible=false;return;}
    drawGroup.visible=true;
    if(meshes.length!==descs.length){clearVisual();for(const d of descs){
      const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(new Float32Array(3*d.N),3));
      const m=new THREE.LineBasicMaterial({color:0x43c2ee,transparent:true,opacity:0.8});
      const l=new THREE.Line(g,m);meshes.push(l);drawGroup.add(l);
    }}
    for(let i=0;i<descs.length;i++){
      const d=descs[i],arr=meshes[i].geometry.attributes.position.array;
      for(let k=0;k<3*d.N;k++)arr[k]=X[d.off+k];
      meshes[i].geometry.attributes.position.needsUpdate=true;
    }
  }
  function maxTransverseBending(){
    let max=0;
    for(let i=0;i<X.length;i+=3)max=Math.max(max,Math.hypot(X[i]-initial[i],X[i+1]-initial[i+1]));
    return max;
  }
  function report(){return {mode:cfg.mode,omega:cfg.omega,spacing:cfg.spacing,side:cfg.side,nodes:cfg.nodes,
    circulation:gamm(),filaments:descs.length,vertices:descs.length*cfg.nodes,
    gap:lastGap,maxTransverseDisplacement:maxTransverseBending(),endpointPolicy:'pinned-open-finite',modelStatus:'RESEARCH_TRACK_NOT_EULER_CERTIFIED'};}
  window.__vlDiscreteBundleAPI={configure:setConfig,getSnapshot:report,reset:setup};
  return {active,setup,advance,knotDerivative,contact,minDistance,snapshot,restore,fullSnapshot,restoreFull,fieldVelocity,isFinite:allFinite,
    maxDisplacementFromBefore,minSegment,render,report};
})();
