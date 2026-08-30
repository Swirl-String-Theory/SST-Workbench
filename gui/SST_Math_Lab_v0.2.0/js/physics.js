(function(){
const Lab=window.SSTLab,V=Lab.Vec,C=Lab.CONSTANTS,D=Lab.DERIVED;

function toPhysical(points,scale){return points.map(p=>[p[0]*scale,p[1]*scale,p[2]*scale]);}

function frames(points){
  const n=points.length,at=i=>points[(i+n)%n],T=[],N=[],B=[];
  for(let i=0;i<n;i++){
    const pm=at(i-1),p=at(i),pp=at(i+1);
    let t=V.sub(pp,pm),tn=V.norm(t); t=tn>0?V.mul(t,1/tn):[1,0,0];
    let r2=V.add(V.sub(pp,V.mul(p,2)),pm);
    let nvec=V.sub(r2,V.mul(t,V.dot(r2,t))),nn=V.norm(nvec);
    if(nn<1e-14){
      const ref=Math.abs(t[2])<0.9?[0,0,1]:[0,1,0];
      nvec=V.cross(ref,t); nn=V.norm(nvec);
    }
    nvec=V.mul(nvec,1/Math.max(nn,1e-300));
    let b=V.cross(t,nvec),bn=V.norm(b); b=V.mul(b,1/Math.max(bn,1e-300));
    T.push(t);N.push(nvec);B.push(b);
  }
  return{T,N,B};
}


function rotateAroundAxis(v,axis,angle){
  const c=Math.cos(angle),ss=Math.sin(angle);return V.add(V.add(V.mul(v,c),V.mul(V.cross(axis,v),ss)),V.mul(axis,V.dot(axis,v)*(1-c)));
}
function periodicTransportFrame(points){
  const n=points.length,T=new Array(n),Nraw=new Array(n),Braw=new Array(n),at=i=>points[(i+n)%n];
  for(let i=0;i<n;i++){let t=V.sub(at(i+1),at(i-1)),nn=V.norm(t);T[i]=nn>0?V.mul(t,1/nn):[1,0,0];}
  let ref=Math.abs(T[0][2])<0.8?[0,0,1]:[0,1,0];let n0=V.sub(ref,V.mul(T[0],V.dot(ref,T[0])));n0=V.mul(n0,1/Math.max(V.norm(n0),1e-300));Nraw[0]=n0;Braw[0]=V.cross(T[0],Nraw[0]);
  function transport(nvec,t0,t1){const ax=V.cross(t0,t1),sn=V.norm(ax),cs=Math.max(-1,Math.min(1,V.dot(t0,t1)));let out=nvec;if(sn>1e-14){out=rotateAroundAxis(nvec,V.mul(ax,1/sn),Math.atan2(sn,cs));}out=V.sub(out,V.mul(t1,V.dot(out,t1)));const q=V.norm(out);return q>1e-14?V.mul(out,1/q):nvec;}
  for(let i=0;i<n-1;i++){Nraw[i+1]=transport(Nraw[i],T[i],T[i+1]);Braw[i+1]=V.cross(T[i+1],Nraw[i+1]);}
  const nClosure=transport(Nraw[n-1],T[n-1],T[0]);
  const holonomy=Math.atan2(V.dot(T[0],V.cross(Nraw[0],nClosure)),V.dot(Nraw[0],nClosure));
  const N=new Array(n),B=new Array(n);
  for(let i=0;i<n;i++){const correction=-holonomy*i/n;N[i]=rotateAroundAxis(Nraw[i],T[i],correction);N[i]=V.mul(N[i],1/Math.max(V.norm(N[i]),1e-300));B[i]=V.cross(T[i],N[i]);B[i]=V.mul(B[i],1/Math.max(V.norm(B[i]),1e-300));}
  return{T,N,B,holonomy,Nraw,Braw};
}

// Rosenhead-Moore style regularized filament quadrature:
// v(x) = Gamma/(4 pi) sum_j [ dl_j x (x-m_j) / (|x-m_j|^2+a^2)^(3/2) ]
function sourceSegments(pointsM){
  const n=pointsM.length,mid=new Array(n),dl=new Array(n);
  for(let j=0;j<n;j++){
    const p0=pointsM[j],p1=pointsM[(j+1)%n];
    mid[j]=[(p0[0]+p1[0])/2,(p0[1]+p1[1])/2,(p0[2]+p1[2])/2];
    dl[j]=[p1[0]-p0[0],p1[1]-p0[1],p1[2]-p0[2]];
  }
  return{mid,dl};
}
function biotSavartAt(evalPointsM,sourcePointsM,coreRadius,gamma){
  if(!(coreRadius>0))throw new Error("Biot-Savart core radius must be > 0 m.");
  const {mid,dl}=sourceSegments(sourcePointsM),a2=coreRadius*coreRadius,factor=gamma/(4*Math.PI),out=new Array(evalPointsM.length);
  for(let i=0;i<evalPointsM.length;i++){
    const x=evalPointsM[i];let vx=0,vy=0,vz=0;
    for(let j=0;j<mid.length;j++){
      const rx=x[0]-mid[j][0],ry=x[1]-mid[j][1],rz=x[2]-mid[j][2],den=Math.pow(rx*rx+ry*ry+rz*rz+a2,1.5),q=factor/Math.max(den,1e-300),d=dl[j];
      vx+=(d[1]*rz-d[2]*ry)*q;vy+=(d[2]*rx-d[0]*rz)*q;vz+=(d[0]*ry-d[1]*rx)*q;
    }
    out[i]=[vx,vy,vz];
  }
  return out;
}
function biotSavartPhysical(pointsM,coreRadius,gamma){return biotSavartAt(pointsM,pointsM,coreRadius,gamma);}

function pressurePoissonProbe(pointsM,coreRadius,gamma,step){
  const n=pointsM.length,axes=[[1,0,0],[0,1,0],[0,0,1]],plus=[],minus=[];
  if(!(step>0))throw new Error("Pressure-Poisson probe step must be > 0.");
  for(let ax=0;ax<3;ax++)for(let i=0;i<n;i++){plus.push(V.add(pointsM[i],V.mul(axes[ax],step)));minus.push(V.sub(pointsM[i],V.mul(axes[ax],step)));}
  const vp=biotSavartAt(plus,pointsM,coreRadius,gamma),vm=biotSavartAt(minus,pointsM,coreRadius,gamma),source=new Array(n),divergence=new Array(n),gradientFrobenius=new Array(n);
  for(let i=0;i<n;i++){
    const G=[[0,0,0],[0,0,0],[0,0,0]]; // G[row velocity component][column spatial derivative]
    for(let ax=0;ax<3;ax++){
      const a=vp[ax*n+i],b=vm[ax*n+i];
      for(let comp=0;comp<3;comp++)G[comp][ax]=(a[comp]-b[comp])/(2*step);
    }
    let contraction=0;for(let ii=0;ii<3;ii++)for(let jj=0;jj<3;jj++)contraction+=G[jj][ii]*G[ii][jj];
    source[i]=-C.rho_f*contraction;
    divergence[i]=G[0][0]+G[1][1]+G[2][2];
    let frob2=0;for(let r=0;r<3;r++)for(let c=0;c<3;c++)frob2+=G[r][c]*G[r][c];gradientFrobenius[i]=Math.sqrt(frob2);
  }
  return{step,source,divergence,gradientFrobenius};
}

function decomposeVelocity(vel,frame){
  const vt=[],vn=[],vb=[],speed=[],shapeSpeed=[],shape=[];
  for(let i=0;i<vel.length;i++){
    const v=vel[i],t=frame.T[i],n=frame.N[i],b=frame.B[i];
    const a=V.dot(v,t),c=V.dot(v,n),d=V.dot(v,b);
    const vs=V.sub(v,V.mul(t,a));
    vt.push(a);vn.push(c);vb.push(d);speed.push(V.norm(v));shape.push(vs);shapeSpeed.push(V.norm(vs));
  }
  return{vt,vn,vb,speed,shapeSpeed,shape};
}

function centralDerivativePeriodic(values,ds){
  const n=values.length,out=new Array(n);
  for(let i=0;i<n;i++)out[i]=(values[(i+1)%n]-values[(i-1+n)%n])/(2*ds);
  return out;
}

function finiteCoreAnalysis(displayGeom,settings){
  const Np=Math.max(32,Math.min(displayGeom.points.length,Math.floor(settings.physicsSamples)));
  const physicsUnit=Lab.Geometry.uniformResampleClosed(displayGeom.points,Np);
  const pointsM=toPhysical(physicsUnit,settings.physicalScale);
  const frame=frames(pointsM);
  const transportFrame=periodicTransportFrame(pointsM);
  const coreRadius=settings.biotCoreFraction*C.r_c;
  const gamma=D.Gamma*settings.circulationMultiplier;
  const vel=biotSavartPhysical(pointsM,coreRadius,gamma);
  const dec=decomposeVelocity(vel,frame);
  const L=Lab.Geometry.closedLength(pointsM),ds=L/Np;
  const pressureDeficit=dec.speed.map(v=>0.5*C.rho_f*v*v);
  const pressureShape=dec.shapeSpeed.map(v=>0.5*C.rho_f*v*v);
  const dpds=centralDerivativePeriodic(pressureDeficit,ds);
  const pressureProbe=pressurePoissonProbe(pointsM,coreRadius,gamma,settings.pressureProbeFraction*coreRadius);
  const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
  const rms=a=>Math.sqrt(a.reduce((s,x)=>s+x*x,0)/a.length);
  const maxAbs=a=>Math.max(...a.map(Math.abs));
  return{
    pointsUnit:physicsUnit,pointsM,frame,transportFrame,frameHolonomy:transportFrame.holonomy,coreRadius,gamma,L,ds,velocity:vel,...dec,
    pressureDeficit,pressureShape,dpds,pressurePoissonSource:pressureProbe.source,divergence:pressureProbe.divergence,velocityGradientFrobenius:pressureProbe.gradientFrobenius,pressureProbeStep:pressureProbe.step,
    sNorm:Array.from({length:Np},(_,i)=>i/Np),
    stats:{
      speedMean:mean(dec.speed),speedRms:rms(dec.speed),speedMax:Math.max(...dec.speed),
      shapeMean:mean(dec.shapeSpeed),shapeMax:Math.max(...dec.shapeSpeed),
      tangentRms:rms(dec.vt),normalRms:rms(dec.vn),binormalRms:rms(dec.vb),
      pressureMin:Math.min(...pressureDeficit),pressureMax:Math.max(...pressureDeficit),
      dpdsMaxAbs:maxAbs(dpds),pressurePoissonMaxAbs:maxAbs(pressureProbe.source),divergenceRms:rms(pressureProbe.divergence),divergenceMaxAbs:maxAbs(pressureProbe.divergence),gradientRms:rms(pressureProbe.gradientFrobenius),divergenceRelativeRms:rms(pressureProbe.divergence)/Math.max(rms(pressureProbe.gradientFrobenius),1e-300)
    }
  };
}

function basisFields(physics,modes){
  const n=physics.pointsM.length,basis=[];
  for(let m=1;m<=modes;m++){
    for(const trig of ["cos","sin"]){
      for(const dir of ["N","B"]){
        const field=new Array(n);
        for(let i=0;i<n;i++){
          const ph=2*Math.PI*m*i/n,q=trig==="cos"?Math.cos(ph):Math.sin(ph),e=physics.transportFrame[dir][i];
          field[i]=V.mul(e,q);
        }
        const norm2=field.reduce((s,e)=>s+V.dot(e,e),0)/n;
        basis.push({m,trig,dir,label:`${dir}${trig==="cos"?"c":"s"}${m}`,field,norm2});
      }
    }
  }
  return basis;
}

function reducedStability(physics,settings){
  if(!window.numeric)throw new Error("numeric.js is required for the stability eigensystem.");
  const modes=Math.max(1,Math.min(12,Math.floor(settings.stabilityModes))),basis=basisFields(physics,modes),dim=basis.length,n=physics.pointsM.length;
  const baseEps=settings.perturbationFraction*physics.coreRadius;
  if(!(baseEps>0))throw new Error("Stability perturbation amplitude must be > 0.");
  function solveAt(eps){
    const A=Array.from({length:dim},()=>new Array(dim).fill(0));
    for(let a=0;a<dim;a++){
      const pertP=physics.pointsM.map((p,i)=>V.add(p,V.mul(basis[a].field[i],eps))),pertM=physics.pointsM.map((p,i)=>V.sub(p,V.mul(basis[a].field[i],eps)));
      const vp=biotSavartPhysical(pertP,physics.coreRadius,physics.gamma),vm=biotSavartPhysical(pertM,physics.coreRadius,physics.gamma);
      for(let b=0;b<dim;b++){
        let proj=0;for(let i=0;i<n;i++){const dv=V.mul(V.sub(vp[i],vm[i]),1/(2*eps));proj+=V.dot(basis[b].field[i],dv);}proj/=n;
        A[b][a]=proj/Math.max(basis[b].norm2,1e-300);
      }
    }
    const eig=numeric.eig(A),re=eig.lambda.x.slice(),im=(eig.lambda.y||new Array(re.length).fill(0)).slice();
    const eigenvalues=re.map((x,i)=>({re:x,im:im[i]||0,abs:Math.hypot(x,im[i]||0),index:i})).sort((a,b)=>b.re-a.re);
    const scale=Math.max(...eigenvalues.map(q=>Math.abs(q.re)),1),threshold=Math.max(1e-12,1e-9*scale),positiveCount=eigenvalues.filter(z=>z.re>threshold).length;
    return{epsilon:eps,A,eigenvalues,maxGrowth:eigenvalues[0]?.re??NaN,minReal:eigenvalues[eigenvalues.length-1]?.re??NaN,spectralRadius:Math.max(...eigenvalues.map(z=>z.abs)),positiveCount};
  }
  const primary=solveAt(baseEps);let convergence=null;
  if(settings.stabilityConvergence){
    const half=solveAt(baseEps/2),twice=solveAt(baseEps*2),vals=[half.maxGrowth,primary.maxGrowth,twice.maxGrowth],meanAbs=vals.reduce((q,x)=>q+Math.abs(x),0)/vals.length;
    convergence={epsilon:[half.epsilon,primary.epsilon,twice.epsilon],maxGrowth:vals,relativeSpread:(Math.max(...vals)-Math.min(...vals))/Math.max(meanAbs,1e-300)};
  }
  return{modes,basis:basis.map(({m,trig,dir,label})=>({m,trig,dir,label})),dimension:dim,epsilon:primary.epsilon,A:primary.A,eigenvalues:primary.eigenvalues,maxGrowth:primary.maxGrowth,minReal:primary.minReal,spectralRadius:primary.spectralRadius,positiveCount:primary.positiveCount,convergence,
    interpretation:"Frozen-geometry centered-difference reduced normal/binormal linearization of regularized Biot-Savart shape dynamics in a periodic transport frame; not Floquet/RPO stability."};
}

Lab.Physics={toPhysical,frames,periodicTransportFrame,biotSavartAt,biotSavartPhysical,pressurePoissonProbe,decomposeVelocity,finiteCoreAnalysis,reducedStability};
})();
