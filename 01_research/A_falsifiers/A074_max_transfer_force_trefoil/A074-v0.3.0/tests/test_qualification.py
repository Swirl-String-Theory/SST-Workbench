import json,hashlib,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from experiment.qualification import prepared_state,one_level,_orthogonal_fit
from experiment.euler3d import Euler3D

def test_provenance_identity():
 cfg,curve,ident=prepared_state()
 assert tuple(ident['pinned_selection'])==tuple(cfg['pinned_candidate']['parameter_vector'])
 assert ident['gap_over_2core']>1
 assert ident['candidate_curve_sha256']==hashlib.sha256(np.asarray(curve,dtype='<f8').tobytes()).hexdigest()

def test_p2_no_fake_stationary_field():
 _,curve,ident=prepared_state()
 cfg=json.loads((ROOT/'configs/qualification.json').read_text())
 g=one_level(32,cfg,curve,ident,steps=False)
 assert 0<=g['full_field_fit']['relative_euler_field_residual']<=1+1e-10
 assert g['full_field_fit']['gram_rank']==6
 assert g['poisson']['poisson_relative_residual']<1e-8

def test_true_stationary_constructed_field_fit():
 # omega_t = -(U.grad omega), a mathematically exact translating equilibrium.
 n=4;xyz=np.zeros((3,n,n,n));omega=np.ones((3,n,n,n));grads=np.zeros((3,3,n,n,n))
 for j in range(3):grads[j,j]=2+j
 u=np.array([.23,-.17,.4]);wt=-np.einsum('j,jiklm->iklm',u,grads)
 fit=_orthogonal_fit(wt,omega,grads,xyz,1.)
 assert fit['relative_euler_field_residual']<1e-5 # Rank deficiency possible, translation only tested.

def test_grid_identity():
 cfg,curve,ident=prepared_state()
 r=one_level(32,cfg,curve,ident,steps=False)
 assert r['candidate_full_input_sha256']==ident['candidate_full_input_sha256']
 assert abs(r['core_radius_cells']-0.28/(6/32))<1e-10

def test_science_report_no_gravity_target():
 txt=(ROOT/'science_contract.json').read_text().lower()
 assert 'c^4' not in txt and 'schwarzschild' not in txt
 assert '1.1.0' in (ROOT/'falsifier.toml').read_text()

def test_actual_backend_matrix_has_only_python(tmp_path):
    # External adapter is loaded via spec_from_file_location; validate actual shape.
    from experiment.backend_matrix import run_backend_matrix
    rec=run_backend_matrix(root=ROOT,cfg={},mode='BASIC',output_dir=tmp_path/'backend_science',devices={})
    assert rec['py']['executed'] is True
    assert rec['cpp']['executed'] is False and rec['gpu']['executed'] is False
    assert (tmp_path/'backend_science/py.json').is_file()
    assert rec['py']['input_sha256']==prepared_state()[2]['candidate_full_input_sha256']

def test_refinement_settings_preclude_coarse_positive_claim():
    cfg,curve,ident=prepared_state()
    assert all(ident['core_m']*n/cfg['box_m']<cfg['min_core_cells'] for n in [32,48,64])
    assert all((ident['nonlocal_gap_m']-2*ident['core_m'])*n/cfg['box_m']<cfg['min_gap_cells'] for n in [32,48,64])
    assert cfg['final_time_s']>0 and cfg['max_dt_s']>0

def test_runtime_snapshot_integrity():
    from framework_bootstrap import resolve_framework_root
    assert resolve_framework_root().name=='_sst_runtime'
