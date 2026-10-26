/* A003 P7 — ideal reference + MATERIAL (node-label) stretching diagnostics.
 * Diagnostic only. Neither a_sim nor Γ nor the Euler/Biot–Savart solver is changed.
 * SI inputs/outputs; reference core r_c is a hypothesis, not measured thickness.
 */
'use strict';
(function(root, factory) {
  const api=factory();
  if(typeof module==='object' && module.exports)module.exports=api;
  if(root)root.VLModelAIdealStretch=api;
})(typeof globalThis!=='undefined'?globalThis:undefined,function(){
  const RC=1.40897017e-15;
  const ID='A003-TwistFlow-P7-IdealReferenceStretch-v0.7.1';
  let state=null;
  function finitePositive(n){return Number.isFinite(n)&&n>0;}
  function analyze(points){
    const a=points;
    if(!a||a.length<12||a.length%3!==0)throw Error('Model A: invalid closed polygon array');
    const n=a.length/3;
    let cx=0,cy=0,cz=0,xmin=Infinity,ymin=Infinity,zmin=Infinity,xmax=-Infinity,ymax=-Infinity,zmax=-Infinity;
    for(let i=0;i<n;i++){
      const x=a[3*i],y=a[3*i+1],z=a[3*i+2];
      if(![x,y,z].every(Number.isFinite))throw Error('Model A: nonfinite polygon');
      cx+=x;cy+=y;cz+=z;
      xmin=Math.min(xmin,x);ymin=Math.min(ymin,y);zmin=Math.min(zmin,z);
      xmax=Math.max(xmax,x);ymax=Math.max(ymax,y);zmax=Math.max(zmax,z);
    }
    cx/=n;cy/=n;cz/=n;
    let rxy=0,r3=0,L=0;const edges=new Float64Array(n);
    for(let i=0;i<n;i++){
      const j=(i+1)%n, x=a[3*i]-cx,y=a[3*i+1]-cy,z=a[3*i+2]-cz;
      const edge=Math.hypot(a[3*j]-a[3*i],a[3*j+1]-a[3*i+1],a[3*j+2]-a[3*i+2]);
      if(!finitePositive(edge))throw Error('Model A: degenerate material segment');
      edges[i]=edge;L+=edge;rxy=Math.max(rxy,Math.hypot(x,y));r3=Math.max(r3,Math.hypot(x,y,z));
    }
    return {n,L,edges,rxy,r3,span:[xmax-xmin,ymax-ymin,zmax-zmin]};
  }
  function clear(reason='OFF'){state={status:reason,version:ID,coreHypothesisMeters:RC};return snapshot();}
  function reset({points,source,metadata,previewN=0,solo=true,autoRelax=false}={}){
    const eligible=source==='ideal'&&metadata?.ideal===true&&solo&&previewN===0&&!autoRelax&&
      finitePositive(Number(metadata.L))&&finitePositive(Number(metadata.D))&&Number(metadata.componentCount)===1;
    if(!eligible)return clear('NOT_ELIGIBLE_IDEAL_ONLY');
    try {
      const geom=analyze(points);
      const ropelength=Number(metadata.L)/Number(metadata.D);
      const physL0=2*RC*ropelength;
      const scale=physL0/geom.L;
      if(!finitePositive(scale))return clear('INVALID_REFERENCE_SCALE');
      state={status:'REFERENCE_ONLY',version:ID,knotId:String(metadata.knotId||''),source,
        coreHypothesisMeters:RC,referenceRopelength:ropelength,sourceDiameter:Number(metadata.D),
        referenceContourMeters:physL0,simReferenceLengthMeters:geom.L,physicalPerSimMeter:scale,
        referenceXYRadiusMeters:geom.rxy*scale, referencePoints:geom.n,
        referenceEdges:geom.edges,steps:0,last:null};
      // At reset the derived radius is exactly r_c and no dynamic step is invented.
      return observe(points,{acceptedStep:false});
    }catch(e){return clear('INVALID_REFERENCE_GEOMETRY: '+String(e.message||e));}
  }
  function observe(points,{acceptedStep=true}={}){
    if(!state?.referenceEdges)return snapshot();
    try {
      const geom=analyze(points);
      if(geom.n!==state.referencePoints)return clear('MATERIAL_LABELS_CHANGED_N');
      const lambda=geom.L/state.simReferenceLengthMeters;
      if(!finitePositive(lambda))return clear('INVALID_STRETCH');
      let minA=Infinity,maxA=0,minLambda=Infinity,maxLambda=0;
      let volume=0,localCurvatureWarning=false;
      for(let i=0;i<geom.n;i++){
        const l0=state.referenceEdges[i],l=geom.edges[i];
        const localLambda=l/l0;
        if(!finitePositive(localLambda))return clear('INVALID_SEGMENT_STRETCH');
        const ai=RC/Math.sqrt(localLambda);
        minA=Math.min(minA,ai);maxA=Math.max(maxA,ai);
        minLambda=Math.min(minLambda,localLambda);maxLambda=Math.max(maxLambda,localLambda);
        volume+=Math.PI*ai*ai*l*state.physicalPerSimMeter;
      }
      const refVolume=Math.PI*RC*RC*state.referenceContourMeters;
      if(acceptedStep)state.steps++;
      state.last={
        lambda,contourMeters:geom.L*state.physicalPerSimMeter,
        meanCoreMeters:RC/Math.sqrt(lambda),minCoreMeters:minA,maxCoreMeters:maxA,
        minimumSegmentStretch:minLambda,maximumSegmentStretch:maxLambda,
        xyRadiusMeters:geom.rxy*state.physicalPerSimMeter,
        threeDRadiusMeters:geom.r3*state.physicalPerSimMeter,
        centerlineSpansMeters:geom.span.map(v=>v*state.physicalPerSimMeter),
        volumeMetersCubed:volume,referenceVolumeMetersCubed:refVolume,
        volumeRelativeError:Math.abs(volume-refVolume)/refVolume,
        tubeGeometryStatus:lambda<1-1e-8 ? 'CONTRACTION_BELOW_IDEAL_REFERENCE_REQUIRES_REACH_AUDIT' : 'REACH_NOT_VERIFIED',
        pointCount:geom.n
      };
      return snapshot();
    }catch(e){return clear('INVALID_EVOLVED_GEOMETRY: '+String(e.message||e));}
  }

  /** Read-only radius samples at equal arclength positions along the displayed
   *  closed centerline, in VortexLab *scene* meters. Refusal is explicit when
   *  ideal material node labels have been changed by resampling/preview.
   *  This never updates physical state, a_sim, Gamma or the solver geometry.
   */
  function tubeProfile(points, rings){
    if(state?.status!=='REFERENCE_ONLY'||!state.referenceEdges) return null;
    const geom=analyze(points), n=geom.n;
    if(n!==state.referencePoints)return null;
    const count=Number.isInteger(rings)&&rings>=4?rings:n;
    const ref=state.referenceEdges;
    const initialRadiusScene=state.simReferenceLengthMeters/(2*state.referenceRopelength);
    if(!finitePositive(initialRadiusScene))return null;
    const atNode=new Float64Array(n+1);
    let min=Infinity,max=0;
    for(let i=0;i<n;i++){
      const prev=(i+n-1)%n;
      const current=initialRadiusScene/Math.sqrt(geom.edges[i]/ref[i]);
      const previous=initialRadiusScene/Math.sqrt(geom.edges[prev]/ref[prev]);
      atNode[i]=0.5*(current+previous);
      if(!finitePositive(atNode[i]))return null;
      min=Math.min(min,atNode[i]);max=Math.max(max,atNode[i]);
    }
    atNode[n]=atNode[0];
    const samples=new Float64Array(count+1);
    let k=0,dist=0;
    for(let j=0;j<=count;j++){
      const target=(j/count)*geom.L;
      while(k<n-1&&dist+geom.edges[k]<target){dist+=geom.edges[k];k++;}
      const t=Math.max(0,Math.min(1,(target-dist)/geom.edges[k]));
      samples[j]=atNode[k]*(1-t)+atNode[k+1]*t;
    }
    return {source:'IDEAL_L_OVER_ROPELENGTH',radiiScene:samples,
      referenceRopelength:state.referenceRopelength,
      referenceDiameterScene:2*initialRadiusScene,
      diameterSceneMean:2*initialRadiusScene/Math.sqrt(geom.L/state.simReferenceLengthMeters),
      minRadiusScene:min,maxRadiusScene:max,
      label:'geometrisch/materieel, visualisatie — geen a_sim-sluiting'};
  }
  function snapshot(){
    if(!state)return {version:ID,status:'UNINITIALIZED',coreHypothesisMeters:RC};
    const {referenceEdges,last,...rest}=state;
    return {...rest,...(last||{})};
  }
  clear();
  return Object.freeze({version:ID,RC,analyze,reset,observe,tubeProfile,clear,snapshot});
});
