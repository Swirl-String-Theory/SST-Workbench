from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from sst_falsifier_framework import __version__
from sst_falsifier_framework.gates import GateLedger,GateRecord
from sst_falsifier_framework.outputs import default_output_dir
from sst_falsifier_framework.sources import validate_dynamic_metadata
from sst_falsifier_framework.replication import assess_replication,replication_group
from sst_falsifier_framework.locator import find_framework_root
from sst_falsifier_framework.provenance import build_fingerprint
from a056_falsifier.pipeline import output_dir_for


def test_gate_dependency_fail_closed():
    g=GateLedger(); g.add(GateRecord('G0_PROVENANCE','FAIL','x',{}))
    try: g.add(GateRecord('G1_ADMISSIBILITY','PASS','x',{},depends_on=('G0_PROVENANCE',)))
    except ValueError: return
    assert False


def test_output_dir_is_local():
    p=default_output_dir(ROOT); assert p.parent==ROOT and p.name==ROOT.name+'-outputs'


def test_provider_contract_missing():
    r=validate_dynamic_metadata({'opaque_id':'x'},False); assert not r['pass'] and 'solver_id' in r['missing'] and 'evidence_class' in r['missing']


def test_pipeline_output_dir_tracks_package_folder(tmp_path):
    package_root=tmp_path/'A056-v0.2.1'
    assert output_dir_for(package_root)==package_root/'A056-v0.2.1-outputs'


def test_exact_framework_root_marker():
    assert __version__=='1.0.2.dev0'
    assert find_framework_root(ROOT/'a056_falsifier',__version__)==ROOT


def test_build_fingerprint_is_deterministic(tmp_path):
    s=tmp_path/'x.cpp'; s.write_text('int x=1;\n')
    c={'kind':'host','available':True,'executable':'C:/fake/cl.exe','fingerprint':'abc'}
    a=build_fingerprint(compiler=c,source_files=[s],flags=['/O2'],python_abi={'v':'3.14'},compile_time_identity={'family':'msvc'})
    b=build_fingerprint(compiler=c,source_files=[s],flags=['/O2'],python_abi={'v':'3.14'},compile_time_identity={'family':'msvc'})
    assert a['fingerprint']==b['fingerprint']
    s.write_text('int x=2;\n')
    d=build_fingerprint(compiler=c,source_files=[s],flags=['/O2'],python_abi={'v':'3.14'},compile_time_identity={'family':'msvc'})
    assert a['fingerprint']!=d['fingerprint']


def test_gate5_synthetic_groups_do_not_become_cross_source():
    rows=[
      {'evidence_class':'synthetic_control','source_group':'SYNTH_A','solver_id':'gen-v1','generator_id':'gen-v1'},
      {'evidence_class':'synthetic_control','source_group':'SYNTH_B','solver_id':'gen-v1','generator_id':'gen-v1'},
    ]
    a=assess_replication(rows,2)
    assert a['control_recovered']
    assert a['control_groups']==['gen-v1']
    assert not a['physical_evidence_present']
    assert not a['cross_source_pass']


def test_gate5_physical_independence_requires_two_groups():
    rows=[
      {'evidence_class':'independent_source','source_group':'LAB_A'},
      {'evidence_class':'experimental','source_group':'LAB_B'},
    ]
    a=assess_replication(rows,2)
    assert a['cross_source_pass']
    assert a['physical_groups']==['LAB_A','LAB_B']

def test_gate5_status_split():
    from sst_falsifier_framework.replication import gate5_statuses
    a=assess_replication([{'evidence_class':'synthetic_control','solver_id':'gen'}],2)
    s=gate5_statuses(a)
    assert s['G5_CONTROL_REPLICATION']=='PASS'
    assert s['G5_CROSS_SOURCE_REPLICATION']=='NOT_RUN_PREREQUISITE'
