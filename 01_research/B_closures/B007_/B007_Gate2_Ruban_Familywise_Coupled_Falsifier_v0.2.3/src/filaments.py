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

def vertex_arclength_weights(parts):
    """Closed-curve trapezoidal arclength quadrature; each component keeps its physical length."""
    weights=[]
    for part in parts:
        prev=np.linalg.norm(part-np.roll(part,1,axis=0),axis=1)
        nxt=np.linalg.norm(np.roll(part,-1,axis=0)-part,axis=1)
        weights.append(.5*(prev+nxt))
    return np.concatenate(weights)

def fit(parts,vels,mode='axial',weighting='vertex'):
    """Weighted least-squares velocity residual against permitted rigid-motion fields.

    Free-space SE(3): V = U + Omega x (x - xc), weighted centroid xc.
    Axial legacy comparator: V = Uz ez + Omegaz(ez x x), fixed z-axis.
    This is a velocity *projection*, not a stationary Euler solution.
    """
    if mode not in ('axial','free'):raise ValueError('fit mode must be axial or free')
    if weighting not in ('vertex','arclength'):raise ValueError('weighting must be vertex or arclength')
    if len(parts)!=len(vels) or not parts:raise ValueError('inconsistent component shapes')
    p=np.concatenate(parts);v=np.concatenate(vels)
    if p.shape!=v.shape or p.ndim!=2 or p.shape[1]!=3:raise ValueError('velocity shape mismatch')
    w=np.ones(len(p)) if weighting=='vertex' else vertex_arclength_weights(parts)
    if not np.isfinite(w).all() or np.min(w)<=0:raise ValueError('degenerate filament edges')
    cen=np.average(p,axis=0,weights=w);r=p-cen
    if mode=='axial':
        A=np.column_stack((np.tile([0.,0.,1.],(len(p),1)).ravel(),
                           np.column_stack((-p[:,1],p[:,0],np.zeros(len(p)))).ravel()))
    else:
        A=np.zeros((3*len(p),6),dtype=float)
        A[0::3,0]=1;A[1::3,1]=1;A[2::3,2]=1
        A[0::3,4]=r[:,2];A[0::3,5]=-r[:,1]
        A[1::3,3]=-r[:,2];A[1::3,5]=r[:,0]
        A[2::3,3]=r[:,1];A[2::3,4]=-r[:,0]
    sw=np.repeat(np.sqrt(w),3);Aw=A*sw[:,None];vw=v.ravel()*sw
    coeff,_,rank,sing=np.linalg.lstsq(Aw,vw,rcond=None)
    dv=(v.ravel()-A@coeff).reshape(-1,3)
    vn=float(np.sum(w*np.sum(v*v,axis=1)))
    rn=float(np.sum(w*np.sum(dv*dv,axis=1)))
    ratio=float(np.sqrt(rn/max(vn,1e-60)))
    out={'fit_mode':mode,'fit_weighting':weighting,'fit_rank':int(rank),
         'fit_dof':int(A.shape[1]),'rank_deficient':bool(rank<A.shape[1]),
         'condition_number':float(sing[0]/sing[-1]) if sing[-1]>0 else None,
         'relative_residual':ratio,
         'rms_velocity':float(np.sqrt(vn/w.sum())),
         'rms_unfitted':float(np.sqrt(rn/w.sum())),
         'weighted_center':cen.tolist()}
    if mode=='axial':
        out.update(U_z=float(coeff[0]),Omega_z=float(coeff[1]))
    else:
        out.update(U_vector=[float(x) for x in coeff[:3]],
                   Omega_vector=[float(x) for x in coeff[3:]])
    return out

def quotient_distance(a,b):
    """Rigid 3D alignment for diagnostic shape drift, same material point labels."""
    x=np.concatenate(a);y=np.concatenate(b)
    x0=x.mean(axis=0);y0=y.mean(axis=0)
    xx=x-x0;yy=y-y0
    u,s,vt=np.linalg.svd(xx.T@yy)
    d=np.linalg.det(u@vt)
    M=u@np.diag([1,1,np.sign(d)])@vt
    return float(np.linalg.norm(xx@M-yy)/max(np.linalg.norm(xx),1e-30))

def run_pair(orig,pert,lam,points=128,steps=3,T=.015,component_gamma=None,
             fit_mode='free',fit_weighting='arclength'):
    """Paired reduced-filament evolution; free and axial fits use IDENTICAL weights."""
    if fit_mode not in ('free','axial','compare'):raise ValueError('unknown fit mode')
    sigma=math.exp(-float(lam))
    a=[resample(p,points) for p in orig]
    b=[resample(p,points) for p in pert]
    def advance(state):
        v=velocity(state,sigma,component_gamma)
        predicted=[x+(T/steps)*w for x,w in zip(state,v)]
        vv=velocity(predicted,sigma,component_gamma)
        return [x+.5*(T/steps)*(w+ww) for x,w,ww in zip(state,v,vv)]
    ao=[x.copy() for x in a];bo=[x.copy() for x in b]
    # 'compare' ranks using the less restrictive free-space fit; retains axial diagnostics.
    preferred='free' if fit_mode=='compare' else fit_mode
    va=velocity(a,sigma,component_gamma);vb=velocity(b,sigma,component_gamma)
    init_a=fit(a,va,preferred,fit_weighting);init_b=fit(b,vb,preferred,fit_weighting)
    ax_a=fit(a,va,'axial',fit_weighting);ax_b=fit(b,vb,'axial',fit_weighting)
    initial_pert=quotient_distance(a,b)
    for k in range(steps):
        a=advance(a);b=advance(b)
        if any(not np.isfinite(x).all() for x in a+b):raise FloatingPointError('nonfinite filament state')
    va=velocity(a,sigma,component_gamma);vb=velocity(b,sigma,component_gamma)
    final_a=fit(a,va,preferred,fit_weighting);final_b=fit(b,vb,preferred,fit_weighting)
    axf_a=fit(a,va,'axial',fit_weighting);axf_b=fit(b,vb,'axial',fit_weighting)
    return {'init_nominal':init_a['relative_residual'],'init_perturbed':init_b['relative_residual'],
        'final_nominal':final_a['relative_residual'],'final_perturbed':final_b['relative_residual'],
        'init_nominal_axial':ax_a['relative_residual'],'init_perturbed_axial':ax_b['relative_residual'],
        'final_nominal_axial':axf_a['relative_residual'],'final_perturbed_axial':axf_b['relative_residual'],
        'init_nominal_free':(fit(ao,velocity(ao,sigma,component_gamma),'free',fit_weighting)['relative_residual']
                             if preferred=='axial' else init_a['relative_residual']),
        'init_perturbed_free':(fit(bo,velocity(bo,sigma,component_gamma),'free',fit_weighting)['relative_residual']
                             if preferred=='axial' else init_b['relative_residual']),
        'axial_vs_free_initial_delta_nominal':ax_a['relative_residual']-init_a['relative_residual'] if preferred=='free' else None,
        'initial_nominal_fit':init_a,'initial_perturbed_fit':init_b,
        'shape_drift_nominal':quotient_distance(ao,a),'shape_drift_perturbed':quotient_distance(bo,b),
        'perturbation_amplification':float(quotient_distance(a,b)/max(initial_pert,1e-30)),
        'relative_length_drift_nominal':float((total_length(a)-total_length(ao))/total_length(ao)),
        'relative_length_drift_perturbed':float((total_length(b)-total_length(bo))/total_length(bo)),
        'filament_points':points,'steps':steps,'final_time':T,'lambda':lam,
        'fit_mode_requested':fit_mode,'fit_mode_selected':preferred,'fit_weighting':fit_weighting,
        'filament_model':'MIDPOINT_REGULARIZED_HEUN_WITHOUT_FINITE_CORE_EULER'}

def exploratory_score(measure):
    """Ranking proxy only: no certified stationary Euler, no nonlinear stability."""
    return max(float(measure['init_nominal']),float(measure['init_perturbed'])) + \
           max(float(measure['shape_drift_nominal']),float(measure['shape_drift_perturbed'])) + \
           .02*max(0.,float(measure['perturbation_amplification'])-1.)
