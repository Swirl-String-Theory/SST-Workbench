#!/usr/bin/env node
"use strict";
// Fysica-regressie op de geëxtraheerde kern (zelfde patroon als eerdere v7.x-
// node-regressies). Veldnaam-agnostisch: draait op v7.4.2-d34 (coRot/
// bgOmegaCoupling) én op v7.5 (solverFrame/displayFrame/bgFlow).
const path = process.argv[2] || './core.cjs';
const C = require(path);
const {P, DELTA, C0, GAMMA0_SST, KAPPA_HE, velocityCore, kelvinSpeed, Gamma,
       applyMfTemp, bundleDensityAtZ, bundleVelocityAt, bundleOmegaAtZ,
       bundlePhysicalCountAtZ, zMin, zMax, effectiveW, carrierAxialDrift} = C;

const results = [];
function add(name, pass, detail){ results.push({name, pass: !!pass, detail: String(detail)}); }

const NEW_FIELDS = ('solverFrame' in P);
function setWallLab(on){
  if (NEW_FIELDS){ P.solverFrame = on ? 'lab' : 'corot'; P.bgFlow = on ? 'wall' : 'none'; }
  else { P.coRot = false; P.bgOmegaCoupling = on; }
}
function setBundleCoupling(on){
  if (NEW_FIELDS){ P.bgFlow = on ? 'bundle' : 'none'; }
  else { P.bundleFlowCoupling = on; }
}
function baseline(){
  P.mode='solo'; P.topo='ring'; P.med='he'; P.nQ=10; P.a=1.2415e-4; P.core='gp';
  P.w=0; P.vzA=0; P.vzB=0; P.lockVz=true; P.Om=0; P.revOm=false;
  P.mfTemp='0'; P.mfAlpha=0; P.mfAlphaP=0; P.vnZ=0; P.timeReverse=false;
  P.taylorOsc.enabled=false; DELTA.gp=0.615;
  P.bundleEnabled=false; P.bundleProfile='parallel'; P.bundleSplay=0.45;
  P.OmBundle=1; P.revOmBundle=false;
  if (NEW_FIELDS){ P.solverFrame='corot'; P.displayFrame='corot'; P.bgFlow='none'; }
  else { P.coRot=true; P.bgOmegaCoupling=false; P.bundleFlowCoupling=false; }
  C.setTPhys(0);
}
function ring(N,R,eps,m){
  const A=new Float64Array(3*N);
  for(let k=0;k<N;k++){const t=2*Math.PI*k/N;const r=R*(1+(eps||0)*Math.cos((m||0)*t));
    A[3*k]=r*Math.cos(t);A[3*k+1]=r*Math.sin(t);A[3*k+2]=0;}
  return A;
}
function meanRadVz(V,N){
  let rad=0,vz=0;
  for(let k=0;k<N;k++){const t=2*Math.PI*k/N;
    rad+=V[3*k]*Math.cos(t)+V[3*k+1]*Math.sin(t);vz+=V[3*k+2];}
  return [rad/N, vz/N];
}
function bufs(n){return{K1:new Float64Array(n),K2:new Float64Array(n),K3:new Float64Array(n),K4:new Float64Array(n),TT:new Float64Array(n)};}
function localRK4(Yl,fl,dt,B,opts){
  const n=Yl.length,{K1,K2,K3,K4,TT}=B,o=opts||{includeExternal:false};
  const u1=velocityCore(Yl,fl,K1,true,o);
  for(let i=0;i<n;i++)TT[i]=Yl[i]+.5*dt*K1[i];
  const u2=velocityCore(TT,fl,K2,true,o);
  for(let i=0;i<n;i++)TT[i]=Yl[i]+.5*dt*K2[i];
  const u3=velocityCore(TT,fl,K3,true,o);
  for(let i=0;i<n;i++)TT[i]=Yl[i]+dt*K3[i];
  const u4=velocityCore(TT,fl,K4,true,o);
  for(let i=0;i<n;i++)Yl[i]+=dt/6*(K1[i]+2*K2[i]+2*K3[i]+K4[i]);
  return Math.max(u1,u2,u3,u4);
}
function localDt(Yl,N,umax){
  let lmin=1e9;
  for(let k=0;k<N;k++){const k2=(k+1)%N;
    lmin=Math.min(lmin,Math.hypot(Yl[3*k2]-Yl[3*k],Yl[3*k2+1]-Yl[3*k+1],Yl[3*k2+2]-Yl[3*k+2]));}
  const nu=Math.abs(Gamma())/(4*Math.PI)*(Math.log(2*lmin/(Math.exp(DELTA[P.core])*P.a))+C0);
  let dt=0.5/(Math.abs(nu)*Math.pow(Math.PI/lmin,2));
  if(umax>0)dt=Math.min(dt,0.25*lmin/umax);
  return dt;
}

// ---------- T1: Kelvin-snelheid, drie kernen, N=256 ----------
baseline();
for(const core of ['hol','vast','gp']){
  P.core=core;
  const N=256,R=0.07,fl=[{off:0,N,carrier:'A'}];
  const Yl=ring(N,R),V=new Float64Array(3*N);
  velocityCore(Yl,fl,V,false,{includeExternal:false});
  const err=Math.abs(meanRadVz(V,N)[1]-kelvinSpeed(R))/kelvinSpeed(R);
  add('T1 Kelvin core='+core+' (N=256)', err<5e-4, 'relfout='+err.toExponential(2));
}
P.core='gp';

// ---------- T1b: N-sweep 96/192/384 (v7.4b spec §B.5) ----------
{
  const R=0.07,errs=[];
  for(const N of [96,192,384]){
    const fl=[{off:0,N,carrier:'A'}];
    const Yl=ring(N,R),V=new Float64Array(3*N);
    velocityCore(Yl,fl,V,false,{includeExternal:false});
    errs.push(Math.abs(meanRadVz(V,N)[1]-kelvinSpeed(R))/kelvinSpeed(R));
  }
  // spiegel van de in-browser T1b: monotone zelfconvergentie tegen een
  // N=1536-referentie (de fout t.o.v. Kelvin stuit op de C0-kalibratievloer,
  // gemeten offset U_inf vs Kelvin ~ -7.6e-5) + de spec-drempel vs Kelvin.
  const fl=[{off:0,N:1536,carrier:'A'}];
  const Yr=ring(1536,R),Vr=new Float64Array(3*1536);
  velocityCore(Yr,fl,Vr,false,{includeExternal:false});
  const Uref=meanRadVz(Vr,1536)[1],K=kelvinSpeed(R);
  const Us=[96,192,384].map((N,i)=>K*(1-errs[i]*Math.sign(1)));
  // herbereken U's expliciet (errs was |U-K|/K; teken kwijt) — doe het opnieuw:
  const Uexp=[96,192,384].map(N=>{const f2=[{off:0,N,carrier:'A'}],Y2=ring(N,R),V2=new Float64Array(3*N);
    velocityCore(Y2,f2,V2,false,{includeExternal:false});return meanRadVz(V2,N)[1];});
  const es=Uexp.map(U=>Math.abs(U-Uref)/K);
  const eK=Math.abs(Uexp[2]-K)/K;
  add('T1b N-sweep (monotoon vs N=1536-ref; N=384 vs Kelvin <1e-4)',
      es[0]>es[1]&&es[1]>es[2]&&eK<1e-4,
      'zelfconv='+es.map(e=>e.toExponential(2)).join(' / ')+' · vsKelvin(384)='+eK.toExponential(2));
}

// ---------- T6: wrijvingsidentiteiten ----------
{
  const N=96,R=0.07,fl=[{off:0,N,carrier:'A'}],Yl=ring(N,R),V=new Float64Array(3*N);
  velocityCore(Yl,fl,V,false,{});
  const U0=meanRadVz(V,N)[1];
  applyMfTemp('1.90');
  velocityCore(Yl,fl,V,false,{});
  const [rad,vz]=meanRadVz(V,N);
  const eR=Math.abs(rad+P.mfAlpha*U0)/Math.abs(P.mfAlpha*U0);
  const eU=Math.abs(vz-(1-P.mfAlphaP)*U0)/Math.abs(U0);
  applyMfTemp('0');
  add('T6 wrijving Ṙ=−αU en (1−α′)U', eR<1e-10&&eU<1e-10, 'εR='+eR.toExponential(1)+' εU='+eU.toExponential(1));
}

// ---------- B3: ghost-ontkoppeling ----------
{
  const N=96,R=0.07;
  const Y1=ring(N,R),V1=new Float64Array(3*N);
  velocityCore(Y1,[{off:0,N,carrier:'A'}],V1,false,{});
  const Y2=new Float64Array(6*N);Y2.set(Y1,0);
  const gh=ring(N,0.12);for(let i=0;i<3*N;i++)Y2[3*N+i]=gh[i];
  const V2=new Float64Array(6*N);
  velocityCore(Y2,[{off:0,N,carrier:'A'},{off:3*N,N,ghost:true,gammaVal:7}],V2,false,{});
  let eq=true,ghZero=true;
  for(let i=0;i<3*N;i++){if(V1[i]!==V2[i])eq=false;}
  for(let i=3*N;i<6*N;i++){if(V2[i]!==0)ghZero=false;}
  add('B3 ghost is geen bron en beweegt niet', eq&&ghZero, 'bron-identiek='+eq+' ghost-stil='+ghZero);
}

// ---------- B1: modusscheiding ----------
{
  P.w=0.02;P.mode='botsing';const wBots=effectiveW();
  P.mode='solo';const wSolo=effectiveW();
  P.vzA=0.03;P.mode='solo';const dSolo=carrierAxialDrift('A');
  P.mode='botsing';const dBots=carrierAxialDrift('A');
  P.w=0;P.vzA=0;P.mode='solo';
  add('B1 modusscheiding w/vz', wBots===0&&wSolo===0.02&&dSolo===0&&dBots===0.03,
      'w(bots)='+wBots+' w(solo)='+wSolo+' vzA(solo)='+dSolo+' vzA(bots)='+dBots);
}

// ---------- wall-advectie-predicaat ----------
{
  baseline();
  P.Om=0.9;
  const N=64,R=0.07,fl=[{off:0,N,carrier:'A'}],Yl=ring(N,R);
  const Voff=new Float64Array(3*N),Von=new Float64Array(3*N);
  setWallLab(false); velocityCore(Yl,fl,Voff,true,{includeExternal:true});
  setWallLab(true);  velocityCore(Yl,fl,Von,true,{includeExternal:true});
  // verwacht verschil exact Ω×r op elk knooppunt
  let ok=true,worst=0;
  for(let k=0;k<N;k++){
    const ex=-P.Om*Yl[3*k+1],ey=P.Om*Yl[3*k];
    worst=Math.max(worst,Math.abs(Von[3*k]-Voff[3*k]-ex),Math.abs(Von[3*k+1]-Voff[3*k+1]-ey),Math.abs(Von[3*k+2]-Voff[3*k+2]));
  }
  ok=worst<1e-14;
  add('Wall-advectie exact Ω×r bij lab+wall, afwezig anders', ok, 'max|Δ−Ω×r|='+worst.toExponential(2));
  if(NEW_FIELDS){
    // corot+wall en lab+none mogen géén term geven
    const Va=new Float64Array(3*N),Vb=new Float64Array(3*N);
    P.solverFrame='corot';P.bgFlow='wall';  velocityCore(Yl,fl,Va,true,{includeExternal:true});
    P.solverFrame='lab';  P.bgFlow='none';  velocityCore(Yl,fl,Vb,true,{includeExternal:true});
    let same=true;
    for(let i=0;i<3*N;i++){if(Va[i]!==Voff[i]||Vb[i]!==Voff[i])same=false;}
    add('T9b-uitbreiding: corot+wall en lab+none termloos', same, 'identiek aan none='+same);
  }
  baseline();
}

// ---------- bundel: T9a-flux + predicaat ----------
{
  baseline();
  P.med='sst';P.bundleEnabled=true;P.bundleProfile='parallel';P.bundleSplay=0;P.OmBundle=1;P.revOmBundle=false;
  const nv=bundleDensityAtZ(0), nvExpected=2/GAMMA0_SST;
  add('T9a bundelflux (parallel)', Math.abs(nv/nvExpected-1)<1e-12, 'n_v='+nv.toExponential(9));
  P.bundleProfile='splay';P.bundleSplay=0.8;
  const Nb=bundlePhysicalCountAtZ(zMin()),Nm=bundlePhysicalCountAtZ(0),Nt=bundlePhysicalCountAtZ(zMax());
  add('T9a fluxbehoud (splay)', Math.max(Math.abs(Nb/Nm-1),Math.abs(Nt/Nm-1))<1e-12,
      'N-/N0/N+='+Nb.toExponential(6)+'/'+Nm.toExponential(6)+'/'+Nt.toExponential(6));
  P.bundleProfile='parallel';
  setBundleCoupling(false);
  const off=bundleVelocityAt(0.1,0.05,0);
  setBundleCoupling(true);
  const on=bundleVelocityAt(0.1,0.05,0);
  add('Bundelveld alleen bij koppeling', off.ux===0&&off.uy===0&&Math.abs(on.uy)>0,
      'uit=('+off.ux+','+off.uy+') aan=('+on.ux.toExponential(2)+','+on.uy.toExponential(2)+')');
  baseline();
}

// ---------- T5: round-trip 4e-orde ----------
{
  baseline();
  const N=96,fl=[{off:0,N,carrier:'A'}];
  function rt(dt,n){
    const Y0=ring(N,0.07,0.05,5),Yl=Y0.slice(),B=bufs(3*N);
    for(let i=0;i<n;i++)localRK4(Yl,fl,dt,B);
    for(let i=0;i<n;i++)localRK4(Yl,fl,-dt,B);
    let e=0,r=0;for(let i=0;i<Yl.length;i++){e+=(Yl[i]-Y0[i])**2;r+=Y0[i]**2;}
    return Math.sqrt(e/r);
  }
  const Yt=ring(N,0.07,0.05,5),dt0=0.5*localDt(Yt,N,0);
  const e1=rt(dt0,16),e2=rt(dt0/2,32),ratio=e1/Math.max(e2,1e-300);
  add('T5 round-trip 4e-orde (ratio≈16)', ratio>8, 'ratio='+ratio.toFixed(1)+' ε='+e1.toExponential(2));
}

// ---------- T8: frame-equivalentie (meting) ----------
{
  baseline();
  const N=96,R=0.07,fl=[{off:0,N,carrier:'A'}];
  const om=0.7, steps=24;
  P.Om=om;P.revOm=false;
  const Y0=ring(N,R,0.05,5);
  const dt=Math.min(0.5*localDt(Y0,N,0), 0.05/om);
  function runFrame(lab){
    setWallLab(lab);
    const Yl=Y0.slice(),B=bufs(3*N);
    for(let i=0;i<steps;i++)localRK4(Yl,fl,dt,B,{includeExternal:true});
    return Yl;
  }
  const Ylab=runFrame(true), Ycor=runFrame(false);
  const ph=om*dt*steps, c=Math.cos(ph), s=Math.sin(ph);
  let emax=0;
  for(let k=0;k<N;k++){
    const x=Ycor[3*k],y=Ycor[3*k+1];
    const rx=c*x-s*y, ry=s*x+c*y, rz=Ycor[3*k+2];
    emax=Math.max(emax, Math.hypot(rx-Ylab[3*k], ry-Ylab[3*k+1], rz-Ylab[3*k+2]));
  }
  const E=emax/R;
  add('T8 frame-equivalentie E_frame<1e-6', E<1e-6, 'E_frame='+E.toExponential(2)+' φ='+ph.toFixed(3)+' rad, dt='+dt.toExponential(2));
  baseline();
}

// ---------- rapport ----------
const pass = results.every(r=>r.pass);
for(const r of results)console.log((r.pass?'PASS':'FAIL')+'  '+r.name+'  —  '+r.detail);
console.log(pass?'\nREGRESSIE GROEN':'\nREGRESSIE ROOD');
process.exit(pass?0:1);
