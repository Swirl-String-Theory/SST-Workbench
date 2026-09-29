from pathlib import Path
import json
from sst_vortex_shear.campaign import run_blind_campaign


def test_campaign_smoke(tmp_path):
    root=Path(__file__).resolve().parents[1]
    cfg=json.loads((root/'configs'/'default.json').read_text(encoding='utf-8'))
    cfg['n_directions']=1000
    dc=cfg['structured_dynamic']
    dc['grid_n']=9
    dc['coarse_grid_n']=9
    dc['microcell_grid']=[2,2,1]
    dc['loop_points']=16
    dc['tube_sigma']=0.55
    dc['dt']=0.02
    dc['t_final']=0.08
    dc['coarse_t_final']=0.06
    dc['control_t_final']=0.06
    dc['sample_stride']=1
    cfg['tolerances']['structured_initial_isotropy_fro_max']=0.6
    cfg['tolerances']['dynamic_energy_drift_rel_max']=0.02
    cfg['tolerances']['rk4_local_convergence_rel_max']=0.01
    cfg['tolerances']['spectral_edge_energy_fraction_initial_max']=0.9
    cfg['tolerances']['static_A2_relative_error_max']=5e-4
    cfg['relative_equilibrium']['resolution_check_grid_n']=9
    cfg['relative_equilibrium']['diagnostic_time']=0.04
    cfg['relative_equilibrium']['translation_residual_max']=2.0
    cfg['relative_equilibrium']['comoving_change_rel_max']=2.0
    cfg['relative_equilibrium']['resolution_residual_delta_max']=2.0
    cfg['frozen_background']['t_final']=0.08
    cfg['frozen_background']['sample_stride']=1
    p=tmp_path/'cfg.json'; p.write_text(json.dumps(cfg),encoding='utf-8')
    s=run_blind_campaign(p,tmp_path/'out')
    assert s['pipeline_status']=='PIPELINE_QUALIFIED'
    assert s['structured_dynamic']['background_meta']['reference_speed'] > 0.0
    assert 'chi_wave_if_qualified' in s['target_free_wave_hierarchy_gate']
