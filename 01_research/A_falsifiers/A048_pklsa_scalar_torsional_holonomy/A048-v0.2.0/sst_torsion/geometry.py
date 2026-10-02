import math
import numpy as np
from scipy.interpolate import CubicSpline

def trefoil(n=512):
    t = np.linspace(0.0, 2.0*np.pi, n, endpoint=False)
    x = (2.0 + np.cos(3.0*t))*np.cos(2.0*t)
    y = (2.0 + np.cos(3.0*t))*np.sin(2.0*t)
    z = np.sin(3.0*t)
    return np.column_stack([x,y,z])

def circle(n=512, radius=1.0):
    t=np.linspace(0.0,2*np.pi,n,endpoint=False)
    return radius*np.column_stack([np.cos(t),np.sin(t),np.zeros_like(t)])

def closed_arclength(points):
    p=np.asarray(points,float)
    if p.ndim != 2 or p.shape[1] != 3 or len(p) < 8:
        raise ValueError("points must have shape (N,3), N>=8")
    q=np.vstack([p,p[0]])
    seg=np.linalg.norm(np.diff(q,axis=0),axis=1)
    if np.any(seg <= 0):
        raise ValueError("duplicate/zero-length segment")
    s=np.concatenate([[0.0],np.cumsum(seg)])
    return s, float(s[-1])

def resample_closed_arclength(points, n=None):
    p=np.asarray(points,float)
    n = int(n or len(p))
    s,L=closed_arclength(p)
    q=np.vstack([p,p[0]])
    target=np.linspace(0.0,L,n+1)
    out=np.empty((n+1,3),float)
    for j in range(3):
        cs=CubicSpline(s,q[:,j],bc_type='periodic')
        out[:,j]=cs(target)
    return out[:-1], L

def canonicalize(points, n=None, rms_radius=1.0):
    q,_=resample_closed_arclength(points,n)
    q=q-np.mean(q,axis=0)
    rms=float(np.sqrt(np.mean(np.sum(q*q,axis=1))))
    if not np.isfinite(rms) or rms <= 0: raise ValueError("invalid RMS radius")
    q=q*(float(rms_radius)/rms)
    _,L=closed_arclength(q)
    return q,L

def _fft_derivative(values, period, order=1):
    v=np.asarray(values,float)
    n=len(v)
    k=2*np.pi*np.fft.fftfreq(n,d=period/n)
    factor=(1j*k)**order
    return np.fft.ifft(np.fft.fft(v,axis=0)*factor[:,None],axis=0).real

def curvature_torsion(points):
    q,L=canonicalize(points, len(points), rms_radius=np.sqrt(np.mean(np.sum((np.asarray(points)-np.mean(points,axis=0))**2,axis=1))))
    r1=_fft_derivative(q,L,1)
    r2=_fft_derivative(q,L,2)
    r3=_fft_derivative(q,L,3)
    cross=np.cross(r1,r2)
    speed=np.linalg.norm(r1,axis=1)
    cross2=np.sum(cross*cross,axis=1)
    kappa=np.linalg.norm(cross,axis=1)/np.maximum(speed**3,1e-30)
    det=np.einsum('ij,ij->i', cross, r3)
    tau=det/np.maximum(cross2,1e-30)
    ds=L/len(q)
    return kappa,tau,ds,L

def bishop_frame(points):
    q,L=canonicalize(points,len(points),rms_radius=1.0)
    r1=_fft_derivative(q,L,1)
    t=r1/np.linalg.norm(r1,axis=1)[:,None]
    ref=np.array([0.0,0.0,1.0])
    if abs(np.dot(ref,t[0]))>0.9: ref=np.array([1.0,0.0,0.0])
    n0=ref-np.dot(ref,t[0])*t[0]; n0/=np.linalg.norm(n0)
    n1=np.empty_like(t); n1[0]=n0
    def transport(n,a,b):
        v=np.cross(a,b); s=np.linalg.norm(v); c=float(np.clip(np.dot(a,b),-1.0,1.0))
        if s < 1e-14:
            z=n-np.dot(n,b)*b; return z/np.linalg.norm(z)
        u=v/s
        z=n*c + np.cross(u,n)*s + u*np.dot(u,n)*(1-c)
        z=z-np.dot(z,b)*b
        return z/np.linalg.norm(z)
    for i in range(1,len(t)): n1[i]=transport(n1[i-1],t[i-1],t[i])
    n_end=transport(n1[-1],t[-1],t[0])
    b0=np.cross(t[0],n1[0])
    hol=math.atan2(float(np.dot(n_end,b0)),float(np.dot(n_end,n1[0])))
    n2=np.cross(t,n1)
    return t,n1,n2,float(hol)

def winding_number(chi):
    chi=np.asarray(chi,float)
    if len(chi)<4: raise ValueError("need >=4 samples")
    closed=np.concatenate([chi,[chi[0]]])
    d=np.angle(np.exp(1j*np.diff(closed)))
    return float(np.sum(d)/(2*np.pi))
