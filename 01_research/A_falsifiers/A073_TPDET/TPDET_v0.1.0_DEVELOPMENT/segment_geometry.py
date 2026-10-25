"""Minimum distance of finite polygon segments, using analytic closest-point candidates.

Exact for fixed straight polygon segments to floating precision, but sampling in
TIME remains finite; this does NOT certify absence of reconnection in continuum.
"""
from __future__ import annotations
import numpy as np


def segment_pair_distance(a,b,chunk=32):
    a=np.asarray(a,float);b=np.asarray(b,float)
    A=a; U=np.roll(a,-1,axis=0)-a
    B=b; V=np.roll(b,-1,axis=0)-b
    cc=np.einsum('ij,ij->i',V,V)[None,:]
    min_sq=float('inf')
    for i in range(0,len(A),chunk):
        p=A[i:i+chunk];u=U[i:i+chunk]
        w=p[:,None,:]-B[None,:,:]
        aa=np.einsum('ij,ij->i',u,u)[:,None]
        if np.min(aa)<=0 or np.min(cc)<=0:raise ValueError('zero-length segment')
        bb=np.einsum('ik,jk->ij',u,V)
        d=np.einsum('ijk,ik->ij',w,u)
        e=np.einsum('ijk,jk->ij',w,V)
        def eval_sq(s,t):
            vec=w+s[...,None]*u[:,None,:]-t[...,None]*V[None,:,:]
            return np.einsum('ijk,ijk->ij',vec,vec)
        zeros=np.zeros_like(d);ones=np.ones_like(d)
        dsq=eval_sq(zeros,np.clip(e/cc,0,1))
        dsq=np.minimum(dsq,eval_sq(ones,np.clip((e+bb)/cc,0,1)))
        dsq=np.minimum(dsq,eval_sq(np.clip(-d/aa,0,1),zeros))
        dsq=np.minimum(dsq,eval_sq(np.clip((bb-d)/aa,0,1),ones))
        den=aa*cc-bb*bb
        okay=den>1.e-14*aa*cc
        s=np.divide(bb*e-cc*d,den,out=np.zeros_like(d),where=okay)
        t=np.divide(aa*e-bb*d,den,out=np.zeros_like(d),where=okay)
        interior=okay&(s>=0)&(s<=1)&(t>=0)&(t<=1)
        intdist=eval_sq(s,t)
        dsq=np.minimum(dsq,np.where(interior,intdist,np.inf))
        min_sq=min(min_sq,float(np.min(dsq)))
    return float(np.sqrt(max(0,min_sq)))


def network_segment_clearance(cs):
    return min(segment_pair_distance(cs[i],cs[j]) for i in range(len(cs)) for j in range(i+1,len(cs)))
