from __future__ import annotations
import numpy as np

def relative_difference(A,B):
    A=np.asarray(A,float); B=np.asarray(B,float)
    return float(np.linalg.norm((A-B).ravel())/(0.5*(np.linalg.norm(A.ravel())+np.linalg.norm(B.ravel()))+1e-300))

def even_odd(plus,minus):
    p=np.asarray(plus,float); m=np.asarray(minus,float)
    e=0.5*(p+m); o=0.5*(p-m)
    ne=float(np.linalg.norm(e.ravel())); no=float(np.linalg.norm(o.ravel()))
    return {'even_norm':ne,'odd_norm':no,'odd_over_even':float(no/(ne+1e-300)),'even':e,'odd':o}

def commutator_scaled(AB,BA,eps):
    AB=np.asarray(AB,float); BA=np.asarray(BA,float); eps=float(eps)
    return float(np.linalg.norm((AB-BA).ravel())/(eps*eps+1e-300))
