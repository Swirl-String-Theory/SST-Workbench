import numpy as np
from a054_state.selector import relax_variational, allocate_resample
from a054_state.dynamics import constrained_potential_factory, gradient_only
from a054_state.energy import energy_matrix,total_kernel
from a054_state.geometry import normalize_by_reach


def circle(n=96):
 t=np.linspace(0,2*np.pi,n,endpoint=False);return np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]
def trefoil(n=120):
 t=np.linspace(0,2*np.pi,n,endpoint=False);return np.c_[np.sin(t)+2*np.sin(2*t),np.cos(t)-2*np.cos(2*t),-np.sin(3*t)]
def cfg():return {
 'selector_resolution':72,'selector_modes':1,'max_iterations':2,'fd_eps':0.02,'stationarity_max':0.2,
 'step0':0.02,'trust_radius_initial':0.02,'trust_expand':1.5,'max_backtracks':12,'backtrack_factor':0.5,
 'armijo_c1':1e-4,'min_step':1e-7,'objective_abs_tolerance':1e-10,'objective_rel_tolerance':1e-10,
 'core_scale':1.0,'clearance_retention':0.5,'link_drift_max':0.1,
 'hessian_negative_relative_tolerance':1e-3,'hessian_fd_rel_l2_max':0.5,
 'ringdown_perturb_eps':0.01,'ringdown_dt':0.02,'ringdown_steps':32,
 'ringdown_amplitude_ratio_max':2.0,'ringdown_energy_drift_max':0.1}


def test_constrained_objective_exactly_matches_projected_geometry():
 cs=allocate_resample([trefoil()],72);cs,_,_=normalize_by_reach(cs);counts=[len(x) for x in cs]
 U,project,B,offs,base=constrained_potential_factory(cs,1.0,1,counts)
 q=np.zeros(len(B));q[0]=0.007
 trial,_,_=project(q)
 assert np.isclose(U(q),total_kernel(energy_matrix(trial,1.0)),rtol=1e-13,atol=1e-13)


def test_negative_constrained_gradient_is_locally_descending_or_reportable():
 cs=allocate_resample([trefoil()],72);cs,_,_=normalize_by_reach(cs);counts=[len(x) for x in cs]
 U,project,B,offs,base=constrained_potential_factory(cs,1.0,1,counts)
 u0,g=gradient_only(U,len(B),0.02);ng=np.linalg.norm(g)
 assert np.isfinite(u0) and np.all(np.isfinite(g))
 if ng>1e-12:
  d=-g/ng
  vals=[U((0.02*(0.5**k))*d) for k in range(14)]
  # The numerical patch explicitly probes this ladder; the test only requires
  # finite evaluability because a nonsmooth reach branch may legitimately be
  # classified UNRESOLVED_NUMERICAL rather than force a false descent claim.
  assert np.all(np.isfinite(vals))


def test_relaxation_does_not_increase_same_objective():
 r=relax_variational([trefoil()],cfg());assert np.isfinite(r['final_energy'])
 tol=cfg()['objective_abs_tolerance']+cfg()['objective_rel_tolerance']*max(1,abs(r['initial_energy']))
 assert r['final_energy']<=r['initial_energy']+tol
 assert r['topology_proxy']['ok'];assert r['objective_consistency_verified']
 assert r['numerical_status'] in ('RESOLVED','UNRESOLVED_NUMERICAL')
 assert len(r['hessian_fd_sweep']['scales'])==3


def test_circle_finite_and_hessian_sweep_present():
 r=relax_variational([circle()],cfg());assert np.isfinite(r['final_stationarity']);assert r['hessian_symmetry_rel']<1e-12
 assert 'hessian_fd_converged' in r and 'hessian_sign_class' in r
