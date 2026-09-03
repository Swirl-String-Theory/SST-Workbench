from __future__ import annotations
import numpy as np
from .kernels import velocity

def fit_relative_equilibrium(points,offsets,gamma,core,require_native=False):
    X=np.asarray(points,float);V=velocity(X,offsets,gamma,core,require_native); A=[];b=[]
    for x,v in zip(X,V):
        xx,yy,zz=x
        # U + Omega x x = U - [x]_x Omega
        M=np.array([[1,0,0,0,zz,-yy],[0,1,0,-zz,0,xx],[0,0,1,yy,-xx,0]],float)
        A.append(M); b.append(v)
    A=np.vstack(A);b=np.concatenate(b); q=np.linalg.lstsq(A,b,rcond=None)[0];pred=(A@q).reshape(-1,3);res=float(np.linalg.norm(V-pred)/max(np.linalg.norm(V),1e-300))
    return {'U':q[:3].tolist(),'Omega':q[3:].tolist(),'epsilon_RE':res,'velocity_norm':float(np.linalg.norm(V))}
