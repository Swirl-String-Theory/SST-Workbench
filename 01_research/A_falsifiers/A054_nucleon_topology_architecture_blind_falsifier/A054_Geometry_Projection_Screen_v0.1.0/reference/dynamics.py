from __future__ import annotations
import math
import numpy as np
from .geometry import as_closed,bishop_frame,resample_closed,normalize_by_reach
from .energy import energy_matrix,total_kernel


def perturbation_basis(components,modes=3):
    comps=[as_closed(c) for c in components]; basis=[]
    offsets=np.cumsum([0]+[len(c) for c in comps]); total=offsets[-1]
    for ci,c in enumerate(comps):
        _,n,b,_=bishop_frame(c); N=len(c); theta=2*np.pi*np.arange(N)/N
        for k in range(1,int(modes)+1):
            for frame,phase,label in [(n,np.cos(k*theta)[:,None],'Ncos'),(b,np.sin(k*theta)[:,None],'Bsin')]:
                arr=np.zeros((total,3));arr[offsets[ci]:offsets[ci+1]]=frame*phase
                norm=np.sqrt(np.mean(np.sum(arr*arr,axis=1))); arr/=max(norm,1e-15);basis.append(arr)
    return np.asarray(basis),offsets


def split_flat(flat,offsets): return [np.asarray(flat[offsets[i]:offsets[i+1]],float) for i in range(len(offsets)-1)]


def _recondition(components,counts):
    cs=[resample_closed(c,int(n)) for c,n in zip(components,counts)]
    norm,scale,detail=normalize_by_reach(cs)
    return norm,scale,detail


def potential_factory(components,core=1.0,modes=3):
    """Legacy/raw local objective retained only for diagnostic compatibility.

    v0.5.1 science uses ``constrained_potential_factory`` so every derivative,
    line-search evaluation, Hessian and ringdown sees exactly the same projected
    objective.
    """
    comps=[as_closed(c) for c in components]; flat=np.vstack(comps);B,offs=perturbation_basis(comps,modes=modes)
    def U(q):
        q=np.asarray(q,dtype=float); x=flat+np.tensordot(q,B,axes=(0,0));return total_kernel(energy_matrix(split_flat(x,offs),core=core))
    return U,B,offs


def constrained_potential_factory(components,core=1.0,modes=3,counts=None):
    """Build the single canonical v0.5.1 objective.

    U_c(q;X) = H( N[ R(X + delta X(q)) ] ).

    ``project(q)`` returns the exact geometry used by ``U(q)``.  This contract
    prevents the v0.5.1 mismatch where gradients/Hessians were computed before
    projection while acceptance was tested after resampling/reach normalization.
    """
    comps=[as_closed(c) for c in components]
    counts=[len(c) for c in comps] if counts is None else [int(n) for n in counts]
    # Canonicalize the base state once so q=0 is on the same projected manifold.
    comps,_,_= _recondition(comps,counts)
    flat=np.vstack(comps);B,offs=perturbation_basis(comps,modes=modes)
    def project(q):
        q=np.asarray(q,dtype=float)
        x=flat+np.tensordot(q,B,axes=(0,0))
        trial=split_flat(x,offs)
        projected,scale,detail=_recondition(trial,counts)
        return projected,scale,detail
    def U(q):
        projected,_,_=project(q)
        return total_kernel(energy_matrix(projected,core=core))
    return U,project,B,offs,comps


def gradient_only(U,d,eps=0.01):
    z=np.zeros(d); u0=float(U(z)); g=np.zeros(d)
    for i in range(d):
        e=np.zeros(d);e[i]=eps; g[i]=(U(e)-U(-e))/(2*eps)
    return u0,g


def gradient_hessian(U,d,eps=0.01):
    z=np.zeros(d);u0=float(U(z));g=np.zeros(d);K=np.zeros((d,d))
    for i in range(d):
        ei=np.zeros(d);ei[i]=eps; up=U(ei);um=U(-ei);g[i]=(up-um)/(2*eps);K[i,i]=(up-2*u0+um)/(eps*eps)
    for i in range(d):
        for j in range(i+1,d):
            ei=np.zeros(d);ej=np.zeros(d);ei[i]=eps;ej[j]=eps
            v=(U(ei+ej)-U(ei-ej)-U(-ei+ej)+U(-ei-ej))/(4*eps*eps);K[i,j]=K[j,i]=v
    return u0,g,K


def _sign_class(K,negative_relative_tolerance=1e-3):
    Ks=.5*(np.asarray(K,float)+np.asarray(K,float).T)
    eig=np.linalg.eigvalsh(Ks)
    if len(eig)==0 or not np.all(np.isfinite(eig)):
        return 'UNRESOLVED',eig
    scale=max(float(np.max(np.abs(eig))),1e-30)
    tol=float(negative_relative_tolerance)*scale
    return ('NONNEGATIVE' if float(eig.min())>=-tol else 'NEGATIVE'),eig


def gradient_hessian_sweep(U,d,eps,negative_relative_tolerance=1e-3,rel_l2_max=0.15):
    """Evaluate the constrained Hessian at eps, eps/2 and eps/4.

    The finest matrix is authoritative only when the Hessian itself converges
    between the two finest scales and the minimum-eigenvalue sign class is stable
    across all three scales.  Otherwise local stability is NUMERICALLY_UNRESOLVED.
    """
    scales=[float(eps),float(eps)/2.0,float(eps)/4.0]
    rows=[]; matrices=[]
    u0=None;g=None
    for j,h in enumerate(scales):
        uj,gj,K=gradient_hessian(U,d,h)
        if j==len(scales)-1:
            u0=float(uj);g=np.asarray(gj,float)
        cls,eig=_sign_class(K,negative_relative_tolerance)
        sym=float(np.linalg.norm(K-K.T)/max(np.linalg.norm(K),1e-30))
        rows.append({'eps':h,'min_eigenvalue':float(eig.min()) if len(eig) else None,'max_abs_eigenvalue':float(np.max(np.abs(eig))) if len(eig) else None,'sign_class':cls,'symmetry_relative':sym,'eigenvalues':eig.tolist()})
        matrices.append(np.asarray(K,float))
    Kmid,Kfine=matrices[-2],matrices[-1]
    rel=float(np.linalg.norm(Kfine-Kmid)/max(np.linalg.norm(Kfine),1e-30))
    classes=[r['sign_class'] for r in rows]
    sign_consistent=(len(set(classes))==1 and classes[0] in ('NONNEGATIVE','NEGATIVE'))
    converged=bool(np.isfinite(rel) and rel<=float(rel_l2_max) and sign_consistent)
    return u0,g,Kfine,{
        'scales':rows,
        'last_pair_relative_l2':rel,
        'relative_l2_threshold':float(rel_l2_max),
        'sign_consistent':bool(sign_consistent),
        'converged':converged,
        'authoritative_sign_class':classes[-1] if classes else 'UNRESOLVED',
    }


def mode_ringdown(U, K, eps_q=0.01, dt=0.01, steps=256):
    """Reduced ringdown on the same objective U used for the Hessian."""
    Ks=.5*(np.asarray(K,float)+np.asarray(K,float).T)
    vals,vecs=np.linalg.eigh(Ks)
    if len(vals)==0 or float(vals[0])<=0:
        return {'evaluated':False,'reason':'nonpositive_minimum_hessian_eigenvalue','min_hessian_eigenvalue':float(vals[0]) if len(vals) else None}
    e=vecs[:,0]; q=float(eps_q); v=0.0
    def V(x): return float(U(np.asarray(x,float)*e))
    dg=max(abs(eps_q)*1e-3,1e-5)
    def grad(x): return (V(x+dg)-V(x-dg))/(2*dg)
    a=-grad(q); rows=[]
    for _ in range(int(steps)):
        H=.5*v*v+V(q); rows.append((q,v,H))
        qn=q+v*dt+.5*a*dt*dt; an=-grad(qn); v=v+.5*(a+an)*dt; q=qn; a=an
    arr=np.asarray(rows,float); amps=np.abs(arr[:,0]); H=arr[:,2]
    return {
      'evaluated':True,
      'objective':'U_c_reconditioned',
      'min_hessian_eigenvalue':float(vals[0]),
      'amplitude_ratio':float(amps.max()/max(abs(eps_q),1e-15)),
      'hamiltonian_relative_drift':float((H.max()-H.min())/max(abs(H.mean()),1e-30)),
      'expected_omega':float(math.sqrt(vals[0])),
    }
