from __future__ import annotations
import numpy as np
from .geometry import modal_basis, tangents, length
from .backend import biot_savart_velocity

def normal_velocity(v,t): return v-np.sum(v*t,axis=1)[:,None]*t

def modal_operator(x,m,gamma,core,eps):
    basis=modal_basis(x,m); t=tangents(x); M=np.zeros((4,4),float)
    for j,e in enumerate(basis):
        vp=normal_velocity(biot_savart_velocity(x+eps*e,gamma,core),t)
        vm=normal_velocity(biot_savart_velocity(x-eps*e,gamma,core),t)
        dv=(vp-vm)/(2*eps)
        for i,q in enumerate(basis):
            M[i,j]=np.mean(np.sum(q*dv,axis=1))
    vals,vecs=np.linalg.eig(M)
    return M,vals,vecs,basis

def spectrum(x,modes,gamma,core,eps):
    rows=[]; cache={}
    L=length(x)
    for m in modes:
        M,vals,vecs,basis=modal_operator(x,m,gamma,core,eps)
        # preregistered oscillatory branch: largest absolute imaginary part; tie -> largest real part
        order=sorted(range(len(vals)),key=lambda i:(abs(vals[i].imag),vals[i].real),reverse=True)
        j=order[0]; lam=vals[j]
        rows.append({"m":int(m),"k":2*np.pi*m/L,"sigma":float(lam.real),"omega":float(abs(lam.imag)),"eig_index":int(j),"eigs":[[float(z.real),float(z.imag)] for z in vals]})
        cache[m]=(vecs[:,j],basis)
    ks=np.array([r['k'] for r in rows]); om=np.array([r['omega'] for r in rows])
    vg=np.gradient(om,ks,edge_order=1) if len(rows)>=2 else np.full_like(om,np.nan)
    for r,v in zip(rows,vg):
        tau=L/max(abs(float(v)),1e-300) if np.isfinite(v) and abs(v)>0 else np.nan
        theta=(r['omega']*tau)%(2*np.pi) if np.isfinite(tau) else np.nan
        r.update(v_group=float(v),tau_loop=float(tau),theta=float(theta),delay_score=float(1-np.cos(theta)) if np.isfinite(theta) else np.nan)
    return rows,cache

def physical_eigen_perturbation(eigvec,basis):
    c=np.real(eigvec)
    if np.linalg.norm(c)<1e-10: c=np.imag(eigvec)
    p=sum(c[j]*basis[j] for j in range(4))
    rms=np.sqrt(np.mean(np.sum(p*p,axis=1)))
    return p/max(rms,1e-300)
