import numpy as np
from a054_state.selector import relax_variational

def circle(n=96):
 t=np.linspace(0,2*np.pi,n,endpoint=False);return np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]
def trefoil(n=120):
 t=np.linspace(0,2*np.pi,n,endpoint=False);return np.c_[np.sin(t)+2*np.sin(2*t),np.cos(t)-2*np.cos(2*t),-np.sin(3*t)]
def cfg():return {'selector_resolution':72,'selector_modes':1,'max_iterations':2,'fd_eps':0.02,'stationarity_max':0.2,'step0':0.02,'max_backtracks':5,'core_scale':1.0,'clearance_retention':0.5,'link_drift_max':0.1,'hessian_negative_relative_tolerance':1e-3,'ringdown_perturb_eps':0.01,'ringdown_dt':0.02,'ringdown_steps':32,'ringdown_amplitude_ratio_max':2.0,'ringdown_energy_drift_max':0.1}
def test_relaxation_does_not_increase_energy():
 r=relax_variational([trefoil()],cfg());assert np.isfinite(r['final_energy']);assert r['final_energy']<=r['initial_energy']+1e-8*max(1,abs(r['initial_energy']));assert r['topology_proxy']['ok']
def test_circle_finite():
 r=relax_variational([circle()],cfg());assert np.isfinite(r['final_stationarity']);assert r['hessian_symmetry_rel']<1e-12
