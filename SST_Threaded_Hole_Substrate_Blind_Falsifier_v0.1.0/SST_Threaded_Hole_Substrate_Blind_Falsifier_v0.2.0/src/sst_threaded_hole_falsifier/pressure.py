from __future__ import annotations
import numpy as np
from .native import field_velocity


def _fit(y,X):
    q=np.linalg.lstsq(X,y,rcond=None)[0];p=X@q;ss=np.sum((y-p)**2);st=np.sum((y-y.mean())**2)
    return float(1-ss/max(st,1e-30)),q,float(ss)


def fit_free_power_exponent(r,p,nu_min=.10,nu_max=4.0,nu_steps=157):
    """Blind free exponent fit p(r)=A+B/r^nu using a preregistered grid.

    No Newtonian exponent is supplied to this search.  The target nu=1 is used
    only after the blind result tree has been sealed and identities are revealed.
    """
    r=np.asarray(r,float);p=np.asarray(p,float)
    m=np.isfinite(r)&np.isfinite(p)&(r>0);r=r[m];p=p[m]
    if len(r)<4:return {'nu_best':float('nan'),'r2_best':float('nan'),'coeff':float('nan'),'offset':float('nan'),'boundary_hit':True}
    nus=np.linspace(float(nu_min),float(nu_max),int(nu_steps));best=None
    for nu in nus:
        X=np.c_[np.ones_like(r),r**(-nu)];r2,q,ss=_fit(p,X);key=(ss,-r2)
        if best is None or key<best[0]:best=(key,float(nu),float(r2),q)
    _,nu,r2,q=best
    step=(float(nu_max)-float(nu_min))/max(int(nu_steps)-1,1)
    boundary=(nu<=float(nu_min)+.51*step or nu>=float(nu_max)-.51*step)
    return {'nu_best':nu,'r2_best':r2,'offset':float(q[0]),'coeff':float(q[1]),'boundary_hit':bool(boundary),'nu_min':float(nu_min),'nu_max':float(nu_max),'nu_steps':int(nu_steps)}


def pressure_poisson_metrics(points,offsets,gammas,core,grid_n=14,box_half=2.4,rho=1.0,fit_cfg=None):
    fit_cfg=fit_cfg or {};n=int(grid_n);box_half=float(box_half)
    ax=np.linspace(-box_half,box_half,n,endpoint=False);h=2*box_half/n
    X,Y,Z=np.meshgrid(ax,ax,ax,indexing='ij');samples=np.c_[X.ravel(),Y.ravel(),Z.ravel()]
    v=field_velocity(samples,points,offsets,gammas,core).reshape(n,n,n,3)
    grad=np.empty((n,n,n,3,3))
    for i in range(3):
        for j in range(3): grad[...,i,j]=(np.roll(v[...,i],-1,axis=j)-np.roll(v[...,i],1,axis=j))/(2*h)
    source=-rho*np.einsum('...ij,...ji->...',grad,grad)
    shat=np.fft.fftn(source-source.mean());k=2*np.pi*np.fft.fftfreq(n,d=h);KX,KY,KZ=np.meshgrid(k,k,k,indexing='ij');k2=KX*KX+KY*KY+KZ*KZ;phat=np.zeros_like(shat);mask=k2>0;phat[mask]=-shat[mask]/k2[mask];p=np.fft.ifftn(phat).real
    r=np.sqrt(X*X+Y*Y+Z*Z)
    cmax=float(fit_cfg.get('center_radius',.35));slo=float(fit_cfg.get('shell_lo',min(1.45,.58*box_half)));shi=float(fit_cfg.get('shell_hi',min(1.95,.78*box_half)))
    cm=r<cmax;sm=(r>slo)&(r<shi);center=float(p[cm].mean()) if np.any(cm) else float('nan');shell=float(p[sm].mean()) if np.any(sm) else float('nan');deficit=float(center-shell)
    rlo=float(fit_cfg.get('radial_fit_lo',max(.55,.22*box_half)));rhi=float(fit_cfg.get('radial_fit_hi',min(2.05,.82*box_half)));nbins=int(fit_cfg.get('radial_bins',10));rbins=np.linspace(rlo,rhi,nbins+1);rc=[];pm=[]
    for a,b in zip(rbins[:-1],rbins[1:]):
        m=(r>=a)&(r<b)
        if np.any(m):rc.append(.5*(a+b));pm.append(float(p[m].mean()))
    rc=np.asarray(rc);pm=np.asarray(pm)
    if len(rc)>=3:
        X1=np.c_[np.ones_like(rc),1/rc];X2=np.c_[np.ones_like(rc),1/(rc*rc)];r21,q1,_=_fit(pm,X1);r22,q2,_=_fit(pm,X2)
    else:r21=r22=float('nan');q1=q2=np.array([np.nan,np.nan])
    free=fit_free_power_exponent(rc,pm,float(fit_cfg.get('nu_min',.10)),float(fit_cfg.get('nu_max',4.0)),int(fit_cfg.get('nu_steps',157)))
    return {
        'pressure_center_minus_shell':deficit,'pressure_center':center,'pressure_shell':shell,
        'pressure_source_mean':float(source.mean()),'pressure_source_abs_mean':float(np.mean(np.abs(source))),
        'r2_1_over_r':r21,'r2_1_over_r2':r22,'r2_advantage_1_over_r':float(r21-r22),
        'fit_coeff_1_over_r':float(q1[1]),'fit_coeff_1_over_r2':float(q2[1]),
        'far_profile_nu_best':free['nu_best'],'far_profile_r2_best':free['r2_best'],'far_profile_coeff_best':free['coeff'],'far_profile_offset_best':free['offset'],'far_profile_nu_boundary_hit':free['boundary_hit'],
        'radial_r':[float(x) for x in rc],'radial_p':[float(x) for x in pm],
        'grid_n':n,'box_half':box_half,'grid_spacing':float(h),'radial_fit_lo':rlo,'radial_fit_hi':rhi,
    }


def pressure_convergence_ladder(points,offsets,gammas,core,ladder,rho=1.0,fit_cfg=None):
    rows=[]
    for ent in ladder or []:
        rows.append(pressure_poisson_metrics(points,offsets,gammas,core,int(ent['grid_n']),float(ent['box_half']),rho,fit_cfg))
    nus=np.asarray([r['far_profile_nu_best'] for r in rows if np.isfinite(r['far_profile_nu_best']) and not r['far_profile_nu_boundary_hit']],float)
    dps=np.asarray([r['pressure_center_minus_shell'] for r in rows if np.isfinite(r['pressure_center_minus_shell'])],float)
    return {
        'levels':rows,
        'n_levels':len(rows),
        'nu_median':float(np.median(nus)) if len(nus) else float('nan'),
        'nu_mad':float(np.median(np.abs(nus-np.median(nus)))) if len(nus) else float('nan'),
        'nu_span':float(np.ptp(nus)) if len(nus)>1 else 0.0 if len(nus)==1 else float('nan'),
        'pressure_deficit_median':float(np.median(dps)) if len(dps) else float('nan'),
    }
