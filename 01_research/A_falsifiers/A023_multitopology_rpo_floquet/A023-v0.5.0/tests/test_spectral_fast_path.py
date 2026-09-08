from run_panel import canonical_entries
from sst_blind.multitopology import dataset_analysis


def _cfg(fast):
    return {
      'fseries_raw_samples':256,'panel_n_total':48,'panel_local_span':3,'panel_kelvin_harmonics':[2,3],
      'panel_eps_values':[0.002,0.004],'panel_eps_convergence_values':[0.002,0.004],'panel_eps_robustness_values':[],
      'panel_jacobian_reference_eps':0.004,'panel_enable_dynamics':False,'panel_enable_rpo':False,
      'panel_spectral_extension_fast':fast,'panel_spectral_nyquist_fraction_max':0.75,
      'core_fraction_of_thickness':0.9,'thickness_stride':2,'dcsc_tangent_tol':0.08,'thickness_min_separation_fraction':0.08,'curvature_quantile':0.005,
      'panel_min_core_clearance':1.05,'panel_jacobian_convergence_max':0.3,'panel_normalized_growth_max':0.12,'panel_nearest_rate_min':0.0,'panel_collective_stabilization_min':0.02,
    }


def test_fast_linear_path_preserves_spectral_observables():
    entry=dict(next(e for e in canonical_entries() if e['source']=='knot_0.1'),blind_id='B01')
    full=dataset_analysis(entry,_cfg(False),backend='python',allow_sycl_cpu=False,mod=None)
    fast=dataset_analysis(entry,_cfg(True),backend='python',allow_sycl_cpu=False,mod=None)
    for key in ('normalized_growth','jacobian_convergence','dominant_kmax_boundary_weight'):
        assert abs(float(full['metrics'][key])-float(fast['metrics'][key]))<1e-12
    assert fast['metrics']['spectral_extension_fast_path'] is True
    assert fast['family_ablation']['skipped'] is True
