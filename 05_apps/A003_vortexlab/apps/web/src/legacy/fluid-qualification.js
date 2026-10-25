/* A003-v7.6.25b-m1 fluid qualification P2: passive, pure; NOT an Euler PDE solver.
   SI units; a_sim and r_core are intentionally distinct. */
(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.VortexLabFluidQualification=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const EPS=Number.EPSILON;
  function classifyCore({a,geometryScale,minimumEdge,maxCurvature=0,physicalRadius=null}={}){
    const scale=Math.max(Number.MIN_VALUE,Math.abs(Number(geometryScale)||0));
    const precisionFloor=64*EPS*scale;
    const radius=Number(a),ds=Number(minimumEdge);
    const inputValid=Number.isFinite(radius)&&radius>0;
    const edgeValid=Number.isFinite(ds)&&ds>0;
    const coreContactResolvable=inputValid&&3*radius>precisionFloor;
    const alpha=inputValid&&edgeValid?radius/ds:null;
    const curvatureProduct=inputValid&&Number.isFinite(maxCurvature)?radius*maxCurvature:null;
    // This assesses numerical applicability, NOT physical validity.
    const localInductionResolved=inputValid&&edgeValid&&ds>4*radius&&!(curvatureProduct>=0.25);
    const regime=!inputValid?'INVALID_CORE':!edgeValid?'INVALID_GEOMETRY':
      !coreContactResolvable?'SUB_PRECISION_CORE':
      !localInductionResolved?'THIN_FILAMENT_UNQUALIFIED':'CANDIDATE_ONLY';
    const rPhys=physicalRadius==null?null:Number(physicalRadius);
    return {regime,inputValid,edgeValid,a:radius,minimumEdge:ds,precisionFloor,
      physicalContactThreshold:inputValid?3*radius:null,
      effectiveContactThreshold:inputValid?Math.max(3*radius,precisionFloor):null,
      coreContactResolvable,alpha,curvatureProduct,localInductionResolved,
      physicalRadius:rPhys!=null&&Number.isFinite(rPhys)&&rPhys>0?rPhys:null,
      pressureClosure:'NOT_IMPLEMENTED',wallClosure:'NOT_IMPLEMENTED',
      status:'NUMERICAL_QUALIFICATION_ONLY'};
  }
  // P5: a fixed microsecond cutoff is NOT a numerical stability criterion.
  // Accept any finite positive CFL step that advances the IEEE-754 simulation
  // clock. Never increase dt, which would invalidate the CFL/contact limit.
  // Spatial resolution and physical-core qualification are separate gates.
  function safeStep(dt,{simTime=0,direction=1}={}){
    if(!Number.isFinite(dt)||dt<=0)return {ok:false,reason:'NONFINITE_OR_NONPOSITIVE_DT',dt};
    if(!Number.isFinite(simTime))return {ok:false,reason:'NONFINITE_SIM_TIME',dt,simTime};
    const step=(direction<0?-dt:dt);
    const nextTime=simTime+step;
    if(!Number.isFinite(nextTime)||nextTime===simTime)
      return {ok:false,reason:'TIME_RESOLUTION_EXHAUSTED',dt,simTime};
    return {ok:true,dt,simTime,nextTime};
  }
  function allFinitePositions(arr){
    if(!arr||!arr.length)return false;
    for(let k=0;k<arr.length;k++)if(!Number.isFinite(arr[k]))return false;
    return true;
  }
  function wallNormalDiagnostic(field,{radius,halfHeight,angularSamples=4}={}){
    if(typeof field!=='function'||!(radius>0)||!(halfHeight>0))return {valid:false};
    let maxAbsNormal=0,maxRelativeNormal=0,minSpeed=Infinity,n=0;
    const sample=(x,y,z,nx,ny,nz)=>{
      const v=field(x,y,z);if(!v||![v.ux,v.uy,v.uz].every(Number.isFinite))return false;
      const normal=v.ux*nx+v.uy*ny+v.uz*nz;
      const speed=Math.hypot(v.ux,v.uy,v.uz);
      maxAbsNormal=Math.max(maxAbsNormal,Math.abs(normal));
      maxRelativeNormal=Math.max(maxRelativeNormal,Math.abs(normal)/(speed+1e-300));
      minSpeed=Math.min(minSpeed,speed);n++;
      return true;
    };
    for(const z of [-0.5*halfHeight,0,0.5*halfHeight]){
      for(let i=0;i<angularSamples;i++){
        const t=2*Math.PI*i/angularSamples,nx=Math.cos(t),ny=Math.sin(t);
        if(!sample(radius*nx,radius*ny,z,nx,ny,0))return {valid:false};
      }
    }
    for(const sign of [-1,1]){
      for(const r of [0,0.5*radius]){
        if(!sample(r,0,sign*halfHeight,0,0,sign))return {valid:false};
      }
    }
    return {valid:true,samples:n,maxAbsNormal,maxRelativeNormal,minSpeed,
      qualified:false,reason:'NO_BOUNDARY_SOLVER; observational diagnostic only'};
  }
  function divergenceDiagnostic(field,{x,y,z,h}={}){
    if(typeof field!=='function'||![x,y,z,h].every(Number.isFinite)||h<=0)return {valid:false};
    const a=field(x+h,y,z),b=field(x-h,y,z),c=field(x,y+h,z),d=field(x,y-h,z),e=field(x,y,z+h),f=field(x,y,z-h);
    const values=[a.ux,b.ux,c.uy,d.uy,e.uz,f.uz];
    if(!values.every(Number.isFinite))return {valid:false};
    const value=((a.ux-b.ux)+(c.uy-d.uy)+(e.uz-f.uz))/(2*h);
    const amp=Math.max(...values.map(Math.abs));
    return {valid:Number.isFinite(value),value,normalized:Math.abs(value)*h/(amp+1e-300),h};
  }
  function coreVolumeDiagnostic({initialLength,currentLength,initialCoreRadius}={}){
    if(![initialLength,currentLength,initialCoreRadius].every(x=>Number.isFinite(x)&&x>0))return {valid:false};
    return {valid:true,initialVolume:Math.PI*initialCoreRadius**2*initialLength,
      proposedRadius:initialCoreRadius*Math.sqrt(initialLength/currentLength),
      status:'HYPOTHESIS_UNCOUPLED'};
  }
  return {classifyCore,safeStep,allFinitePositions,wallNormalDiagnostic,divergenceDiagnostic,coreVolumeDiagnostic};
});
