"""Targeted Framework v1.1.0 migration and honest scientific backend-evidence tests."""
import json,os,sys,hashlib
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from framework_bootstrap import resolve_framework_root,load_framework


def test_self_contained_version_and_byte_hash_pin():
    r=resolve_framework_root()
    assert r==ROOT/'_sst_runtime'
    info=json.loads((r/'RUNTIME_SNAPSHOT_MANIFEST.json').read_text())
    assert info['version']=='1.1.0' and len(info['files'])>=25
    assert all(hashlib.sha256((r/v['path']).read_bytes()).hexdigest()==v['sha256'] for v in info['files'])
    load_framework()
    import sst_falsifier
    assert sst_falsifier.__version__=='1.1.0'


def test_framework_v110_science_contract_and_report():
    load_framework()
    from sst_falsifier.science_contract import validate_science_contract
    from sst_falsifier.source_registry import validate_source_contract
    from sst_falsifier.report import validate_report
    from sst_falsifier.gates import validate_gate_plan
    assert not validate_science_contract(json.loads((ROOT/'science_contract.json').read_text()))
    assert not validate_source_contract(json.loads((ROOT/'source_contract.json').read_text()))
    assert not validate_report(ROOT/'report/FALSIFIER_REPORT.tex',require_complete=True)
    assert not validate_gate_plan(ROOT/'gate_plan.json')


def test_native_gpu_probes_do_not_count_as_scientific_execution(tmp_path):
    load_framework()
    from sst_falsifier.auto_backend_matrix import run_auto_matrix
    probes={k:{'available':True,'status':'DEVICE_READY'} for k in ('py','cpp','gpu')}
    z=run_auto_matrix(ROOT,{'auto_backends':{'enabled':True,'minimum_science_backends':2},'gpu':{'provider':'intel'}},'BASIC',tmp_path,
        probes=probes,science_override={})
    assert z['counted_backend_categories']==0
    assert z['status']=='EXECUTION_CONTRACT_BLOCKED'


def test_python_science_execution_record_is_verifiable(tmp_path,monkeypatch):
    load_framework()
    from sst_falsifier.auto_backend_matrix import run_auto_matrix
    monkeypatch.setenv('A075_RUNTIME_OPTIONS_JSON',json.dumps({'grid':16,'grid_up':24,'dt':0.01,'t_end':0.03,
                 'knots':['0_1'],'threads':2,'diagnostic_stride':1,'allow_expensive':True}))
    probes={'py':{'available':True,'actual':'numpy.cpu'},'cpp':{'available':False,'reason':'No C++ device'},
            'gpu':{'available':False,'reason':'No XPU on test environment'}}
    z=run_auto_matrix(ROOT,{'auto_backends':{'enabled':True,'minimum_science_backends':2},'gpu':{'provider':'intel'}},'BASIC',tmp_path,probes=probes)
    assert z['scientific']['py']['status']=='EXECUTED'
    assert (tmp_path/'backend_science/py.json').is_file()
    assert z['scientific']['gpu']['status']!='EXECUTED'
    assert z['counted_backend_categories']==1 and z['status']=='EXECUTION_CONTRACT_BLOCKED'


def test_falsified_evidence_hash_is_rejected(tmp_path):
    load_framework()
    from sst_falsifier.auto_backend_matrix import _record
    evidence=tmp_path/'backend_science';evidence.mkdir()
    source=ROOT/'experiment/euler3d.py'
    f=evidence/'py.json';f.write_text(json.dumps({'executed':True,'actual_backend':'python',
      'input_sha256':'a'*64,'observable':[1.0],'precision':'float64','physical_final_time':.03}))
    claim={'executed':True,'actual_backend':'python','source_path':'experiment/euler3d.py',
      'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'evidence_path':'backend_science/py.json',
      'evidence_sha256':'0'*64,'input_sha256':'a'*64,'observable':[1.0]}
    z=_record('py',claim,{'available':True},ROOT,tmp_path,'intel')
    assert z['status']=='REJECTED' and z['scientific_execution'] is False
