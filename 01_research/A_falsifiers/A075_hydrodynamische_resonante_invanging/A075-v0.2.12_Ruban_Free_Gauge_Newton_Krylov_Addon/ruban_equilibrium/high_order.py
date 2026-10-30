"""Conservative independent numerical tests for Ruban's regularized filament.

Units R0=1, Gamma=2*pi, time=R0^2/Gamma. No proof of exact equilibrium.
This module intentionally keeps the original A075 0.2.9 midpoint source unchanged.
"""
from __future__ import annotations
import numpy as np
from scipy.optimize import least_squares
from .core import torus,derivative,normal_project,DELTA,LOCAL_COEFFICIENT,GAMMA,B_REFERENCE


def validate(x):
    x=np.asarray(x,dtype=np.float64)
    if x.ndim!=2 or x.shape[1]!=3 or len(x)<32 or len(x)%2 or not np.isfinite(x).all():
        raise ValueError('Require finite even-N 3D closed curve, N>=32')
    speed=np.linalg.norm(derivative(x),axis=1)
    if speed.min()<1e-7:raise ValueError('Degenerate parameterization')
    return x,speed


def field(x,scheme='trapezoid',delta=DELTA,local_coefficient=LOCAL_COEFFICIENT,block=64):
    """Regularized Biot-Savart integral plus local curvature binormal.

    trapezoid: spectral dX/dtheta * periodic weights;
    midpoint: polygon segment quadrature, for independent discretization check.
    The two finite-N operators must NOT be interpreted as the same discrete model.
    """
    x,speed=validate(x)
    if delta<=0 or not np.isfinite(delta):raise ValueError('Invalid regulator')
    if scheme not in ('midpoint','trapezoid'):raise ValueError('Unknown quadrature')
    if scheme=='trapezoid':
        dl=derivative(x)* (2*np.pi/len(x)); src=x
    else:
        dl=np.roll(x,-1,axis=0)-x; src=x+dl/2
    out=np.empty_like(x)
    for a in range(0,len(x),block):
        r=x[a:a+block,None,:]-src[None,:,:]
        denom=(np.sum(r*r,axis=-1)+delta**2)**1.5
        out[a:a+block]=0.5*np.sum(np.cross(dl[None,:,:],r)/denom[:,:,None],axis=1)
    d1=derivative(x);d2=derivative(x,2)
    out+=local_coefficient*np.cross(d1,d2)/(speed**3)[:,None]
    if not np.isfinite(out).all():raise RuntimeError('Nonfinite velocity')
    return out


def residual(x,scheme='trapezoid',delta=DELTA):
    x,speed=validate(x)
    v=field(x,scheme,delta)
    d1=derivative(x);t=d1/speed[:,None]
    ez=np.broadcast_to(np.array([0.,0.,1.]),x.shape)
    spin=np.column_stack((-x[:,1],x[:,0],np.zeros(len(x))))
    p0=normal_project(ez,t);p1=normal_project(spin,t)
    tar=normal_project(v,t)
    weights=np.sqrt(speed*2*np.pi/len(x))
    A=np.column_stack(((p0*weights[:,None]).ravel(),(p1*weights[:,None]).ravel()))
    co=np.linalg.lstsq(A,(tar*weights[:,None]).ravel(),rcond=None)[0]
    r=tar-co[0]*p0-co[1]*p1
    length=float(2*np.pi/len(x)*np.sum(speed))
    rms=np.sqrt(np.sum(speed*np.sum(r*r,axis=1))*(2*np.pi/len(x))/length)
    return {'x':x,'v':v,'residual':r,'U':float(co[0]),'Omega':float(co[1]),
            'epsilon':float(rms/GAMMA),'rms_velocity':float(rms), 'length':length,
            't':t,'speed':speed,'alpha':np.sum((v-co[0]*ez-co[1]*spin)*d1,axis=1)/speed**2}


def make_shape(b,n,c):
    """Fixed (p,q)=(2,3) winding; use additional radial and z harmonics.

    The B0 reference harmonic is kept fixed for meaningful B0 scans.
    """
    theta=np.arange(n)*2*np.pi/n
    radial=1+b*np.cos(3*theta)
    z=b*np.sin(3*theta)
    if len(c)%4:raise ValueError('Coefficient vector must have length 4*h')
    for k in range(len(c)//4):
        w=3*(k+2)*theta
        a,d,e,f=c[4*k:4*k+4]
        radial+=a*np.cos(w)+d*np.sin(w)
        z+=e*np.cos(w)+f*np.sin(w)
    if radial.min()<0.25:raise ValueError('Radius crossing')
    return np.column_stack((radial*np.cos(2*theta),radial*np.sin(2*theta),z))


def fit(b,n,harmonics=2,scheme='trapezoid',max_nfev=45, bound=.08, reference_points=None):
    if not 0<b<.9 or harmonics<0 or harmonics>10 or max_nfev<1:
        raise ValueError('Invalid optimization settings')
    if reference_points is not None:
        reference_points=np.asarray(reference_points,dtype=float)
        if reference_points.shape!=(n,3) or not np.isfinite(reference_points).all():
            raise ValueError('A007 reference must be a finite (N,3) array')
        offset=reference_points-make_shape(b,n,[])
    else:offset=np.zeros((n,3))
    def x_from(c):return make_shape(b,n,c)+offset
    if harmonics==0:
        x=x_from([]);r=residual(x,scheme)
        return {'x':x,'coeff':np.empty(0),'initial':r,'final':r,'nfev':0,'optimizer_success':False,'optimizer_message':'not requested'}
    initial=residual(x_from([]),scheme)
    def fun(c):
        x=x_from(c);r=residual(x,scheme)
        w=np.sqrt(r['speed']*2*np.pi/n/r['length'])
        return np.r_[(r['residual']*w[:,None]).ravel()/GAMMA, 1e-5*c]
    r=least_squares(fun,np.zeros(4*harmonics),bounds=(-bound,bound),max_nfev=max_nfev,
                    x_scale='jac',xtol=1e-11,ftol=1e-11,gtol=1e-11)
    x=x_from(r.x)
    return {'x':x,'coeff':r.x,'initial':initial,'final':residual(x,scheme),'nfev':r.nfev,
            'optimizer_success':bool(r.success),'optimizer_message':str(r.message)}


def refine_check(b,coef,n,scheme='trapezoid',reference_points=None):
    x=make_shape(b,n,coef)
    if reference_points is not None:
        reference_points=np.asarray(reference_points,dtype=float)
        if reference_points.shape!=(n,3):raise ValueError('Bad fine reference shape')
        x=x+reference_points-make_shape(b,n,[])
    return residual(x,scheme)
