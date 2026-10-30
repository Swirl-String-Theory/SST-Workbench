from pathlib import Path
import json,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from experiment.ruban_filament import velocity,hamiltonian,evolve,run_filament_study,C_LOCAL
from experiment.ruban import DELTA,PRIMARY,load_primary_seed
from experiment.euler3d import resample_closed

def test_exact_finite_difference_ruban_coefficient():
    import math
    assert abs(C_LOCAL-(7/10-math.log(2)/4))<1e-15
    assert DELTA==.05

def test_velocity_finite_and_regularization_has_effect():
    a,_=load_primary_seed(ROOT/'inputs/ruban_t23'/PRIMARY)
    p=resample_closed(a,64)
    u=velocity(p)
    assert u.shape==p.shape and np.isfinite(u).all()
    assert not np.allclose(u,velocity(p,delta=.1))

def test_short_rk4_filament_is_diagnostic_only():
    a,_=load_primary_seed(ROOT/'inputs/ruban_t23'/PRIMARY)
    p=resample_closed(a,64)
    out=evolve(p,.01,.005)
    assert out['time_final']==.01 and out['steps']==2
    assert np.isfinite(out['final_hamiltonian'])
    assert out['physical_stability']=='UNRESOLVED'
    assert not out['paper_trajectory_reproduced'] and not out['full_pseudospectral_method_used']

def test_small_filament_study_outputs_do_not_claim_paper_lifetime(tmp_path):
    out=run_filament_study(ROOT,tmp_path,n=32,T=.01,dt=.005)
    assert out['status']=='DIAGNOSTIC_ONLY'
    assert set(out['cases'])=={'ruban','analytic_032'}
    assert not out['paper_t_320_reproduced']
    assert (tmp_path/'ruban_series.csv').exists()

def test_gate_g13_is_activated_but_not_auto_claimed():
    g={r['gate_id']:r for r in json.loads((ROOT/'gate_plan.json').read_text())['gates']}
    assert g['G13']['enabled'] and g['G13']['requires']==['G11']
