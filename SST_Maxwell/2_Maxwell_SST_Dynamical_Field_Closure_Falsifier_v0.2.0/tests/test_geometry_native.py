from __future__ import annotations
import numpy as np
from native_ext import polyline_stats,interaction_energy,interaction_force_gradient

def circle(n=80,r=1.0):
 t=np.linspace(0,2*np.pi,n,endpoint=False);return np.c_[r*np.cos(t),r*np.sin(t),np.zeros(n)]

def test_stats_python():
 p=circle();s=polyline_stats(p,force_python=True);assert abs(s['length']-2*np.pi)<0.01

def test_energy_force_finite():
 a=circle(48);b=a+np.array([3.,0,0]);e=interaction_energy(a,b,.05,force_python=True);f=interaction_force_gradient(a,b,.05,force_python=True);assert np.isfinite(e) and np.all(np.isfinite(f))
