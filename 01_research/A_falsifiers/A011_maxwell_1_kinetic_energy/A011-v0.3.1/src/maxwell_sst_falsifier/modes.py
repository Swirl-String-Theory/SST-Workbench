from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np
from .geometry import tangent_vectors

@dataclass
class ModeCandidate:
    mode_id: str
    family: str
    m: int
    phase: str
    polarization: str
    vector: np.ndarray
    roughness_lambda: float
    retained_norm: float


def _normalize(v:np.ndarray)->tuple[np.ndarray,float]:
    n=float(np.sqrt(np.sum(v*v)))
    return (v/n if n>0 else v,n)


def _rotate_about_axis(v:np.ndarray,axis:np.ndarray,angle:float)->np.ndarray:
    a=axis/(np.linalg.norm(axis)+1e-300)
    return v*math.cos(angle)+np.cross(a,v)*math.sin(angle)+a*np.dot(a,v)*(1-math.cos(angle))


def parallel_transport_frame(points:np.ndarray)->tuple[np.ndarray,np.ndarray,np.ndarray]:
    p=np.asarray(points,float); t=tangent_vectors(p,True); npts=len(p)
    axes=np.eye(3); a=axes[np.argmin(np.abs(axes@t[0]))]
    n0=a-np.dot(a,t[0])*t[0]; n0/=np.linalg.norm(n0)
    n=np.zeros_like(p); n[0]=n0
    for i in range(1,npts):
        cand=n[i-1]-np.dot(n[i-1],t[i])*t[i]
        cn=np.linalg.norm(cand)
        if cn<1e-12:
            a=axes[np.argmin(np.abs(axes@t[i]))]; cand=a-np.dot(a,t[i])*t[i]; cn=np.linalg.norm(cand)
        n[i]=cand/cn
    # Closure correction: distribute residual frame holonomy so the frame is approximately periodic.
    nend=n[-1]-np.dot(n[-1],t[0])*t[0]; nend/=np.linalg.norm(nend)
    c=float(np.clip(np.dot(nend,n[0]),-1.0,1.0)); s=float(np.dot(t[0],np.cross(nend,n[0])))
    mismatch=math.atan2(s,c)
    for i in range(npts):
        n[i]=_rotate_about_axis(n[i],t[i],mismatch*(i/(npts-1 if npts>1 else 1)))
        n[i]-=np.dot(n[i],t[i])*t[i]; n[i]/=np.linalg.norm(n[i])
    b=np.cross(t,n); b/=np.linalg.norm(b,axis=1)[:,None]
    return t,n,b


def rigid_basis(points:np.ndarray)->np.ndarray:
    p=np.asarray(points,float); q=p-p.mean(axis=0); n=len(p)
    cols=[]
    for a in np.eye(3): cols.append(np.tile(a,(n,1)).reshape(-1))
    for a in np.eye(3): cols.append(np.cross(np.tile(a,(n,1)),q).reshape(-1))
    A=np.stack(cols,axis=1)
    Q,_=np.linalg.qr(A)
    keep=np.linalg.norm(Q,axis=0)>1e-12
    return Q[:,keep]


def project_out_rigid(v:np.ndarray,Q:np.ndarray)->np.ndarray:
    x=np.asarray(v,float).reshape(-1)
    if Q.size: x=x-Q@(Q.T@x)
    return x.reshape(v.shape)


def roughness_lambda(v:np.ndarray,points:np.ndarray)->float:
    p=np.asarray(points,float); u=np.asarray(v,float)
    ds=float(np.mean(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)))
    if ds<=0: return float("nan")
    du=np.roll(u,-1,axis=0)-u
    num=float(np.sum(du*du))/(ds*ds)
    den=float(np.sum(u*u))
    return num/max(den,1e-300)


def generate_mode_candidates(points:np.ndarray,max_m:int=12)->list[ModeCandidate]:
    p=np.asarray(points,float); npts=len(p); t,n,b=parallel_transport_frame(p); Q=rigid_basis(p)
    s=np.arange(npts,dtype=float)/npts
    raw=[]
    for m in range(1,max_m+1):
        for phase,trig in (("cos",np.cos),("sin",np.sin)):
            f=trig(2*math.pi*m*s)[:,None]
            for pol,frame in (("N",n),("B",b)):
                u=frame*f
                # Keep only normal displacement and remove rigid zero directions.
                u-=np.sum(u*t,axis=1)[:,None]*t
                before=float(np.sqrt(np.sum(u*u)))
                u=project_out_rigid(u,Q)
                u-=np.sum(u*t,axis=1)[:,None]*t
                u=project_out_rigid(u,Q)
                raw.append((m,phase,pol,u,before))
    # Modified Gram-Schmidt keeps interpretable labels while avoiding double counting in projections.
    basis=[]; out=[]
    for m,phase,pol,u,before in raw:
        x=u.reshape(-1).copy()
        for q in basis: x-=q*np.dot(q,x)
        nx=float(np.linalg.norm(x))
        if nx<1e-10*max(before,1e-300): continue
        q=x/nx; basis.append(q); vv=q.reshape(npts,3)
        out.append(ModeCandidate(
            mode_id=f"kelvin_m{m:02d}_{pol}_{phase}",family="kelvin",m=m,phase=phase,polarization=pol,
            vector=vv,roughness_lambda=roughness_lambda(vv,p),retained_norm=nx/max(before,1e-300)))
    return out


def decompose_rigid_velocity(points:np.ndarray,velocity:np.ndarray)->dict:
    p=np.asarray(points,float); v=np.asarray(velocity,float); q=p-p.mean(axis=0)
    V=v.mean(axis=0); vr=v-V
    # Solve vr_i = omega x q_i = -[q_i]_x omega.
    A=np.zeros((3*len(p),3)); y=vr.reshape(-1)
    for i,(x,yq,z) in enumerate(q):
        A[3*i:3*i+3]=np.array([[0,z,-yq],[-z,0,x],[yq,-x,0]],float)
    omega,*_=np.linalg.lstsq(A,y,rcond=None)
    vrot=np.cross(np.tile(omega,(len(p),1)),q)
    vtrans=np.tile(V,(len(p),1)); residual=v-vtrans-vrot
    tot=float(np.sum(v*v)); et=float(np.sum(vtrans*vtrans)); er=float(np.sum(vrot*vrot)); es=float(np.sum(residual*residual))
    denom=max(tot,1e-300)
    return {"V":V,"omega":omega,"v_translation":vtrans,"v_rotation":vrot,"v_shape":residual,
            "translation_fraction":et/denom,"rotation_fraction":er/denom,"shape_fraction":es/denom,"total_norm2":tot}


def project_shape_modes(shape_velocity:np.ndarray,modes:list[ModeCandidate])->dict:
    x=np.asarray(shape_velocity,float).reshape(-1); norm2=float(np.dot(x,x))
    coeffs=[]
    for m in modes:
        q=m.vector.reshape(-1); c=float(np.dot(q,x)); coeffs.append((m.mode_id,c,c*c/max(norm2,1e-300)))
    coeffs.sort(key=lambda z:z[2],reverse=True)
    captured=sum(c*c for _,c,_ in coeffs)/max(norm2,1e-300)
    return {"coefficients":coeffs,"captured_fraction":float(min(max(captured,0.0),1.0)),
            "dominant_mode_id":coeffs[0][0] if coeffs else "","dominant_mode_fraction":coeffs[0][2] if coeffs else 0.0}
