from __future__ import annotations
import numpy as np
from native_ext.core import biot_savart

def periodic_pressure_poisson(points, *, core, gamma=1.0, grid_n=0, padding=1.0, backend='auto', mod=None, allow_sycl_cpu=False, chunk=200000):
    """Diagnostic only: periodic-box pressure-Poisson closure for p/rho. Not used to evolve the filament."""
    if not grid_n: return None
    x=np.asarray(points,float); lo=x.min(0)-padding; hi=x.max(0)+padding; N=int(grid_n)
    axes=[np.linspace(lo[k],hi[k],N,endpoint=False) for k in range(3)]; dx=np.array([(hi[k]-lo[k])/N for k in range(3)])
    X,Y,Z=np.meshgrid(*axes,indexing='ij'); q=np.c_[X.ravel(),Y.ravel(),Z.ravel()]; vel=np.empty_like(q); used=None
    for a in range(0,len(q),chunk): vel[a:a+chunk],used=biot_savart(x,q[a:a+chunk],gamma=gamma,core=core,backend=backend,allow_sycl_cpu=allow_sycl_cpu,mod=mod)
    V=vel.reshape(N,N,N,3); G=np.empty((N,N,N,3,3))
    for i in range(3):
        grads=np.gradient(V[...,i],*dx,edge_order=2)
        for j in range(3): G[...,i,j]=grads[j]
    src=np.zeros((N,N,N))
    for i in range(3):
        for j in range(3): src-=G[...,i,j]*G[...,j,i]
    kvec=[2*np.pi*np.fft.fftfreq(N,d=dx[k]) for k in range(3)]; KX,KY,KZ=np.meshgrid(*kvec,indexing='ij'); k2=KX*KX+KY*KY+KZ*KZ
    sh=np.fft.fftn(src); ph=np.zeros_like(sh); mask=k2>0; ph[mask]=-sh[mask]/k2[mask]; p=np.fft.ifftn(ph).real
    gp=np.stack(np.gradient(p,*dx,edge_order=2),axis=-1)
    # nearest-cell sampling is deliberate and reported as a diagnostic approximation.
    ijk=np.floor((x-lo)/dx).astype(int)%N; acc=np.array([-gp[i,j,k] for i,j,k in ijk])
    return dict(grid_n=N,box_lo=lo,box_hi=hi,dx=dx,backend=used,source_rms=float(np.sqrt(np.mean(src*src))),p_rms=float(np.sqrt(np.mean(p*p))),pressure_accel=acc)
