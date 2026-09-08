import numpy as np
from sst_eft_falsifier.geometry import resample_arclength,curve_length,observables
from sst_eft_falsifier.bishop import gauge_invariance_residual
from sst_eft_falsifier.operators import redundancy_residuals
def trefoil(n=240):
 t=np.linspace(0,2*np.pi,n,endpoint=False); return np.column_stack([np.sin(t)+2*np.sin(2*t),np.cos(t)-2*np.cos(2*t),-np.sin(3*t)])
def test_geometry():
 x=resample_arclength(trefoil(),128); assert curve_length(x)>0; assert np.isfinite(observables(x)['ropelength'])
def test_gauge():
 x=resample_arclength(trefoil(),128); r,H=gauge_invariance_residual(x); assert r<1e-9
def test_ibp():
 x=resample_arclength(trefoil(),128); r=redundancy_residuals(x); assert r['total_derivative_kappa']<1e-8
