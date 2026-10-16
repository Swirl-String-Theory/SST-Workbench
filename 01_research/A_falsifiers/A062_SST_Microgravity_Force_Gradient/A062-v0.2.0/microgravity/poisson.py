"""Exploratory periodic-grid Euler-Poisson cross-pressure diagnostic.

This is NOT an isolated-space converged Poisson solver near a canonical core;
results cannot certify momentum exchange without the full unsteady flux balance.
"""
from __future__ import annotations
import numpy as np
from .filament import induced_velocity,rotate_x

def poisson_cross(xa,xb,core=0.02817,R=1.5,n=24):
    """Calculate p_cross / (rho (Gamma/L)^2) on a periodic cube.

    External velocity for both vortices is computed from 3-D Biot-Savart. Numerical
    gradients are finite differences, then periodic Poisson solved spectrally.
    """
    b=rotate_x(xb,0.)+np.array([0,0,R]);
    half=R/2+0.62;center=R/2
    dx=2*half/n
    grid=np.linspace(-half+dx/2,half-dx/2,n)
    x,y,z=np.meshgrid(grid,grid,grid+center,indexing='ij')
    pos=np.stack([x.ravel(),y.ravel(),z.ravel()],axis=1)
    ua=induced_velocity(pos,xa,core,block=1800).reshape((n,n,n,3))
    ub=induced_velocity(pos,b,core,block=1800).reshape((n,n,n,3))
    ga=np.stack([np.stack(np.gradient(ua[...,j],dx,edge_order=2),axis=-1) for j in range(3)],axis=-2)
    gb=np.stack([np.stack(np.gradient(ub[...,j],dx,edge_order=2),axis=-1) for j in range(3)],axis=-2)
    # ga[i,j] = partial_j u_i: contraction tr(ga @ gb) and inverse.
    src=-np.einsum('...ij,...ji->...',ga,gb)-np.einsum('...ij,...ji->...',gb,ga)
    k=2*np.pi*np.fft.fftfreq(n,d=dx)
    kx,ky,kz=np.meshgrid(k,k,k,indexing='ij'); k2=kx*kx+ky*ky+kz*kz
    shat=np.fft.fftn(src-src.mean()); phat=np.zeros_like(shat)
    mask=k2>0;phat[mask]=-shat[mask]/k2[mask]
    p=np.fft.ifftn(phat).real
    roundtrip=np.fft.ifftn(-k2*phat).real
    residual=np.linalg.norm((src-src.mean())-roundtrip)/max(np.linalg.norm(src-src.mean()),1e-30)
    div_a=ga[...,0,0]+ga[...,1,1]+ga[...,2,2]
    div_b=gb[...,0,0]+gb[...,1,1]+gb[...,2,2]
    grad_norm=np.linalg.norm(ga)+np.linalg.norm(gb)
    interior=(slice(2,-2),)*3
    div_l2=(np.linalg.norm(div_a[interior])+np.linalg.norm(div_b[interior]))/max(grad_norm,1e-30)
    return {'status':'PERIODIC_NUMERICAL_DIAGNOSTIC_ONLY',
            'n':n,'box_half_length_dimensionless':half,'core_radius_grid_cells':core/dx,
            'poisson_inversion_rel_residual':float(residual),'finite_diff_div_over_grad':float(div_l2),
            'max_cross_pressure_normalized':float(np.max(np.abs(p))),
            'source_zero_mode_removed':float(src.mean()),
            'limits':'Periodic pressure is not isolated-space pressure; canonical core underresolved; no physical force certification.'}
