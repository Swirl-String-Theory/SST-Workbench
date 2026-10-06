from __future__ import annotations
import numpy as np
from .blind_geometry import close_curve, resample_closed_curve, pairwise_link_matrix

FOUR_PI=4.0*np.pi


def _all_segments(components, gammas):
    mids=[]; dls=[]; gs=[]
    for c,g in zip(components,gammas):
        x=close_curve(c); y=np.roll(x,-1,axis=0)
        mids.append(0.5*(x+y)); dls.append(y-x); gs.append(np.full(len(x),float(g)))
    return np.vstack(mids),np.vstack(dls),np.concatenate(gs)


def induced_velocity(targets, components, gammas, core):
    targets=np.asarray(targets,float)
    mids,dls,gs=_all_segments(components,gammas)
    try:
        from . import _native
        return np.asarray(_native.induced_velocity(targets,mids,dls,gs,float(core)))
    except ImportError:
        pass
    out=np.zeros_like(targets)
    # Batch target dimension to bound memory.
    for s in range(0,len(targets),128):
        t=targets[s:s+128]
        r=t[:,None,:]-mids[None,:,:]
        den=(np.einsum('ijk,ijk->ij',r,r)+core*core)**1.5
        cr=np.cross(dls[None,:,:],r)
        out[s:s+128]=np.sum((gs[None,:,None]*cr)/den[:,:,None],axis=1)/FOUR_PI
    return out

def backend_name():
    try:
        from . import _native
        return 'cpp_pybind11_openmp' if bool(getattr(_native,'openmp_enabled',False)) else 'cpp_pybind11'
    except ImportError:
        return 'numpy_reference'


def velocities_on_components(components,gammas,core,cross=True):
    out=[]
    if cross:
        for c in components:
            out.append(induced_velocity(c,components,gammas,core))
    else:
        for c,g in zip(components,gammas):
            out.append(induced_velocity(c,[c],[g],core))
    return out


def relative_equilibrium_residual(components, velocities):
    x=np.vstack(components); u=np.vstack(velocities); xc=x.mean(axis=0); r=x-xc
    A=np.zeros((3*len(x),6)); b=u.reshape(-1)
    for i,(rx,ry,rz) in enumerate(r):
        # u = V + Omega x r
        M=np.array([[0,rz,-ry],[-rz,0,rx],[ry,-rx,0]],float)
        A[3*i:3*i+3,:3]=np.eye(3); A[3*i:3*i+3,3:]=M
    q,*_=np.linalg.lstsq(A,b,rcond=None)
    fit=(A@q).reshape(-1,3)
    rms=np.sqrt(np.mean(np.sum((u-fit)**2,axis=1)))
    scale=np.sqrt(np.mean(np.sum(u*u,axis=1)))
    return float(rms/max(scale,1e-15)), q[:3], q[3:]


def radius_of_gyration(components):
    x=np.vstack(components); c=x.mean(axis=0)
    return float(np.sqrt(np.mean(np.sum((x-c)**2,axis=1))))


def fibonacci_sphere(n=96):
    i=np.arange(n); phi=(1+5**0.5)/2
    z=1-2*(i+0.5)/n; rr=np.sqrt(np.maximum(0,1-z*z)); a=2*np.pi*i/phi
    return np.c_[rr*np.cos(a),rr*np.sin(a),z]


def farfield_anisotropy(components,gammas,core,radius_factor=6.0,n_dir=96,directions=None):
    x=np.vstack(components); ctr=x.mean(axis=0); Rg=radius_of_gyration(components)
    dirs=fibonacci_sphere(n_dir) if directions is None else np.asarray(directions,float)
    targets=ctr+radius_factor*Rg*dirs
    u=induced_velocity(targets,components,gammas,core)
    q=np.einsum('ij,ij->i',u,u)
    mean=float(q.mean())
    return float(q.std()/max(abs(mean),1e-20)),mean


def _state_to_components(Y,sizes):
    out=[]; o=0
    for n in sizes:
        out.append(Y[o:o+n]); o+=n
    return out


def _rhs(Y,sizes,gammas,core):
    comps=_state_to_components(Y,sizes)
    return np.vstack(velocities_on_components(comps,gammas,core,True))


def rk4(components,gammas,core,dt,steps):
    sizes=[len(c) for c in components]; Y=np.vstack(components).copy()
    for _ in range(steps):
        k1=_rhs(Y,sizes,gammas,core)
        k2=_rhs(Y+0.5*dt*k1,sizes,gammas,core)
        k3=_rhs(Y+0.5*dt*k2,sizes,gammas,core)
        k4=_rhs(Y+dt*k3,sizes,gammas,core)
        Y += dt*(k1+2*k2+2*k3+k4)/6.0
        if not np.isfinite(Y).all():
            raise FloatingPointError("non-finite RK4 state")
    return _state_to_components(Y,sizes)


def kabsch_rms(reference,current):
    X=np.vstack(reference); Y=np.vstack(current)
    Xc=X-X.mean(0); Yc=Y-Y.mean(0)
    U,S,Vt=np.linalg.svd(Yc.T@Xc); R=U@Vt
    if np.linalg.det(R)<0:
        U[:,-1]*=-1; R=U@Vt
    Ya=Yc@R
    rms=np.sqrt(np.mean(np.sum((Ya-Xc)**2,axis=1)))
    rg=np.sqrt(np.mean(np.sum(Xc*Xc,axis=1)))
    return float(rms/max(rg,1e-15))


def topology_drift(initial,final):
    if len(initial)<2: return 0.0
    A=pairwise_link_matrix(initial); B=pairwise_link_matrix(final)
    return float(np.max(np.abs(A-B)))


def circulation_vector(ncomp, sector):
    if ncomp!=3:
        raise ValueError("A054 v0.1 circulation ensemble is preregistered for exactly 3 components")
    signs={
      "Q0":np.array([ 1., 1., 1.]), "Q1":np.array([-1., 1., 1.]),
      "Q2":np.array([ 1.,-1., 1.]), "Q3":np.array([ 1., 1.,-1.]),
      "Q4":np.array([ 1., 1., 1.]), "Q5":np.array([-1., 1., 1.]),
      "Q6":np.array([ 1.,-1., 1.]), "Q7":np.array([ 1., 1.,-1.]),
    }
    # Backward-compatible aliases used by unit tests / early smoke data.
    if sector=="S0": return np.ones(3,float)
    if sector=="S1": return np.ones(3,float)/3.0
    if sector not in signs: raise ValueError(sector)
    g=signs[sector]
    return g if sector in {"Q0","Q1","Q2","Q3"} else g/3.0


def evaluate_static(components,core_ratio,sector,far_dirs=None):
    L=sum(np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1).sum() for c in components)
    core=core_ratio*L
    gammas=circulation_vector(len(components),sector)
    vel=velocities_on_components(components,gammas,core,True)
    rel,trans,omega=relative_equilibrium_residual(components,vel)
    selfvel=velocities_on_components(components,gammas,core,False)
    rel_self,_,_=relative_equilibrium_residual(components,selfvel)
    ani3,_=farfield_anisotropy(components,gammas,core,3.0,directions=far_dirs)
    ani6,_=farfield_anisotropy(components,gammas,core,6.0,directions=far_dirs)
    return {"rel_eq_residual":rel,"cross_stabilization":rel_self-rel,
            "farfield_anisotropy_r3":ani3,"farfield_anisotropy_r6":ani6,
            "fit_translation_norm":float(np.linalg.norm(trans)),
            "fit_rotation_norm":float(np.linalg.norm(omega)),"core":core}


def evaluate_dynamic(components,core_ratio,sector,dt,steps):
    L=sum(np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1).sum() for c in components)
    core=core_ratio*L; gammas=circulation_vector(len(components),sector)
    fin=rk4(components,gammas,core,dt,steps)
    return {"shape_drift":kabsch_rms(components,fin),
            "linking_drift_max":topology_drift(components,fin),
            "finite":bool(all(np.isfinite(c).all() for c in fin))},fin
