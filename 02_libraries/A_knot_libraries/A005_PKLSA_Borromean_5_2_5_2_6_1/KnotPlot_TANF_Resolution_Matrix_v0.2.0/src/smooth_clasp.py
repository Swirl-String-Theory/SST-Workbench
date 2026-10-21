"""RoundFolded near-unknot smooth-clasp family.

At fixed planar polar angle theta, use the positive radial affine map
 r -> R + alpha(theta) (r-R), with alpha(theta)>0.
For a source curve excluding its polar axis, this is an ambient embedding in
that annular region. alpha is boosted smoothly near the lower clasp, avoiding
artificially pinching the bottom fold when the rest of the knot is compressed.
The original TikZ approximation and over/under crossing lifts remain input.
"""
from __future__ import annotations
import numpy as np
from scipy.interpolate import CubicSpline
from near_unknot import params

PROFILES={
    'SOFT':{'radial_fraction':0.19,'bottom_fraction':0.62,'bottom_width_rad':0.55,'scale':2.50,'visual_cyl_rad':0.07},
    'BALANCED':{'radial_fraction':0.16,'bottom_fraction':0.44,'bottom_width_rad':0.45,'scale':2.50,'visual_cyl_rad':0.06},
    'TIGHT':{'radial_fraction':0.12,'bottom_fraction':0.30,'bottom_width_rad':0.35,'scale':2.50,'visual_cyl_rad':0.045},
}


def fold_map(x,profile):
    p=PROFILES[profile]
    center,R,_=params(x)
    x=np.asarray(x,dtype=float)
    v=x[:,:2]-center
    r=np.linalg.norm(v,axis=1)
    if np.any(r<=0):raise ValueError('Polar origin encountered')
    theta=np.arctan2(v[:,1],v[:,0])
    # Bottom is the negative-y direction, continuously wrapped.
    # Periodic C-infinity angular bump: unlike a wrapped Gaussian, has no seam at ±pi.
    angular_bump=np.exp((np.cos(theta+np.pi/2)-1.0)/(p['bottom_width_rad']**2))
    alpha=p['radial_fraction']+(p['bottom_fraction']-p['radial_fraction'])*angular_bump
    rp=R+alpha*(r-R)
    if np.min(rp)<=0 or np.min(alpha)<=0:raise ValueError('Radial map ceased to be injective')
    out=x.copy()
    out[:,:2]=center+(rp/r)[:,None]*v
    out*=p['scale']*12.
    return out,{'center_source':center.tolist(),'source_R':R,'alpha_min':float(np.min(alpha)),'alpha_max':float(np.max(alpha)),**p}


def resample_periodic_c2(x,n):
    """Arc-length periodic cubic interpolation of an analytic dense source.
    Knot invariants and clearance MUST be checked again on returned polyline.
    """
    x=np.asarray(x,dtype=float)
    d=np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1)
    if np.min(d)<=1e-12:raise ValueError('Repeated dense vertex')
    s=np.r_[0.,np.cumsum(d)]
    spline=CubicSpline(s,np.vstack([x,x[0]]),bc_type='periodic')
    return np.asarray(spline(np.arange(n)*s[-1]/n))
