import importlib.util
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiment.pipeline import check_sources,check_method,analyze_optional_field,run_scientific_pipeline
from experiment.phaseclock import demo,compare_two,run_npz
import numpy as np

def test_input_hashes():
    assert check_sources(ROOT)['all_valid']

def test_synthetic_controls():
    assert check_method(ROOT)['pass_method_control']

def test_rigid_rotation_null():
    d=demo()['negative_rigid_rotation_shape_invariants']
    assert d['q1']['status']==d['q2']['status']=='NO_CLOCK'

def test_beating_null():
    assert demo()['negative_beating']['G3_phase_reproducibility']=='SCREEN_FAIL'

def test_exact_numerical_frequency_only():
    p=demo()['positive_two_shape_signals']
    assert abs(p['q1']['frequency']-0.25)<1e-5
    assert p['G3_phase_reproducibility']=='PASS_NUMERICAL_ONLY'

def test_operator_not_independently_validated():
    r=check_method(ROOT)['a064_audit']
    assert r['G4_operator_prediction_holdout']=='NOT_TESTABLE'
    assert r['overall']=='NO_PHYSICAL_CLOCK_INFERENCE_POSSIBLE'

def test_no_real_field_present():
    assert analyze_optional_field(ROOT)['status']=='NOT_PROVIDED'

def test_nonuniform_time_rejected():
    t=np.arange(200.,dtype=float);t[100:]+=0.1
    out=compare_two(t,np.sin(t),np.cos(t))
    assert out['q1']['status']=='INDETERMINATE'

def test_real_field_only_screen_and_shape_contract(tmp_path):
    # Intentionally malformed input must not establish clock.
    d=tmp_path/'data';d.mkdir()
    np.savez(d/'PKLSA_DYNAMICS.npz',t=np.array([0.,1.]),u=np.zeros((2,2,2,2)),domain_length=1.)
    assert analyze_optional_field(tmp_path)['status']=='INVALID_INPUT'

def test_source_tampering_fails_closed(tmp_path):
    (tmp_path/'data').mkdir()
    for name in ('PREFLIGHT_RESULTS.json','PREFLIGHT_WITH_A064.json','A064-v0.3.0_results.json'):
        (tmp_path/'data'/name).write_bytes((ROOT/'data'/name).read_bytes())
    (tmp_path/'data/PREFLIGHT_RESULTS.json').write_text('{}')
    assert not check_sources(tmp_path)['all_valid']

class FakeDef:
    def __init__(self):self.enabled=True
class FakeLedger:
    def __init__(self):
        self.defs={f'G{k}':FakeDef() for k in range(10)}
        self.records={}
    def record(self,gid,status,**kwargs):
        assert gid not in self.records
        self.records[gid]=status
    def skip_due_prerequisite(self,gid,**kwargs):
        self.record(gid,'NOT_RUN_PREREQUISITE')
    def status(self,gid):return self.records.get(gid)

def test_framework_gate_semantics():
    led=FakeLedger()
    result=run_scientific_pipeline(ROOT,{},led,'BASIC')
    assert [led.status(f'G{i}') for i in range(9)]==[
        'PASS','PASS','PASS','UNRESOLVED',
        'NOT_RUN_PREREQUISITE','NOT_RUN_PREREQUISITE',
        'NOT_RUN_PREREQUISITE','NOT_RUN_PREREQUISITE','NOT_RUN_PREREQUISITE']
    assert result['physical_clock_status']=='UNRESOLVED'
