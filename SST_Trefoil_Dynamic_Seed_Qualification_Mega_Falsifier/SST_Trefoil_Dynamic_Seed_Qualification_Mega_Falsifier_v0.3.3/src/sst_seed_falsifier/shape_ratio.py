"""Target-free trefoil anisotropy observables.

No target constant is used.  The observable is inferred only from the embedded
centreline after arclength resampling and rigid alignment.
"""
from __future__ import annotations
import numpy as np
from .geometry import center,resample_closed,align_cyclic


def _frame(x):
    y=center(np.asarray(x,float))
    cov=(y.T@y)/max(len(y),1)
    vals,vecs=np.linalg.eigh(cov)
    order=np.argsort(vals)
    axis=vecs[:,order[0]]
    e1=vecs[:,order[-1]]
    e2=np.cross(axis,e1); e2/=max(np.linalg.norm(e2),1e-30)
    e1=np.cross(e2,axis); e1/=max(np.linalg.norm(e1),1e-30)
    return axis,e1,e2,vals[order]


def trefoil_shape_ratio(x, *, axis=None, e1=None, e2=None, toroidal_winding=2, poloidal_mode=3):
    """Estimate R_radial/r_axial from an ordered trefoil centreline.

    The toroidal phase is recovered from the projected azimuth around the PCA
    axis.  For T(2,3), theta ~= 2 t, hence t=theta/2.  Fourier amplitudes of the
    m=3 radial and axial modulations then estimate R_radial and r_axial.
    Returned amplitudes have the same length unit as ``x``; chi is dimensionless.
    """
    y=resample_closed(np.asarray(x,float),len(x)); y=center(y)
    if axis is None or e1 is None or e2 is None:
        axis,e1,e2,eigs=_frame(y)
    else:
        axis=np.asarray(axis,float); axis/=max(np.linalg.norm(axis),1e-30)
        e1=np.asarray(e1,float); e1-=np.dot(e1,axis)*axis; e1/=max(np.linalg.norm(e1),1e-30)
        e2=np.asarray(e2,float); e2-=np.dot(e2,axis)*axis+np.dot(e2,e1)*e1; e2/=max(np.linalg.norm(e2),1e-30)
        eigs=np.linalg.eigvalsh((y.T@y)/max(len(y),1))
    u=y@e1; v=y@e2; z=y@axis
    theta=np.unwrap(np.arctan2(v,u))
    # Remove direction sign; amplitude is phase-invariant.
    t=(theta-theta[0])/float(toroidal_winding)
    rho=np.sqrt(u*u+v*v)
    # Least-squares harmonic amplitudes are used instead of a simple DFT because
    # uniform arclength samples are generally nonuniform in torus parameter t.
    w=float(poloidal_mode)*t
    A=np.c_[np.ones(len(t)),np.cos(w),np.sin(w)]
    cr,*_=np.linalg.lstsq(A,rho,rcond=None); cz,*_=np.linalg.lstsq(A,z,rcond=None)
    ar=float(np.hypot(cr[1],cr[2])); az=float(np.hypot(cz[1],cz[2]))
    chi=float(ar/max(az,1e-30))
    winding=float((theta[-1]-theta[0])/(2*np.pi)) if len(theta)>1 else 0.0
    return {'R_radial':float(ar),'r_axial':float(az),'chi_eff':chi,
            'toroidal_winding_estimate':winding,'pca_eigenvalues':[float(q) for q in np.sort(eigs)],
            'target_free':True}


def trefoil_shape_ratio_series(traj,x0,coarse_stride=4):
    ref=resample_closed(np.asarray(x0,float),len(x0)); axis,e1,e2,_=_frame(ref)
    values=[]
    for x in np.asarray(traj['x']):
        y=resample_closed(np.asarray(x,float),len(ref))
        aligned,_,_,_,_=align_cyclic(y,ref,coarse_stride)
        values.append(trefoil_shape_ratio(aligned,axis=axis,e1=e1,e2=e2))
    chi=np.asarray([v['chi_eff'] for v in values],float)
    return {'t':[float(t) for t in np.asarray(traj['t'],float)],
            'chi_eff':[float(v) for v in chi],
            'chi_initial':float(chi[0]) if len(chi) else float('nan'),
            'chi_final':float(chi[-1]) if len(chi) else float('nan'),
            'chi_median':float(np.median(chi)) if len(chi) else float('nan'),
            'chi_range':float(np.ptp(chi)) if len(chi) else float('nan'),
            'R_radial_initial':values[0]['R_radial'] if values else float('nan'),
            'r_axial_initial':values[0]['r_axial'] if values else float('nan'),
            'observable_used_in_score':False,'target_free':True}
