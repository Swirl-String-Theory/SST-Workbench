from pathlib import Path
import json
from sst_vortex_shear.campaign import run_blind_campaign


def test_campaign_smoke(tmp_path):
    root=Path(__file__).resolve().parents[1]
    cfg=json.loads((root/'configs'/'default.json').read_text(encoding='utf-8'))
    cfg['n_directions']=1000
    f=cfg['filament']
    f['orientation_count']=12
    f['points_per_loop']=16
    f['dt']=0.02
    f['t_final']=0.04
    f['sample_times']=[0.0,0.04]
    f['reversibility_t_final']=0.04
    cfg['tolerances']['orientation_isotropy_fro_max']=0.20
    cfg['tolerances']['modulus_plane_spread_rel_max']=0.6
    cfg['tolerances']['static_A2_relative_error_max']=5e-4
    p=tmp_path/'cfg.json'; p.write_text(json.dumps(cfg),encoding='utf-8')
    s=run_blind_campaign(p,tmp_path/'out')
    assert s['pipeline_status']=='PIPELINE_QUALIFIED'
    assert s['static_born_carry_forward']['A2_mean'] > 0.0
    assert s['topological_filament_campaign']['static_linked']['mu_over_rho_mean'] > 0.0
