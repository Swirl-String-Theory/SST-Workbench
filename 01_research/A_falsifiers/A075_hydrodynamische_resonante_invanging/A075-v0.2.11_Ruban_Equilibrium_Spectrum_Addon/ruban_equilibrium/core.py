"""Ruban equation-(9) equilibrium diagnostics. A075 v0.2.9 solver is pinned, unchanged.

Independent midpoint-filament quadrature + spectral derivatives for curvature;
not Ruban's original pseudo-spectral implementation and NOT certified dynamics.
All primary values are dimensionless (R0=1, Gamma=2*pi).
"""
from __future__ import annotations
import math
import numpy as np
from scipy.optimize import least_squares

GAMMA = 2.0 * math.pi
DELTA = 1.0/20.0
LAMBDA = 7.0/5.0 + 0.5*math.log(200.0)
LOCAL_COEFFICIENT = 0.5 * (7.0/5.0 - 0.5*math.log(2.0))
B_REFERENCE = 77.0/500.0


def derivative(x: np.ndarray, order: int=1) -> np.ndarray:
    """Spectral derivative for 2*pi-periodic theta, uniform theta spacing."""
    n = len(x)
    w = np.fft.fftfreq(n, d=1.0/n)
    return np.fft.ifft((1j*w[:,None])**order * np.fft.fft(x, axis=0), axis=0).real


def torus(b: float, n: int, p: int=2, q: int=3, correction=None) -> np.ndarray:
    if not (0 < b < 1 and n >= 32 and n % 2 == 0 and math.gcd(p,q) == 1):
        raise ValueError("Require 0<B<1, even n>=32, coprime positive p,q")
    th = np.arange(n, dtype=float)*2*math.pi/n
    rad = 1+b*np.cos(q*th)
    z = b*np.sin(q*th)
    if correction is not None:
        c = np.asarray(correction, dtype=float)
        if c.ndim!=1 or len(c)%4 or not np.isfinite(c).all():
            raise ValueError('Fourier correction requires 4 coefficients per added harmonic')
        for idx in range(len(c)//4):
            w=(idx+2)*q*th
            a,b0,d,e=c[4*idx:4*idx+4]
            rad += a*np.cos(w)+b0*np.sin(w)
            z += d*np.cos(w)+e*np.sin(w)
    if float(np.min(rad))<=0.05:
        raise ValueError('Invalid radial profile')
    return np.column_stack((rad*np.cos(p*th),rad*np.sin(p*th),z))


def field(x: np.ndarray, delta: float=DELTA,local_coefficient: float=LOCAL_COEFFICIENT, block=64):
    """Eq9 with Gamma=2*pi, midpoint-segment Biot-Savart and Fourier curvature.

    FFT derivatives require uniform-theta samples; periodic collocation is explicit.
    """
    x=np.asarray(x,dtype=float)
    if x.ndim !=2 or x.shape[1]!=3 or len(x)<32 or len(x)%2 or not np.isfinite(x).all():
        raise ValueError('Invalid geometry')
    if delta<=0 or not np.isfinite(delta):raise ValueError('delta must be positive')
    dl=np.roll(x,-1,axis=0)-x
    mid=x+0.5*dl
    out=np.empty_like(x)
    for a in range(0,len(x),block):
        r=x[a:a+block,None,:]-mid[None,:,:]
        norm=np.sum(r*r,axis=2)+delta*delta
        out[a:a+block]=0.5*np.sum(np.cross(dl[None,:,:],r)/(norm**1.5)[:,:,None],axis=1)
    d1=derivative(x,1);d2=derivative(x,2)
    kbin=np.cross(d1,d2)/np.maximum(np.linalg.norm(d1,axis=1)**3,1e-15)[:,None]
    return out+local_coefficient*kbin


def normal_project(vec:np.ndarray, tangent: np.ndarray) -> np.ndarray:
    return vec-np.sum(vec*tangent,axis=1)[:,None]*tangent


def fitted_residual(x:np.ndarray, vel:np.ndarray|None=None, delta=DELTA, local_coefficient=LOCAL_COEFFICIENT):
    if vel is None:vel=field(x,delta,local_coefficient)
    d=derivative(x,1)
    speed=np.linalg.norm(d,axis=1)
    if float(np.min(speed))<1e-9: raise ValueError('Degenerate tangent')
    tangent=d/speed[:,None]
    ws=np.sqrt(speed * 2*math.pi/len(x))
    ez=np.broadcast_to(np.array([0.,0.,1.]), x.shape)
    spin=np.column_stack((-x[:,1],x[:,0],np.zeros(len(x))))
    col0=normal_project(ez,tangent)
    col1=normal_project(spin,tangent)
    target=normal_project(vel,tangent)
    A=np.stack((col0*ws[:,None],col1*ws[:,None]),axis=-1).reshape(-1,2)
    b=(target*ws[:,None]).ravel()
    coef,_,_,_=np.linalg.lstsq(A,b,rcond=None)
    residual=target-coef[0]*col0-coef[1]*col1
    L=float(np.sum(speed)*(2*math.pi/len(x)))
    rms=float(np.sqrt(np.sum(np.sum(residual*residual,axis=1)*ws**2)/L))
    eps=float(rms/GAMMA)  # R0=1
    return {'U':float(coef[0]),'Omega':float(coef[1]),'epsilon':eps,
            'length':L,'residual':residual,'rms_velocity':rms,
            'normal_rms_velocity':float(np.sqrt(np.sum(np.sum(target*target,axis=1)*ws**2)/L)),
            'weights':ws,'tangent':tangent}


def relax(b:float,n:int,harmonics:int=1,max_nfev:int=25,regularization=1e-3,delta=DELTA,reference_points=None):
    """Constrained harmonic shape correction; small residual != certified equilibrium."""
    if harmonics<0 or harmonics>5:raise ValueError('harmonics must be 0..5')
    base=torus(b,n)
    if reference_points is not None:
        source=np.asarray(reference_points,dtype=float)
        if source.shape!=base.shape or not np.isfinite(source).all():raise ValueError('Invalid pinned A007 input geometry')
        base=source.copy()
    def make_x(c):
        # Each relaxed candidate is a deformation of the ORIGINAL A007 geometry at reference B.
        return base + torus(b,n,correction=c)-torus(b,n)
    if harmonics==0:
        x=base;f=fitted_residual(x,delta=delta)
        return {'x':x,'coeff':np.zeros(0),'initial_epsilon':f['epsilon'],'final_epsilon':f['epsilon'],
                'U':f['U'],'Omega':f['Omega'],'converged_optimizer':False,
                'optimizer_message':'no relaxation requested','nfev':0}
    initial=fitted_residual(base,delta=delta)
    def fun(c):
        x=make_x(c)
        v=field(x,delta=delta)
        f=fitted_residual(x,vel=v,delta=delta)
        return np.r_[f['residual'].ravel()/GAMMA,regularization*c]
    c0=np.zeros(4*harmonics)
    ls=least_squares(fun,c0,bounds=(-0.035*np.ones(len(c0)),0.035*np.ones(len(c0))),
                     x_scale='jac',max_nfev=max_nfev,ftol=1e-8,xtol=1e-8,gtol=1e-8)
    x=make_x(ls.x)
    f=fitted_residual(x,delta=delta)
    return {'x':x,'coeff':ls.x,'initial_epsilon':initial['epsilon'],'final_epsilon':f['epsilon'],
            'U':f['U'],'Omega':f['Omega'], 'converged_optimizer':bool(ls.success),
            'optimizer_message':str(ls.message),'nfev':int(ls.nfev)}


def numerical_spectral_proxy(x:np.ndarray,U:float,Omega:float,modes:int=4,step=1e-5,delta=DELTA):
    """NON-CERTIFYING Fourier-Ritz directional Jacobian, fixed e_r and e_z basis.

    The finite-mode projection does NOT account for all gauge, continuous spectrum,
    constraints or non-normal dynamics. Values MUST NOT be called Floquet exponents
    or proof of stability.
    """
    n=len(x);th=np.arange(n)*2*math.pi/n
    er=np.column_stack((np.cos(2*th),np.sin(2*th),np.zeros(n)))
    ez=np.broadcast_to(np.array([0.,0.,1.]),(n,3))
    basis=[]
    for m in range(1,modes+1):
        for f in (np.cos(m*th),np.sin(m*th)):
            basis += [er*f[:,None],ez*f[:,None]]
    Q=np.array(basis).reshape(len(basis),-1).T
    Q,_=np.linalg.qr(Q)
    def F(a):
        v=field(a,delta=delta)
        rot=np.column_stack((-a[:,1],a[:,0],np.zeros(n)))
        return (v-Omega*rot-np.array([0.,0.,U])).ravel()
    J=np.empty((len(basis),len(basis)))
    for k in range(len(basis)):
        direction=Q[:,k].reshape(n,3)
        J[:,k]=Q.T@((F(x+step*direction)-F(x-step*direction))/(2*step))
    eig=np.linalg.eigvals(J)
    return {'ritz_eigenvalues':[[float(z.real),float(z.imag)] for z in eig],
            'max_real_part':float(np.max(eig.real)), 'mode_count':len(basis),
            'status':'EXPLORATORY_UNCERTIFIED_GAUGE_INCOMPLETE', 'step':step}
