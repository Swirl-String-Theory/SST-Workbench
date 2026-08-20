from __future__ import annotations
import numpy as np
from .native import field_velocity


def _fit(y,X):
    q=np.linalg.lstsq(X,y,rcond=None)[0];p=X@q;ss=np.sum((y-p)**2);st=np.sum((y-y.mean())**2)
    return float(1-ss/max(st,1e-30)),q,float(ss)


def fit_free_power_exponent(r,p,nu_min=.10,nu_max=4.0,nu_steps=157):
    """Blind free exponent fit p(r)=A+B/r^nu; no gravity target enters the fit."""
    r=np.asarray(r,float);p=np.asarray(p,float)
    m=np.isfinite(r)&np.isfinite(p)&(r>0);r=r[m];p=p[m]
    if len(r)<4:return {'nu_best':float('nan'),'r2_best':float('nan'),'coeff':float('nan'),'offset':float('nan'),'boundary_hit':True}
    nus=np.linspace(float(nu_min),float(nu_max),int(nu_steps));best=None
    for nu in nus:
        X=np.c_[np.ones_like(r),r**(-nu)];r2,q,ss=_fit(p,X);key=(ss,-r2)
        if best is None or key<best[0]:best=(key,float(nu),float(r2),q)
    _,nu,r2,q=best;step=(float(nu_max)-float(nu_min))/max(int(nu_steps)-1,1)
    boundary=(nu<=float(nu_min)+.51*step or nu>=float(nu_max)-.51*step)
    return {'nu_best':nu,'r2_best':r2,'offset':float(q[0]),'coeff':float(q[1]),'boundary_hit':bool(boundary),'nu_min':float(nu_min),'nu_max':float(nu_max),'nu_steps':int(nu_steps)}


def fibonacci_sphere(n):
    n=max(int(n),1);i=np.arange(n,dtype=float);z=1.0-2.0*(i+.5)/n;phi=np.pi*(3.0-np.sqrt(5.0))*i;r=np.sqrt(np.maximum(0.0,1.0-z*z))
    return np.c_[r*np.cos(phi),r*np.sin(phi),z]


def free_space_potential_from_source(samples,source_xyz,source_values,cell_volume=1.0,softening=0.0,chunk=64):
    """Open-boundary Poisson Green function: p(x)=-(4pi)^-1 int S(x')/|x-x'| dV'."""
    x=np.asarray(samples,float);y=np.asarray(source_xyz,float);s=np.asarray(source_values,float).reshape(-1);out=np.empty(len(x),float);eps2=float(softening)**2
    for i0 in range(0,len(x),int(chunk)):
        q=x[i0:i0+int(chunk),None,:]-y[None,:,:];d=np.sqrt(np.sum(q*q,axis=2)+eps2);out[i0:i0+int(chunk)]=-(float(cell_volume)/(4*np.pi))*np.sum(s[None,:]/np.maximum(d,1e-15),axis=1)
    return out


def _source_grid(points,offsets,gammas,core,n,box_half,rho):
    n=int(n);box_half=float(box_half);h=2*box_half/n;ax=-box_half+(np.arange(n)+.5)*h
    X,Y,Z=np.meshgrid(ax,ax,ax,indexing='ij');xyz=np.c_[X.ravel(),Y.ravel(),Z.ravel()]
    v=field_velocity(xyz,points,offsets,gammas,core).reshape(n,n,n,3);grad=np.empty((n,n,n,3,3),float)
    for i in range(3):
        for j in range(3):grad[...,i,j]=np.gradient(v[...,i],h,axis=j,edge_order=2)
    source=-float(rho)*np.einsum('...ij,...ji->...',grad,grad);return xyz,source.reshape(-1),h


def _moments(xyz,s,dv):
    q=float(np.sum(s)*dv);absq=float(np.sum(np.abs(s))*dv);dip=np.sum(xyz*s[:,None],axis=0)*dv
    r2=np.sum(xyz*xyz,axis=1);Q=np.zeros((3,3),float)
    for i in range(3):
        for j in range(3):Q[i,j]=float(np.sum((3*xyz[:,i]*xyz[:,j]-(r2 if i==j else 0.0))*s)*dv)
    return q,absq,dip,Q


def pressure_poisson_metrics(points,offsets,gammas,core,grid_n=14,box_half=4.5,rho=1.0,fit_cfg=None):
    """Free-space pressure-Poisson diagnostics and source multipoles.

    v0.2.1 deliberately does not subtract the source mean and does not remove k=0.
    """
    fit_cfg=fit_cfg or {};n=int(grid_n);box_half=float(box_half);xyz,source,h=_source_grid(points,offsets,gammas,core,n,box_half,rho);dv=h**3
    q,absq,dip,quad=_moments(xyz,source,dv);soft=float(fit_cfg.get('green_softening_cells',.55))*h;dirs=fibonacci_sphere(int(fit_cfg.get('angular_samples',32)))
    cmax=float(fit_cfg.get('center_radius',.35));slo=float(fit_cfg.get('shell_lo',1.5));shi=float(fit_cfg.get('shell_hi',2.0));sr=.5*(slo+shi)
    center=float(free_space_potential_from_source(np.zeros((1,3)),xyz,source,dv,soft)[0]);shell=float(np.mean(free_space_potential_from_source(sr*dirs,xyz,source,dv,soft)));deficit=center-shell
    rlo=float(fit_cfg.get('radial_fit_lo',3.0));rhi=float(fit_cfg.get('radial_fit_hi',8.0));nbins=int(fit_cfg.get('radial_bins',12));rc=np.linspace(rlo,rhi,nbins);pm=[]
    for r in rc:pm.append(float(np.mean(free_space_potential_from_source(float(r)*dirs,xyz,source,dv,soft))))
    pm=np.asarray(pm,float)
    if len(rc)>=3:
        X1=np.c_[np.ones_like(rc),1/rc];X2=np.c_[np.ones_like(rc),1/(rc*rc)];r21,q1,_=_fit(pm,X1);r22,q2,_=_fit(pm,X2)
    else:r21=r22=float('nan');q1=q2=np.array([np.nan,np.nan])
    free=fit_free_power_exponent(rc,pm,float(fit_cfg.get('nu_min',.10)),float(fit_cfg.get('nu_max',4.0)),int(fit_cfg.get('nu_steps',157)))
    return {
        'pressure_solver':'free_space_green_direct','pressure_center_minus_shell':float(deficit),'pressure_center':center,'pressure_shell':shell,
        'pressure_source_mean':float(np.mean(source)),'pressure_source_abs_mean':float(np.mean(np.abs(source))),
        'source_monopole':q,'source_abs_integral':absq,'source_monopole_fraction_abs':float(abs(q)/max(absq,1e-30)),
        'source_dipole':[float(x) for x in dip],'source_dipole_norm':float(np.linalg.norm(dip)),'source_quadrupole_frobenius':float(np.linalg.norm(quad)),
        'r2_1_over_r':r21,'r2_1_over_r2':r22,'r2_advantage_1_over_r':float(r21-r22),'fit_coeff_1_over_r':float(q1[1]),'fit_coeff_1_over_r2':float(q2[1]),
        'far_profile_nu_best':free['nu_best'],'far_profile_r2_best':free['r2_best'],'far_profile_coeff_best':free['coeff'],'far_profile_offset_best':free['offset'],'far_profile_nu_boundary_hit':free['boundary_hit'],
        'radial_r':[float(x) for x in rc],'radial_p':[float(x) for x in pm],'grid_n':n,'box_half':box_half,'grid_spacing':float(h),'radial_fit_lo':rlo,'radial_fit_hi':rhi,
    }


def pressure_convergence_ladder(points,offsets,gammas,core,ladder,rho=1.0,fit_cfg=None):
    rows=[pressure_poisson_metrics(points,offsets,gammas,core,int(ent['grid_n']),float(ent['box_half']),rho,fit_cfg) for ent in (ladder or [])]
    nus=np.asarray([r['far_profile_nu_best'] for r in rows if np.isfinite(r['far_profile_nu_best']) and not r['far_profile_nu_boundary_hit']],float);dps=np.asarray([r['pressure_center_minus_shell'] for r in rows if np.isfinite(r['pressure_center_minus_shell'])],float);qs=np.asarray([r['source_monopole'] for r in rows if np.isfinite(r['source_monopole'])],float)
    qabs=np.abs(qs);qrel=float(np.ptp(qabs)/max(np.median(qabs),1e-30)) if len(qabs)>1 else 0.0 if len(qabs)==1 else float('nan')
    return {'levels':rows,'n_levels':len(rows),'nu_median':float(np.median(nus)) if len(nus) else float('nan'),'nu_mad':float(np.median(np.abs(nus-np.median(nus)))) if len(nus) else float('nan'),'nu_span':float(np.ptp(nus)) if len(nus)>1 else 0.0 if len(nus)==1 else float('nan'),'monopole_median':float(np.median(qs)) if len(qs) else float('nan'),'monopole_abs_relative_span':qrel,'pressure_deficit_median':float(np.median(dps)) if len(dps) else float('nan')}
