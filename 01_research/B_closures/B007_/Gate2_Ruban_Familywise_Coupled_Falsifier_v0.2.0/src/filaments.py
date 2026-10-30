"""Reduced regularized midpoint filament model; NOT the full 3D Euler PDE."""
from __future__ import annotations
import math
import numpy as np
from .geometry import total_length
from numba import njit

@njit(cache=True)
def _velocity(P,starts,ends,gammas,sig):
    V=np.zeros_like(P);ss=sig*sig
    for i in range(len(P)):
        xi,yi,zi=P[i,0],P[i,1],P[i,2]
        for j in range(len(starts)):
            rx=xi-(starts[j,0]+ends[j,0])*.5
            ry=yi-(starts[j,1]+ends[j,1])*.5
            rz=zi-(starts[j,2]+ends[j,2])*.5
            dx=ends[j,0]-starts[j,0];dy=ends[j,1]-starts[j,1];dz=ends[j,2]-starts[j,2]
            inv=gammas[j]/((rx*rx+ry*ry+rz*rz+ss)**1.5)/(4*math.pi)
            V[i,0]+=(dy*rz-dz*ry)*inv
            V[i,1]+=(dz*rx-dx*rz)*inv
            V[i,2]+=(dx*ry-dy*rx)*inv
    return V

def velocity(parts,sigma,component_gamma=None):
    if component_gamma is None:component_gamma=[1.0/len(parts)]*len(parts)
    nodes=np.concatenate(parts)
    starts=np.concatenate(parts);ends=np.concatenate([np.roll(p,-1,axis=0) for p in parts])
    gammas=np.concatenate([np.full(len(p),g) for p,g in zip(parts,component_gamma)])
    v=_velocity(np.ascontiguousarray(nodes),np.ascontiguousarray(starts),np.ascontiguousarray(ends),gammas,float(sigma))
    cuts=np.cumsum([len(p) for p in parts])[:-1]
    return list(np.split(v,cuts))

def resample(p,n):
    p=np.asarray(p,float);q=np.concatenate((p,p[:1]))
    ds=np.linalg.norm(np.diff(q,axis=0),axis=1);s=np.concatenate(([0.],np.cumsum(ds)))
    ar=np.arange(n)*s[-1]/n
    return np.column_stack([np.interp(ar,s,q[:,j]) for j in range(3)])

def fit(parts,vels):
    p=np.concatenate(parts);v=np.concatenate(vels)
    t=np.column_stack((np.tile([0.,0.,1.],(len(p),1)).ravel(),np.column_stack((-p[:,1],p[:,0],np.zeros(len(p)))).ravel()))
    a=np.linalg.lstsq(t,v.ravel(),rcond=None)[0]
    rv=(v.ravel()-t@a)
    n=np.linalg.norm(v)
    return {'U_z':float(a[0]),'Omega_z':float(a[1]),'relative_residual':float(np.linalg.norm(rv)/max(n,1e-30)),
            'rms_velocity':float(n/np.sqrt(len(p))),'rms_unfitted':float(np.linalg.norm(rv)/np.sqrt(len(p)))}

def quotient_distance(a,b):
    """Rigid 3D alignment for diagnostic shape drift, same material point labels."""
    x=np.concatenate(a);y=np.concatenate(b)
    x0=x.mean(axis=0);y0=y.mean(axis=0)
    xx=x-x0;yy=y-y0
    u,s,vt=np.linalg.svd(xx.T@yy)
    d=np.linalg.det(u@vt)
    M=u@np.diag([1,1,np.sign(d)])@vt
    return float(np.linalg.norm(xx@M-yy)/max(np.linalg.norm(xx),1e-30))

def run_pair(orig,pert,lam,points=128,steps=3,T=.015):
    sigma=math.exp(-float(lam))
    a=[resample(p,points) for p in orig]
    b=[resample(p,points) for p in pert]
    def advance(state):
        v=velocity(state,sigma)
        predicted=[x+(T/steps)*w for x,w in zip(state,v)]
        vv=velocity(predicted,sigma)
        return [x+.5*(T/steps)*(w+ww) for x,w,ww in zip(state,v,vv)]
    ao=[x.copy() for x in a];bo=[x.copy() for x in b]
    init_a=fit(a,velocity(a,sigma));init_b=fit(b,velocity(b,sigma))
    initial_pert=quotient_distance(a,b)
    for k in range(steps):
        a=advance(a);b=advance(b)
        if any(not np.isfinite(x).all() for x in a+b):raise FloatingPointError('nonfinite filament state')
    final_a=fit(a,velocity(a,sigma));final_b=fit(b,velocity(b,sigma))
    return {'init_nominal':init_a['relative_residual'],'init_perturbed':init_b['relative_residual'],
        'final_nominal':final_a['relative_residual'],'final_perturbed':final_b['relative_residual'],
        'shape_drift_nominal':quotient_distance(ao,a),'shape_drift_perturbed':quotient_distance(bo,b),
        'perturbation_amplification':float(quotient_distance(a,b)/max(initial_pert,1e-30)),
        'relative_length_drift_nominal':float((total_length(a)-total_length(ao))/total_length(ao)),
        'relative_length_drift_perturbed':float((total_length(b)-total_length(bo))/total_length(bo)),
        'filament_points':points,'steps':steps,'final_time':T,'lambda':lam,
        'filament_model':'MIDPOINT_REGULARIZED_HEUN_WITHOUT_FINITE_CORE_EULER'}

def exploratory_score(measure):
    """Registered only as ranking heuristic; never promote to stability proof."""
    return max(float(measure['init_nominal']),float(measure['init_perturbed'])) + \
           max(float(measure['shape_drift_nominal']),float(measure['shape_drift_perturbed'])) + \
           .02*max(0.,float(measure['perturbation_amplification'])-1.)
