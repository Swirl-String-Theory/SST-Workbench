import hashlib, json
from pathlib import Path
import numpy as np
from sst_gfcc_blind.temporal import phase_randomized_surrogate, mean_autocorrelation
from sst_gfcc_blind.persistence import aggregate_groups
ROOT=Path(__file__).resolve().parents[1]

def test_v022_preregistration_is_confirmatory_and_frozen():
    cfg=json.loads((ROOT/'config/default.json').read_text())
    frozen=json.loads((ROOT/'config/frozen_gate_thresholds_v0.2.0.json').read_text())
    assert cfg['observation_protocol']['policy']=='confirmatory_holdout_persistence_and_memory_convergence'
    assert cfg['observation_protocol']['legacy_gate_thresholds_retuned'] is False
    assert cfg['spatial_gate_steps']==80
    assert cfg['temporal_memory_steps']==1024
    assert cfg['modal_persistence_steps']==2048
    assert cfg['sample_every']==4 and cfg['time_step']==0.02
    assert cfg['temporal_memory_gate']==frozen['temporal_memory_gate']
    assert cfg['kelvin_gate']==frozen['kelvin_gate']
    for k,v in frozen['spatial_thresholds'].items(): assert cfg[k]==v
    assert cfg['floquet_policy']['active'] is False

def test_holdout_manifest_is_20_hash_locked_carriers():
    m=json.loads((ROOT/'data/HOLDOUT_MANIFEST.json').read_text())
    assert m['carrier_total']==20 and m['group_count']==4 and m['replicates_per_group']==5
    groups={}
    for e in m['entries']:
        groups[e['group_id']]=groups.get(e['group_id'],0)+1
        p=ROOT/'data'/e['file']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256']
        z=np.load(p)['points']; assert z.shape==(56,3); assert np.isfinite(z).all()
    assert sorted(groups.values())==[5,5,5,5]

def test_phase_randomization_preserves_individual_power_spectrum():
    rng=np.random.default_rng(7)
    x=rng.normal(size=(64,3))
    y=phase_randomized_surrogate(x,np.random.default_rng(8))
    for j in range(3):
        a=np.abs(np.fft.rfft(x[:,j]-x[:,j].mean()))
        b=np.abs(np.fft.rfft(y[:,j]-y[:,j].mean()))
        assert np.allclose(a,b,rtol=1e-10,atol=1e-10)

def test_group_confirmation_requires_four_same_branch():
    rows=[]
    for i in range(5):
        rows.append({'carrier_id':f'C{i:05d}','group_id':'H01','persistence':{'pass':i<4,'persistent_mode':3 if i<4 else 2}})
    g=aggregate_groups(rows,{'minimum_replicates_per_group':4})[0]
    assert g['pass'] is True and g['branch_mode']==3 and g['supporting_replicates']==4

def test_preregistration_checkpoints_are_nested_and_final_required():
    cfg=json.loads((ROOT/'config/default.json').read_text())
    p=cfg['modal_persistence_gate']
    assert p['checkpoints']==[320,640,1024,1536,2048]
    assert p['late_checkpoints']==[640,1024,1536,2048]
    assert p['require_final_checkpoint_qualified'] is True
    assert cfg['temporal_memory_convergence_gate']['window_steps']==[80,160,320,640,1024]
