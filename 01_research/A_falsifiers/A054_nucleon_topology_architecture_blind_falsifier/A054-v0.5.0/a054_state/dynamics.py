from __future__ import annotations
import math
import numpy as np
from .geometry import as_closed,bishop_frame
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


def potential_factory(components,core=1.0,modes=3):
    comps=[as_closed(c) for c in components]; flat=np.vstack(comps);B,offs=perturbation_basis(comps,modes=modes)
    def U(q):
        q=np.asarray(q,dtype=float); x=flat+np.tensordot(q,B,axes=(0,0));return total_kernel(energy_matrix(split_flat(x,offs),core=core))
    return U,B,offs


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


def mode_ringdown(U, K, eps_q=0.01, dt=0.01, steps=256):
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
      'min_hessian_eigenvalue':float(vals[0]),
      'amplitude_ratio':float(amps.max()/max(abs(eps_q),1e-15)),
      'hamiltonian_relative_drift':float((H.max()-H.min())/max(abs(H.mean()),1e-30)),
      'expected_omega':float(math.sqrt(vals[0])),
    }
