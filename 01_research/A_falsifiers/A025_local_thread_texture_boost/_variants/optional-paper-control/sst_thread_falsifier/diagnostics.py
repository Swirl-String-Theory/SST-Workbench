from __future__ import annotations
import numpy as np
from .native_ext.core import filament_velocity


def field_solenoidal_diagnostics(center, rg, thread_points, thread_offsets, thread_gammas, thread_core,
                                 halfwidth_rg=0.75, grid_n=7, force_python=False, skip_build=False):
    """Finite-difference audit of div(v) and div(curl(v)) in the local patch."""
    grid_n=max(5,int(grid_n)); grid_n += (grid_n%2==0)
    c=np.asarray(center,float); rg=float(rg); h=float(halfwidth_rg)*rg
    ax=np.linspace(-h,h,grid_n); X,Y,Z=np.meshgrid(ax,ax,ax,indexing='ij')
    probes=np.c_[X.ravel(),Y.ravel(),Z.ravel()]+c
    v=filament_velocity(probes,thread_points,thread_offsets,thread_gammas,thread_core,
                        force_python=force_python,skip_build=skip_build).reshape(grid_n,grid_n,grid_n,3)
    dx=float(ax[1]-ax[0])
    def d(f,axis):
        slp=[slice(1,-1)]*3; slm=[slice(1,-1)]*3
        slp[axis]=slice(2,None); slm[axis]=slice(None,-2)
        return (f[tuple(slp)]-f[tuple(slm)])/(2.0*dx)
    dvx_dx=d(v[...,0],0); dvy_dy=d(v[...,1],1); dvz_dz=d(v[...,2],2); div_v=dvx_dx+dvy_dy+dvz_dz
    dvy_dz=d(v[...,1],2); dvz_dy=d(v[...,2],1); dvz_dx=d(v[...,2],0); dvx_dz=d(v[...,0],2); dvx_dy=d(v[...,0],1); dvy_dx=d(v[...,1],0)
    omega=np.stack([dvz_dy-dvy_dz,dvx_dz-dvz_dx,dvy_dx-dvx_dy],axis=-1)
    if grid_n>=7:
        def di(f,axis):
            slp=[slice(1,-1)]*3; slm=[slice(1,-1)]*3
            slp[axis]=slice(2,None); slm[axis]=slice(None,-2)
            return (f[tuple(slp)]-f[tuple(slm)])/(2.0*dx)
        div_omega=di(omega[...,0],0)+di(omega[...,1],1)+di(omega[...,2],2)
    else: div_omega=np.zeros((1,1,1),float)
    v_rms=float(np.sqrt(np.mean(np.sum(v*v,axis=-1)))); omega_rms=float(np.sqrt(np.mean(np.sum(omega*omega,axis=-1))))
    divv_rms=float(np.sqrt(np.mean(div_v*div_v))); divw_rms=float(np.sqrt(np.mean(div_omega*div_omega)))
    return {"grid_n":grid_n,"halfwidth_rg":float(halfwidth_rg),"velocity_rms":v_rms,"vorticity_rms":omega_rms,
            "div_velocity_rms":divv_rms,"div_vorticity_rms":divw_rms,
            "normalized_div_velocity":float(rg*divv_rms/max(v_rms,1e-300)),
            "normalized_div_vorticity":float(rg*divw_rms/max(omega_rms,1e-300))}


def background_field_relative_difference(eval_points,bundle_a,bundle_b,core_radius,force_python=False,skip_build=False):
    va=filament_velocity(eval_points,bundle_a['points'],bundle_a['offsets'],bundle_a['gammas'],core_radius,
                         force_python=force_python,skip_build=skip_build)
    vb=filament_velocity(eval_points,bundle_b['points'],bundle_b['offsets'],bundle_b['gammas'],core_radius,
                         force_python=force_python,skip_build=skip_build)
    den=max(float(np.linalg.norm(va)),float(np.linalg.norm(vb)),1e-300)
    return float(np.linalg.norm(va-vb)/den)


def _point_to_segment_min(points,poly,offsets,chunk=128):
    P=np.asarray(points,float); Q=np.asarray(poly,float); O=np.asarray(offsets,np.int64); best=float('inf')
    for lo,hi in zip(O[:-1],O[1:]):
        q=Q[int(lo):int(hi)]
        if len(q)<2: continue
        A=q; B=np.roll(q,-1,axis=0); D=B-A; D2=np.einsum('ij,ij->i',D,D)
        for j in range(0,len(A),int(chunk)):
            aa=A[j:j+chunk]; dd=D[j:j+chunk]; d2=D2[j:j+chunk]
            R=P[:,None,:]-aa[None,:,:]
            t=np.einsum('pji,ji->pj',R,dd)/np.maximum(d2[None,:],1e-300); t=np.clip(t,0.0,1.0)
            C=aa[None,:,:]+t[:,:,None]*dd[None,:,:]
            dist2=np.sum((P[:,None,:]-C)**2,axis=2); best=min(best,float(np.sqrt(np.min(dist2))))
    return best


def minimum_centerline_clearance(knot_points,knot_offsets,thread_points,thread_offsets):
    """Symmetric point-to-segment clearance proxy between knot and thread centerlines.

    Using both directions strongly reduces missed crossings relative to point-point tests,
    while avoiding an O(NM) scalar segment-segment loop in the Python report stage.
    """
    a=_point_to_segment_min(knot_points,thread_points,thread_offsets)
    b=_point_to_segment_min(thread_points,knot_points,knot_offsets)
    return float(min(a,b))


def segment_uniformity(points,offsets):
    p=np.asarray(points,float); o=np.asarray(offsets,np.int64); cvs=[]; ratios=[]
    for lo,hi in zip(o[:-1],o[1:]):
        q=p[int(lo):int(hi)]
        if len(q)<3: continue
        ds=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1); m=float(np.mean(ds)); s=float(np.std(ds))
        cvs.append(s/max(m,1e-300)); ratios.append(float(np.max(ds)/max(float(np.min(ds)),1e-300)))
    return {"segment_cv_max":float(max(cvs) if cvs else 0.0),"segment_ratio_max":float(max(ratios) if ratios else 1.0)}
