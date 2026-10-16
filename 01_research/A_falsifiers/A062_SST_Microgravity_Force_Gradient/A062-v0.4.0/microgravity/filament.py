"""Rosenhead regularized Biot-Savart and Kelvin impulse EXCHANGE proxy.

No G in this module. This is instantaneous filament advection, not a complete
3-D Euler evolution, material test-body force, or a gravity derivation.
"""
from __future__ import annotations
import math
import numpy as np
RHO_F=7.0e-7
V_SWIRL=1.09384563e6
R_C=1.40897017e-15
GAMMA=2*math.pi*R_C*V_SWIRL
G_REF=6.67430e-11

def segments(x):
    x=np.asarray(x,dtype=np.float64)
    dl=np.roll(x,-1,axis=0)-x
    return x+0.5*dl,dl

def induced_velocity(target,source,core,block=5000):
    """Return induced nondimensional u=v*L/Gamma via Rosenhead kernel."""
    mid,dl=segments(source)
    ret=np.empty_like(target)
    for k in range(0,len(target),block):
        xx=target[k:k+block]
        r=xx[:,None,:]-mid[None,:,:]
        kernel=np.cross(dl[None,:,:],r)/(np.sum(r*r,axis=2)+core*core)[:,:,None]**1.5
        ret[k:k+block]=kernel.sum(axis=1)/(4*np.pi)
    return ret

def rotate_x(x,angle):
    c,s=math.cos(angle),math.sin(angle)
    a=np.array([[1,0,0],[0,c,-s],[0,s,c]],dtype=np.float64)
    return x@a.T

def interaction(xa,xb,separation,core,theta=0.0,sign_b=1):
    """Fixed separation along +z, B tilted around x; two-way impulse exchange.

    For a closed constant-circulation filament I= (rho Gamma/2) int X x dX.
    dI/dt|cross = rho Gamma int u_other x dX, where u_other is Biot-Savart.
    Because u = Gamma/(L) * u_hat and dX = L*dX_hat, result
    F = rho Gamma_A Gamma_B times dimensionless integral (N).
    """
    b=rotate_x(xb,theta)+np.array([0.,0.,separation])
    ma,da=segments(xa); mb,db=segments(b)
    if np.linalg.norm(mb[:,None,:]-ma[None,:,:],axis=2).min() < 2.0*core:
        # Non-overlap is essential for a separated-source interpretation.
        raise ValueError('Vortex cores intersect; choose larger separation')
    ua=induced_velocity(mb,xa,core)
    ub=induced_velocity(ma,b,core)
    fb=(RHO_F*GAMMA**2*sign_b)*np.cross(ua,db).sum(axis=0)
    fa=(RHO_F*GAMMA**2*sign_b)*np.cross(ub,da).sum(axis=0)
    return {'f_b_N':fb,'f_a_N':fa,'f_parallel_N':float(fb[2]),
            'third_law_residual':float(np.linalg.norm(fa+fb)/max(np.linalg.norm(fa),np.linalg.norm(fb),1e-100)),
            'gap_over_core':float(np.linalg.norm(mb[:,None,:]-ma[None,:,:],axis=2).min()/core)}

def sweep(a,b,separations,core,angles=(0.,math.pi/2,math.pi),sign_b=1):
    out=[]
    for theta in angles:
        for R in separations:
            q=interaction(a,b,float(R),core,theta,sign_b)
            out.append({'theta_rad':theta,'R_over_length':float(R),
                'F_b_z_N':q['f_parallel_N'], 'F_b_vector_N':q['f_b_N'].tolist(),
                'F_a_vector_N':q['f_a_N'].tolist(),
                'third_law_residual':q['third_law_residual'],'gap_over_core':q['gap_over_core']})
    return out

def exponent(data,angle=0.,limit=9):
    d=[q for q in data if abs(q['theta_rad']-angle)<1e-10 and q['R_over_length']>=limit]
    x=np.array([q['R_over_length'] for q in d]);y=np.abs([q['F_b_z_N'] for q in d])
    if len(x)<3 or np.any(y<=0):return float('nan')
    return float(-np.polyfit(np.log(x),np.log(y),1)[0])

def gradient_fd(xa,xb,r,core,h=0.05,theta=0):
    plus=interaction(xa,xb,r+h,core,theta)['f_parallel_N']
    minus=interaction(xa,xb,r-h,core,theta)['f_parallel_N']
    # Dimensionless separation -> d/d physical R = 1/L*d/d dimensionless R
    return (plus-minus)/(2*h)
