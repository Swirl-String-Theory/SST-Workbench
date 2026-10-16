"""A061 v0.2 canonical math and experimental negative controls. No SST physical validation."""
from __future__ import annotations
import math
import numpy as np
C_SI=299792458.0
H_SI=6.62607015e-34
V_SWIRL=1.09384563e6

def canon_factor(u, c=C_SI):
    a=np.asarray(u,dtype=float)
    if c<=0 or np.any(~np.isfinite(a)) or np.any(np.abs(a)>=c):
        raise ValueError("clock reduction requires |u|<c with explicit speed meaning")
    return np.sqrt((1.-a/c)*(1.+a/c))

def legacy_factor(v, vscale=V_SWIRL):
    if not(0<=abs(v)<vscale): raise ValueError('invalid historical speed-normalized domain')
    return math.sqrt(1-(v/vscale)**2)

def action_phase(p_over_rest, omega0=1.0):
    q=np.asarray(p_over_rest,dtype=float)
    if np.any(~np.isfinite(q)) or not math.isfinite(omega0): raise ValueError('nonfinite action-phase input')
    H_over_E0=np.hypot(q,1.0)
    return omega0/H_over_E0, 1.0/H_over_E0

def spectro_gap(freq_Hz):
    f=np.asarray(freq_Hz,dtype=float)
    if np.any(~np.isfinite(f)) or np.any(f<0): raise ValueError('invalid frequency')
    return H_SI*f

def lock_window(omega_drive, omega_k, strength):
    if strength<0: raise ValueError('negative locking amplitude')
    return abs(omega_drive-omega_k)<=strength

def pinning_energy(theta,q,K=1.):
    if int(q)!=q or q<0 or not np.isfinite(K): raise ValueError('bad q or K')
    theta=np.asarray(theta,dtype=float)
    return K*(1.-np.cos(q*theta)) if q else np.zeros_like(theta)

def pinning_stationary_minima(q):
    return np.arange(q,dtype=float)*2*np.pi/q if q else np.array([],dtype=float)

def phase_jump_countermodel(time,base_hz=10.,offset_hz=2.,transition_s=1.):
    t=np.asarray(time,dtype=float)
    if t.ndim!=1 or len(t)<4 or np.any(np.diff(t)<=0): raise ValueError('sorted time required')
    # Piecewise continuous phase, constant local time factor (=1) by construction.
    phi=2*np.pi*(base_hz*t+offset_hz*np.maximum(t-transition_s,0))
    return phi,np.diff(phi)/(2*np.pi*np.diff(t))

def common_ratio(base_ratio, common, source1=1., source2=1.):
    if min(common,source1,source2)<=0: raise ValueError('positive response only')
    return base_ratio*(common*source1)/(common*source2)
