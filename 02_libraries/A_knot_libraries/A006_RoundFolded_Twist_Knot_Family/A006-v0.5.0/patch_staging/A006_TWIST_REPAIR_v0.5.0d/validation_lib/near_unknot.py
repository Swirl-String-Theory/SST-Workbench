"""Injective radial annulus squeeze for TikZ-derived twist-knot embeddings.

For r>0, F_alpha(r, theta, z)=(R+alpha*(r-R), theta, z).
This is an embedding of the region occupied by the original curve for alpha>0.
Straight-line interpolation of alpha from 1 is a curve isotopy.  No topology
is inferred from looking like a round unknot; source knot invariants are tested.
"""
import numpy as np

PROFILES={
    'ROUND': {'radial_fraction':.42,'global_scale':1.50,'cyl_rad_visual':.12},
    'TOROIDAL': {'radial_fraction':.23,'global_scale':2.00,'cyl_rad_visual':.09},
    'NEAR_UNKNOT': {'radial_fraction':.12,'global_scale':2.50,'cyl_rad_visual':.06},
}

def params(x):
    x=np.asarray(x,dtype=np.float64)
    lo=np.min(x[:,:2],axis=0);hi=np.max(x[:,:2],axis=0)
    c=.5*(lo+hi)
    r=np.linalg.norm(x[:,:2]-c,axis=1)
    if r.min()<1e-5: raise ValueError('Source curve crosses angular singularity')
    return c,float(np.median(r)),float(np.min(r))

def annulus_squeeze(x,alpha,scale,center=None,R=None):
    if not (0<alpha<=1 and scale>0): raise ValueError('Requires 0<alpha<=1, scale>0')
    x=np.asarray(x,dtype=np.float64)
    if center is None or R is None:
        center,R,_=params(x)
    w=x[:,:2]-center
    r=np.linalg.norm(w,axis=1)
    if r.min()<1e-5: raise ValueError('Curve enters excluded axis')
    rt=R+alpha*(r-R)
    if rt.min()<=0: raise ValueError('Radial map violates injectivity')
    q=x.copy()
    q[:,:2]=center+(rt/r)[:,None]*w
    q*=scale
    return q

def winding_number_xy(x,center=None):
    if center is None:center,_,_=params(x)
    th=np.arctan2(x[:,1]-center[1],x[:,0]-center[0]);delta=np.angle(np.exp(1j*(np.roll(th,-1)-th)))
    winding=delta.sum()/(2*np.pi)
    if abs(winding-round(winding))>1e-6:raise ValueError('nonintegral angular winding')
    return int(round(winding))

def area_vector(x):
    return .5*np.cross(x,np.roll(x,-1,axis=0)).sum(axis=0)

def toroidal_metrics(x, center, R):
    r=np.linalg.norm(x[:,:2]-center,axis=1)
    major=R
    rho=r-major
    minor=np.sqrt(rho**2+x[:,2]**2)
    return {'major_radius':float(major),'max_minor_envelope':float(minor.max()),
            'minor_to_major':float(minor.max()/major),
            'radial_spread_to_major':float((np.max(r)-np.min(r))/(2*major)),
            'median_radius':float(np.median(r))}

def approximate_curvature(x):
    v1=x-np.roll(x,1,axis=0);v2=np.roll(x,-1,axis=0)-x
    L1=np.linalg.norm(v1,axis=1);L2=np.linalg.norm(v2,axis=1)
    dot=np.sum(v1*v2,axis=1)/(L1*L2)
    angle=np.arccos(np.clip(dot,-1,1))
    return angle/(.5*(L1+L2))
