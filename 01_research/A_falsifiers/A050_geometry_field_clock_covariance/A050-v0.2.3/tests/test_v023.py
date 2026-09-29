import hashlib, json
from pathlib import Path
import numpy as np
from sst_gfcc_blind.basin import wilson_interval, perturb_base, measured_perturbation_rms
from sst_gfcc_blind.geometry import make_curve
ROOT=Path(__file__).resolve().parents[1]

def test_parent_verdict_and_hash_are_locked():
    p=json.loads((ROOT/'provenance/PARENT_v0.2.2_EVIDENCE.json').read_text())
    assert p['parent_primary_verdict']=='MODAL_PERSISTENCE_NOT_REPRODUCED'
    assert p['parent_blind_results_sha256']=='73978a661d25067feb9f4aee88f175e7cd70d7f216f09c6bea258e1baf9f83b1'
    assert p['selection_basis']['base_family']=='G0002' and p['selection_basis']['target_branch_mode']==3

def test_preregistered_basin_map_is_frozen_and_paired():
    c=json.loads((ROOT/'config/default.json').read_text())
    assert c['analysis_stage']=='post_confirmatory_reveal_diagnostic'
    assert c['basin_map']['amplitude_ladder']==[0.0,0.00125,0.0025,0.00375,0.005,0.0075,0.01]
    assert c['basin_map']['core_amplitudes']==[0.00125,0.0025]
    assert c['basin_map']['minimum_core_support']==9
    assert c['basin_map']['paired_directions_across_amplitudes'] is True
    assert c['target_branch_mode']==3 and c['modal_persistence_steps']==2048

def test_legacy_kelvin_thresholds_are_unchanged():
    c=json.loads((ROOT/'config/default.json').read_text()); f=json.loads((ROOT/'config/frozen_gate_thresholds_v0.2.0.json').read_text())
    assert c['kelvin_gate']==f['kelvin_gate']
    assert c['modal_persistence_gate']['frequency_cv_max']==0.15

def test_direction_manifest_has_12_hash_locked_unit_rms_directions():
    m=json.loads((ROOT/'data/DIRECTION_MANIFEST.json').read_text())
    assert m['direction_count']==12 and len(m['entries'])==12
    for e in m['entries']:
        p=ROOT/e['file']; assert hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256']
        d=np.load(p)['direction']; assert d.shape==(56,3) and np.isfinite(d).all()
        rms=np.sqrt(np.mean(np.sum(d*d,axis=1))); assert abs(rms-1.0)<1e-12

def test_nominal_perturbation_scale_is_recovered_locally():
    m=json.loads((ROOT/'data/DIRECTION_MANIFEST.json').read_text()); d=np.load(ROOT/m['entries'][0]['file'])['direction']; base=make_curve('G0002',56)
    eps=0.0025; p=perturb_base(base,d,eps); got=measured_perturbation_rms(p,base)
    assert abs(got-eps)/eps < 0.08

def test_wilson_interval_sane():
    lo,hi=wilson_interval(9,12); assert 0<lo<0.75<hi<1
