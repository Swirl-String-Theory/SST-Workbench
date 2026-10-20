"""Dimensional Euler-vorticity residual for time resolved 3D velocity grids.

Physical pass requires independent field provenance and spatial/time refinements;
this module computes verification observables only, never promotes itself to
experimentally or physically certified status.
"""
from __future__ import annotations
import numpy as np


def _grad(a,coords,axis):
    return np.gradient(a,coords,axis=axis,edge_order=2)


def diagnose_velocity_grid(t,x,y,z,u):
    t,x,y,z=[np.asarray(v,dtype=float) for v in (t,x,y,z)]
    u=np.asarray(u,dtype=float)
    if any(v.ndim!=1 or len(v)<3 or np.any(np.diff(v)<=0) for v in (t,x,y,z)):
        raise ValueError('t,x,y,z must be increasing 1D grids >=3 samples')
    if len(t)<5 or min(map(len,(x,y,z)))<5:
        raise ValueError('Euler diagnostic needs >=5 positions/time samples')
    if u.shape!=(len(t),len(x),len(y),len(z),3) or not np.isfinite(u).all():
        raise ValueError('u shape must be (T,Nx,Ny,Nz,3) in m/s')
    spatial_axes=(1,2,3)
    derivatives=np.empty(u.shape+(3,),dtype=float)
    for j,coordinate in enumerate((x,y,z)):
        derivatives[...,j]=np.gradient(u,coordinate,axis=spatial_axes[j],edge_order=2)
    # derivatives[t,x,y,z, component, coordinate]
    div=np.einsum('...ii->...',derivatives)
    omega=np.empty_like(u)
    omega[...,0]=derivatives[...,2,1]-derivatives[...,1,2]
    omega[...,1]=derivatives[...,0,2]-derivatives[...,2,0]
    omega[...,2]=derivatives[...,1,0]-derivatives[...,0,1]
    dd_omega=np.empty(omega.shape+(3,),dtype=float)
    for j,coordinate in enumerate((x,y,z)):
        dd_omega[...,j]=np.gradient(omega,coordinate,axis=spatial_axes[j],edge_order=2)
    dwdt=np.gradient(omega,t,axis=0,edge_order=2)
    adv=np.einsum('...j,...ij->...i',u,dd_omega)
    stretch=np.einsum('...j,...ij->...i',omega,derivatives)
    residual=dwdt+adv-stretch
    core=(slice(1,-1),)*4
    co=(core+(slice(None),))
    def rms(a):return float(np.sqrt(np.mean(np.square(a))))
    scale_T=float(t[-1]-t[0]);omega_rms=rms(omega[co]);gradient_rms=rms(derivatives[co]);speed_rms=rms(u[co])
    # Zero-vorticity cases use dimensional absolute errors only: no singular normalized residual.
    residual_abs=rms(residual[co]);div_abs=rms(div[core])
    scale=omega_rms/scale_T + speed_rms*gradient_rms/max(min(np.diff(x).min(),np.diff(y).min(),np.diff(z).min()),1e-99)
    euler_rel=(residual_abs/scale if scale>1e-30 else None)
    div_rel=(div_abs/gradient_rms if gradient_rms>1e-30 else None)
    return {'status':'DIAGNOSTIC_ONLY',
       'divergence_rms_per_s':div_abs,'gradient_rms_per_s':gradient_rms,'divergence_relative':div_rel,
       'omega_rms_per_s':omega_rms,'euler_vorticity_residual_rms_per_s2':residual_abs,
       'euler_residual_relative':euler_rel, 'time_points':len(t),'grid_shape':list(u.shape[1:4]),
       'pass_screen':bool(div_abs<1e-8 and residual_abs<1e-8),
       'unit_contract':{'t':'s','xyz':'m','u':'m/s','omega':'1/s','Euler_residual':'1/s^2'},
       'limitation':'Single grid check; cannot establish spatial/temporal convergence, circulation transport, or physical source independence.'}


def diagnose_vertex_transport(t,filaments,present,u_vertices,material_ids=None):
    """Centerline displacement against supplied measured 3D velocity at same MATERIAL labels.

    Does not certify Euler, unless material IDs and independent grid solver prove provenance.
    """
    t=np.asarray(t,dtype=float);filaments=np.asarray(filaments,dtype=float)
    present=np.asarray(present,dtype=bool);u=np.asarray(u_vertices,dtype=float)
    if u.shape!=filaments.shape:raise ValueError('vertex velocity shape mismatch')
    if material_ids is None or len(material_ids)!=present.shape[1]:
        return {'status':'UNRESOLVED_NO_MATERIAL_IDENTITIES'}
    active=present[1:-1]&present[:-2]&present[2:]
    dx=(filaments[2:]-filaments[:-2])/(t[2:,None,None,None]-t[:-2,None,None,None])
    uu=u[1:-1]
    if not active.any():return {'status':'UNRESOLVED_NO_CONSECUTIVE_MATERIAL_TRACKS'}
    dif=(dx-uu)[active]; ref=uu[active]
    num=np.sqrt(np.mean(dif*dif));den=np.sqrt(np.mean(ref*ref))
    return {'status':'DIAGNOSTIC_ONLY','material_ids':list(map(str,material_ids)),
        'rms_residual_m_s':float(num),'relative_residual':float(num/max(den,1e-30)),
        'n_active_track_pairs':int(active.sum()),
        'warning':'Centerline vertex indexing must be material-consistent, not arclength-remapped.'}
