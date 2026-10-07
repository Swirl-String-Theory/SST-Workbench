from pathlib import Path
import sys,tempfile,json
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from sst_falsifier_framework.gates import GateLedger,GateRecord
from sst_falsifier_framework.outputs import default_output_dir
from sst_falsifier_framework.sources import validate_dynamic_metadata
from a056_falsifier.pipeline import output_dir_for

def test_gate_dependency_fail_closed():
    g=GateLedger(); g.add(GateRecord('G0_PROVENANCE','FAIL','x',{}))
    try: g.add(GateRecord('G1_ADMISSIBILITY','PASS','x',{},depends_on=('G0_PROVENANCE',)))
    except ValueError: return
    assert False

def test_output_dir_is_local():
    p=default_output_dir(ROOT); assert p.parent==ROOT and p.name==ROOT.name+'-outputs'

def test_provider_contract_missing():
    r=validate_dynamic_metadata({'opaque_id':'x'},False); assert not r['pass'] and 'solver_id' in r['missing']


def test_pipeline_output_dir_tracks_package_folder(tmp_path):
    package_root=tmp_path/'A056-v0.2.0'
    assert output_dir_for(package_root)==package_root/'A056-v0.2.0-outputs'
