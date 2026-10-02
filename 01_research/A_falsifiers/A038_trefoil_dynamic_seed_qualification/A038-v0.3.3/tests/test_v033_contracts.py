import inspect, json
from pathlib import Path
from sst_seed_falsifier.evidence import dynamics_contract
from sst_seed_falsifier.release import release_identity
from sst_seed_falsifier import operator_split


def cfg():
    return {'core_fraction':.08,'operator_split_remap_interval':.25,'operator_split_remap_kernel':'periodic_cubic','operator_split_remap_oversample_factor':16,'operator_split_remap_min_oversample':1024,'long_hard_ds_cv':.45}

def test_contract_is_operator_split():
    c,h=dynamics_contract(cfg(),96)
    assert c['format']=='SST-TREFOIL-DYNAMICS-CONTRACT-2'
    assert c['continuous_mesh_velocity_enabled'] is False
    assert c['reparameterization_scheme']=='operator_split_periodic_cubic_arclength_v2'

def test_operator_split_module_has_no_tangential_controller_dependency():
    src=inspect.getsource(operator_split)
    assert 'tangential_redistribution' not in src

def test_release_identity_matches():
    r=release_identity(); assert r['match']; assert r['runtime_version']=='0.3.3'

def test_configs_do_not_contain_target_ratio():
    root=Path(__file__).resolve().parents[1]
    text='\n'.join(p.read_text().lower() for p in (root/'config').glob('*.json'))
    for token in ('golden','varphi','1.618','target_ratio'):
        assert token not in text
