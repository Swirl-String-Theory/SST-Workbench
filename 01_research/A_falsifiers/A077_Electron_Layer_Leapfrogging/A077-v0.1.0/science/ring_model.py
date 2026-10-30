"""Independent axisymmetric REGULARIZED-FILAMENT model. Not 3D finite-core Euler.

Rings are circular with variable radius and axial position. Velocity from other
rings is evaluated at (R_i,0,z_i) with a compact quadrature in angular source
coordinate. Self-translation uses a separate thin-core closure. Circulation is
prescribed; material core-volume closure is only a proxy and must not be confused
with a resolved vortex cross section. SI units are used throughout.
"""
from __future__ import annotations
import math
import numpy as np


def circulation(r_c=1.40897017e-15, speed=1.09384563e6):
    return 2 * math.pi * r_c * speed


def ring_derivative(y, gammas, core_volumes, ntheta=96, self_constant=0.25):
    """y=[R0,z0,R1,z1,...]; V_i=a_i^2 R_i, kept fixed as proxy."""
    y=np.asarray(y,dtype=np.float64)
    gamma=np.asarray(gammas,dtype=np.float64)
    v=np.asarray(core_volumes,dtype=np.float64)
    rings=y.reshape((-1,2))
    if len(gamma)!=len(rings) or len(v)!=len(rings):
        raise ValueError('ring data mismatch')
    if not np.isfinite(y).all() or (rings[:,0]<=0).any() or (v<=0).any():
        raise ValueError('invalid nonpositive ring radius or core volume')
    n=int(ntheta)
    if n<16 or n%2:raise ValueError('ntheta must be even >=16')
    angles=(2*math.pi/n)*np.arange(n,dtype=np.float64)
    co,si=np.cos(angles),np.sin(angles)
    result=np.zeros_like(rings)
    for i,(ri,zi) in enumerate(rings):
        ai=math.sqrt(v[i]/ri)
        if 8*ri<=ai or not np.isfinite(ai):
            raise ValueError('thin-core closure outside validity domain')
        result[i,1]+=gamma[i]*(math.log(8*ri/ai)-self_constant)/(4*math.pi*ri)
        for j,(rj,zj) in enumerate(rings):
            if i==j:continue
            aj=math.sqrt(v[j]/rj)
            dz=zi-zj
            dist2=ri*ri+rj*rj-2*ri*rj*co+dz*dz+aj*aj
            w=dist2**(-1.5)
            fac=gamma[j]*rj/(2*n)
            result[i,0]+=fac*float(np.sum(co*dz*w))
            result[i,1]+=fac*float(np.sum((rj-ri*co)*w))
    return result.ravel()


def trajectory(initial, gammas, core_radii, *, dt, steps, ntheta=96, self_constant=0.25,
               save_every=1):
    y=np.asarray(initial,dtype=np.float64).reshape((-1,2)).copy()
    g=np.asarray(gammas,dtype=np.float64)
    a=np.asarray(core_radii,dtype=np.float64)
    if len(g)!=len(y) or len(a)!=len(y) or (a<=0).any() or dt<=0 or steps<1 or save_every<1:
        raise ValueError('bad model inputs')
    vols=a*a*y[:,0]
    deriv=lambda q:ring_derivative(q,g,vols,ntheta,self_constant)
    yflat=y.ravel()
    times=[0.0]; values=[yflat.copy()]
    for step in range(1,steps+1):
        k1=deriv(yflat)
        k2=deriv(yflat+dt*k1/2)
        k3=deriv(yflat+dt*k2/2)
        k4=deriv(yflat+dt*k3)
        yflat=yflat+(dt/6)*(k1+2*k2+2*k3+k4)
        if not np.isfinite(yflat).all() or np.any(yflat[::2]<=0):
            raise FloatingPointError('ring collapsed/invalid trajectory; cannot claim Euler result')
        if step%save_every==0 or step==steps:
            times.append(step*dt); values.append(yflat.copy())
    return {'t':np.array(times), 'y':np.array(values), 'gamma':g.copy(),'a2R':vols.copy()}


def axial_order_crossings(t, y, *, hysteresis=0.0):
    """Count crossings of relative axial separation, not quantum levels."""
    y=np.asarray(y).reshape((-1,np.asarray(y).shape[-1]//2,2))
    if y.shape[1]!=2:raise ValueError('two rings required')
    dz=y[:,1,1]-y[:,0,1]
    signs=np.where(dz>hysteresis,1,np.where(dz<-hysteresis,-1,0))
    nonzero=np.flatnonzero(signs)
    events=[]
    for a,b in zip(nonzero[:-1],nonzero[1:]):
        if signs[a]!=signs[b]:
            crossing=float(t[a]+(t[b]-t[a])*abs(dz[a])/(abs(dz[a])+abs(dz[b])))
            events.append(crossing)
    return events


def analysis(t,y,gamma, a2R):
    yy=np.asarray(y).reshape((len(t),-1,2)); rr=yy[:,:,0];zz=yy[:,:,1]
    am=np.sqrt(np.asarray(a2R)[None,:]/rr)
    crossings=axial_order_crossings(t,y) if yy.shape[1]==2 else []
    # The relative-height sequence is a continuous observable. Rank swaps are NOT levels.
    return {'crossings':crossings,'crossing_count':len(crossings),
        'initial_final_relative_z_normalized':float(zz[-1,-1]-zz[-1,0]) if yy.shape[1]>1 else None,
        'min_radius_normalized':float(rr.min()),'min_core_normalized':float(am.min()),
        'max_core_over_radius':float((am/rr).max()),
        'circulation_relative_drift':0.0, 'core_proxy_relative_drift':float(np.max(np.abs(am*am*rr/np.asarray(a2R)[None,:]-1.0))),
        'ring_velocity_sgn': [int(np.sign(zz[-1,k]-zz[0,k])) for k in range(yy.shape[1])],
        'ring_order_not_quantum_level':True}
