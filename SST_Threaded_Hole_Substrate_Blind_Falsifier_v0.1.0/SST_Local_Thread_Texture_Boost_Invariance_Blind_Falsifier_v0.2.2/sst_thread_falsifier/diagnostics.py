from __future__ import annotations
import numpy as np
from .native_ext.core import filament_velocity


def field_solenoidal_diagnostics(center, rg, thread_points, thread_offsets, thread_gammas, thread_core,
                                 halfwidth_rg=0.75, grid_n=7, force_python=False, skip_build=False):
    """Finite-difference audit of ∇·v=0 and ∇·(∇×v)=0 in the local patch.

    The exact regularized segment kernel is divergence-free; these diagnostics test the
    discrete implementation and the committed closed-filament field on a small cube.
    """
    grid_n=max(5,int(grid_n))
    if grid_n%2==0: grid_n+=1
    c=np.asarray(center,float); rg=float(rg)
    h=float(halfwidth_rg)*rg
    ax=np.linspace(-h,h,grid_n)
    X,Y,Z=np.meshgrid(ax,ax,ax,indexing='ij')
    probes=np.c_[X.ravel(),Y.ravel(),Z.ravel()]+c
    v=filament_velocity(probes,thread_points,thread_offsets,thread_gammas,thread_core,
                        force_python=force_python,skip_build=skip_build).reshape(grid_n,grid_n,grid_n,3)
    dx=float(ax[1]-ax[0])
    # Central finite-difference derivatives on the interior to avoid one-sided edge noise.
    def d(f,axis):
        slp=[slice(1,-1)]*3; slm=[slice(1,-1)]*3
        slp[axis]=slice(2,None); slm[axis]=slice(None,-2)
        return (f[tuple(slp)]-f[tuple(slm)])/(2.0*dx)
    # derivatives have shape (n-2)^3 only if all non-axis slices are interior
    dvx_dx=d(v[...,0],0); dvy_dy=d(v[...,1],1); dvz_dz=d(v[...,2],2)
    div_v=dvx_dx+dvy_dy+dvz_dz
    # For curl, make full-ish interior arrays; each derivative is common (n-2)^3.
    dvy_dz=d(v[...,1],2); dvz_dy=d(v[...,2],1)
    dvz_dx=d(v[...,2],0); dvx_dz=d(v[...,0],2)
    dvx_dy=d(v[...,0],1); dvy_dx=d(v[...,1],0)
    omega=np.stack([dvz_dy-dvy_dz, dvx_dz-dvz_dx, dvy_dx-dvx_dy],axis=-1)
    # divergence of omega on one further interior shell
    if grid_n >= 7:
        def di(f,axis):
            slp=[slice(1,-1)]*3; slm=[slice(1,-1)]*3
            slp[axis]=slice(2,None); slm[axis]=slice(None,-2)
            return (f[tuple(slp)]-f[tuple(slm)])/(2.0*dx)
        div_omega=di(omega[...,0],0)+di(omega[...,1],1)+di(omega[...,2],2)
    else:
        div_omega=np.zeros((1,1,1),float)
    v_rms=float(np.sqrt(np.mean(np.sum(v*v,axis=-1))))
    omega_rms=float(np.sqrt(np.mean(np.sum(omega*omega,axis=-1))))
    divv_rms=float(np.sqrt(np.mean(div_v*div_v)))
    divw_rms=float(np.sqrt(np.mean(div_omega*div_omega)))
    return {
        "grid_n":grid_n,
        "halfwidth_rg":float(halfwidth_rg),
        "velocity_rms":v_rms,
        "vorticity_rms":omega_rms,
        "div_velocity_rms":divv_rms,
        "div_vorticity_rms":divw_rms,
        "normalized_div_velocity":float(rg*divv_rms/max(v_rms,1e-300)),
        "normalized_div_vorticity":float(rg*divw_rms/max(omega_rms,1e-300)),
    }


def background_field_relative_difference(eval_points, bundle_a, bundle_b, core_radius,
                                         force_python=False, skip_build=False):
    va=filament_velocity(eval_points,bundle_a['points'],bundle_a['offsets'],bundle_a['gammas'],core_radius,
                         force_python=force_python,skip_build=skip_build)
    vb=filament_velocity(eval_points,bundle_b['points'],bundle_b['offsets'],bundle_b['gammas'],core_radius,
                         force_python=force_python,skip_build=skip_build)
    den=max(float(np.linalg.norm(va)),float(np.linalg.norm(vb)),1e-300)
    return float(np.linalg.norm(va-vb)/den)
