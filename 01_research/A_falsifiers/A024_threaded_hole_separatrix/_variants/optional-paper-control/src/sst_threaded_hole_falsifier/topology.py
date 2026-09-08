from __future__ import annotations
import numpy as np

def gauss_link(c1,c2):
    a=np.asarray(c1,float);b=np.asarray(c2,float);a2=np.roll(a,-1,axis=0);b2=np.roll(b,-1,axis=0);ma=.5*(a+a2);mb=.5*(b+b2);da=a2-a;db=b2-b;tot=0.
    for i in range(len(a)):
        r=ma[i]-mb;den=np.maximum(np.linalg.norm(r,axis=1)**3,1e-18);tot+=np.sum(np.einsum('ij,ij->i',r,np.cross(da[i][None,:],db))/den)
    return float(tot/(4*np.pi))

def thread_link_matrix(carrier,threads): return [[gauss_link(c,t) for t in threads.components()] for c in carrier.components()]
