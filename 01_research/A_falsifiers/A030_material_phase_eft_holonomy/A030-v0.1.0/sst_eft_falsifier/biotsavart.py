import numpy as np
from .constants import GAMMA_STAR,CORE_RADIUS_STAR
try:
    from native_ext import HAVE_NATIVE,biot_savart_velocity as _native_bs
except Exception:
    HAVE_NATIVE=False; _native_bs=None
def biot_savart_velocity_python(x,gamma_star=GAMMA_STAR,core_radius_star=CORE_RADIUS_STAR):
    x=np.asarray(x,float); x2=np.roll(x,-1,axis=0); dl=x2-x; mid=.5*(x+x2); out=np.zeros_like(x); a2=core_radius_star**2; coeff=gamma_star/(4*np.pi)
    for i in range(len(x)):
        r=x[i]-mid; d2=np.sum(r*r,axis=1)+a2; out[i]=coeff*np.sum(np.cross(dl,r)/np.power(d2[:,None],1.5),axis=0)
    return out
def velocity(x,gamma_star=GAMMA_STAR,core_radius_star=CORE_RADIUS_STAR,require_native=False):
    if HAVE_NATIVE: return np.asarray(_native_bs(np.asarray(x,float),float(gamma_star),float(core_radius_star)))
    if require_native: raise RuntimeError("native extension required but unavailable")
    return biot_savart_velocity_python(x,gamma_star,core_radius_star)
