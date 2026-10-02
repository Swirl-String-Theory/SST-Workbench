from __future__ import annotations
import numpy as np

def _norm_edge(V,r):
    ve=float(np.interp(1.0,r,V)); return V/max(abs(ve),1e-14),max(abs(ve),1e-14)

def profile(name,r,axial_ratio):
    """Dimensionless finite-core base profiles. r is in core-radius units."""
    r=np.asarray(r,float); rr=np.maximum(r,1e-10); x=r
    name=str(name).lower()
    if name=='gaussian':
        V=(1-np.exp(-x*x))/rr; V,_=_norm_edge(V,r); U=float(axial_ratio)*np.exp(-x*x)
    elif name=='smooth_rankine':
        V=x/np.sqrt(1+x**4); V,_=_norm_edge(V,r); U=float(axial_ratio)/(1+x**4)
    elif name=='compact_poly':
        F=np.where(x<1,0.5*x*x-0.5*x**4+x**6/6,1/6); V=6*F/rr; V[r<1e-9]=0.0; V,_=_norm_edge(V,r); U=float(axial_ratio)*np.where(x<1,(1-x*x)**2,0.0)
    else: raise ValueError(f'unknown profile {name}')
    # exact axis limits for numerical stability
    if len(r) and r[0]==0:
        if name=='gaussian': V[0]=0.0
        elif name=='smooth_rankine': V[0]=0.0
        elif name=='compact_poly': V[0]=0.0
    return U,V

def vorticity_components(r,U,V):
    r=np.asarray(r,float); dU=np.gradient(U,r,edge_order=2); dRV=np.gradient(r*V,r,edge_order=2); omega_ax=dRV/np.maximum(r,0.5*max(float(r[1]-r[0]),1e-12)); omega_theta=-dU
    return omega_ax,omega_theta

def profile_metrics(r,U,V):
    oa,ot=vorticity_components(r,U,V); w=np.maximum(r,1e-12)
    Ea=float(np.trapezoid(U*U*w,r)); Et=float(np.trapezoid(V*V*w,r)); Wa=float(np.trapezoid(oa*oa*w,r)); Wt=float(np.trapezoid(ot*ot*w,r));
    return {'base_axial_energy_fraction':Ea/max(Ea+Et,1e-30),'base_axial_vorticity_fraction':Wt/max(Wa+Wt,1e-30),'omega_axial_rms':float(np.sqrt(Wa/max(np.trapezoid(w,r),1e-30))),'omega_toroidal_rms':float(np.sqrt(Wt/max(np.trapezoid(w,r),1e-30)))}
