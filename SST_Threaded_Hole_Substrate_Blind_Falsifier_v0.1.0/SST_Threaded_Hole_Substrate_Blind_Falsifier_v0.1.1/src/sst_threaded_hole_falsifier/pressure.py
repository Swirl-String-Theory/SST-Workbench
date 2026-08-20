from __future__ import annotations
import numpy as np
from .native import field_velocity

def _fit(y,X):
    q=np.linalg.lstsq(X,y,rcond=None)[0];p=X@q;ss=np.sum((y-p)**2);st=np.sum((y-y.mean())**2);return float(1-ss/max(st,1e-30)),q

def pressure_poisson_metrics(points,offsets,gammas,core,grid_n=14,box_half=2.4,rho=1.0):
    n=int(grid_n);ax=np.linspace(-box_half,box_half,n,endpoint=False);h=2*box_half/n
    X,Y,Z=np.meshgrid(ax,ax,ax,indexing='ij');samples=np.c_[X.ravel(),Y.ravel(),Z.ravel()]
    v=field_velocity(samples,points,offsets,gammas,core).reshape(n,n,n,3)
    grad=np.empty((n,n,n,3,3))
    for i in range(3):
        for j in range(3): grad[...,i,j]=(np.roll(v[...,i],-1,axis=j)-np.roll(v[...,i],1,axis=j))/(2*h)
    source=-rho*np.einsum('...ij,...ji->...',grad,grad)
    shat=np.fft.fftn(source-source.mean());k=2*np.pi*np.fft.fftfreq(n,d=h);KX,KY,KZ=np.meshgrid(k,k,k,indexing='ij');k2=KX*KX+KY*KY+KZ*KZ;phat=np.zeros_like(shat);mask=k2>0;phat[mask]=-shat[mask]/k2[mask];p=np.fft.ifftn(phat).real
    r=np.sqrt(X*X+Y*Y+Z*Z);center=p[r<0.35].mean();shell=p[(r>1.45)&(r<1.95)].mean();deficit=float(center-shell)
    rbins=np.linspace(.55,2.05,9);rc=[];pm=[]
    for a,b in zip(rbins[:-1],rbins[1:]):
        m=(r>=a)&(r<b)
        if np.any(m):rc.append(.5*(a+b));pm.append(float(p[m].mean()))
    rc=np.asarray(rc);pm=np.asarray(pm);X1=np.c_[np.ones_like(rc),1/rc];X2=np.c_[np.ones_like(rc),1/(rc*rc)];r21,q1=_fit(pm,X1);r22,q2=_fit(pm,X2)
    return {'pressure_center_minus_shell':deficit,'pressure_source_mean':float(source.mean()),'pressure_source_abs_mean':float(np.mean(np.abs(source))),'r2_1_over_r':r21,'r2_1_over_r2':r22,'r2_advantage_1_over_r':float(r21-r22),'fit_coeff_1_over_r':float(q1[1]),'fit_coeff_1_over_r2':float(q2[1]),'grid_n':n,'box_half':box_half}
