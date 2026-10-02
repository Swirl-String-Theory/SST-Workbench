from __future__ import annotations
import numpy as np
from .geometry import segments, close_curve
from native_ext import backend as _get_native

def native_backend(): return _get_native()

def biot_savart_points(points, centerline, gamma=1.0, core_a=0.0, chunk=1024):
    x=np.atleast_2d(np.asarray(points,float)); c=np.ascontiguousarray(close_curve(centerline),dtype=float)
    b=_get_native()
    if b is not None:
        try: return np.asarray(b.biot_savart_points(np.ascontiguousarray(x),c,float(gamma),float(core_a)))
        except Exception: pass
    _,_,dl,mid=segments(c); out=np.zeros_like(x); a2=float(core_a)**2; fac=float(gamma)/(4*np.pi)
    for i in range(0,len(x),chunk):
        xx=x[i:i+chunk]; r=xx[:,None,:]-mid[None,:,:]; den=(np.einsum('...i,...i->...',r,r)+a2)**1.5
        cr=np.cross(dl[None,:,:],r); out[i:i+chunk]=fac*np.sum(cr/den[:,:,None],axis=1)
    return out

def biot_savart_set(points, components, gammas=None, core_a=0.0):
    comps=list(components); gammas=[1.0]*len(comps) if gammas is None else list(gammas)
    out=np.zeros((len(np.atleast_2d(points)),3),float)
    for c,g in zip(comps,gammas): out += biot_savart_points(points,c,g,core_a)
    return out

def line_integral_velocity(loop, field_fn):
    p=close_curve(loop); q=np.roll(p,-1,axis=0); mid=0.5*(p+q); dl=q-p
    return float(np.einsum('ij,ij->i',field_fn(mid),dl).sum())

def gauss_linking(curve1, curve2):
    c1=np.ascontiguousarray(close_curve(curve1)); c2=np.ascontiguousarray(close_curve(curve2)); b=_get_native()
    if b is not None:
        try: return float(b.gauss_linking(c1,c2))
        except Exception: pass
    _,_,dl1,m1=segments(c1); _,_,dl2,m2=segments(c2); r=m1[:,None,:]-m2[None,:,:]; den=np.linalg.norm(r,axis=2)**3
    den=np.where(den<1e-30,np.inf,den); cr=np.cross(dl1[:,None,:],dl2[None,:,:])
    return float(np.sum(np.einsum('ijk,ijk->ij',cr,r)/den)/(4*np.pi))

def pairwise_linking_matrix(components):
    n=len(components); M=np.zeros((n,n),float)
    for i in range(n):
        for j in range(i+1,n): M[i,j]=M[j,i]=gauss_linking(components[i],components[j])
    return M

def regularized_filament_energy(curve, gamma=1.0, rho=1.0, core_a=0.05):
    c=np.ascontiguousarray(close_curve(curve)); b=_get_native()
    if b is not None:
        try: return float(b.regularized_energy(c,float(gamma),float(rho),float(core_a)))
        except Exception: pass
    _,_,dl,mid=segments(c); r=mid[:,None,:]-mid[None,:,:]; den=np.sqrt(np.einsum('...i,...i->...',r,r)+core_a**2)
    dots=np.einsum('ik,jk->ij',dl,dl); return float(rho*gamma**2/(8*np.pi)*np.sum(dots/den))

def writhe_midpoint(curve, exclude_near=2):
    c=np.ascontiguousarray(close_curve(curve)); b=_get_native()
    if b is not None and hasattr(b,'writhe_midpoint'):
        try: return float(b.writhe_midpoint(c,int(exclude_near)))
        except Exception: pass
    n=len(c); _,_,dl,mid=segments(c); r=mid[:,None,:]-mid[None,:,:]; den=np.linalg.norm(r,axis=2)**3
    cr=np.cross(dl[:,None,:],dl[None,:,:]); val=np.einsum('ijk,ijk->ij',cr,r); mask=np.ones((n,n),bool)
    for k in range(-exclude_near,exclude_near+1): mask[np.arange(n),(np.arange(n)+k)%n]=False
    den=np.where(mask & (den>1e-30),den,np.inf); return float(np.sum(val/den)/(4*np.pi))
