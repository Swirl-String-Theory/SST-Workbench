"""Fail-closed self-contained and 2/3 tests (synthetic records, not hardware parity)."""
import hashlib,json,subprocess,sys
from pathlib import Path
import pytest
from sst_falsifier.auto_backend_matrix import run_auto_matrix
from sst_falsifier.pklsa_integration import check_atlas,resolve_paths


def _sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def _setup(tmp_path):
    root=tmp_path/'A123-v0.1.0';root.mkdir()
    (root/'experiment').mkdir();(root/'native'/'cpp').mkdir(parents=True)
    (root/'experiment'/'py.py').write_text('observable = 1.0\n')
    (root/'native'/'cpp'/'native.cpp').write_text('// compiled pybind11 kernel source\n')
    (root/'experiment'/'gpu.py').write_text('import torch\n')
    out=root/'run';out.mkdir()
    probes={k:{'available':True,'modules':[{'sha256':'dummy'}]} for k in ('py','cpp','gpu')}
    return root,out,probes

def _rec(root,out,kind,provider='intel',input_sha='a'*64,time=None,observable=(1.0,2.0)):
    actual={'py':'python','cpp':'pybind11','gpu':'torch_xpu' if provider=='intel' else 'torch_cuda'}[kind]
    source=root/('experiment/py.py' if kind=='py' else 'native/cpp/native.cpp' if kind=='cpp' else 'experiment/gpu.py')
    efile=out/'backend_science'/f'{kind}.json';efile.parent.mkdir(exist_ok=True)
    ev={'actual_backend':actual,'executed':True,'input_sha256':input_sha,'observable':list(observable),
        'precision':'float32' if kind=='gpu' else 'float64','physical_final_time':time}
    if kind=='cpp':ev['compiled_binary_sha256']='dummy'
    if kind=='gpu':ev['device_type']='xpu' if provider=='intel' else 'cuda'
    efile.write_text(json.dumps(ev)+'\n')
    return {'actual_backend':actual,'executed':True,'source_path':str(source), 'source_sha256':_sha(source),
            'evidence_path':str(efile),'evidence_sha256':_sha(efile),'observable':list(observable),'input_sha256':input_sha}

def test_python_and_cpp_meet_two_of_three_without_gpu(tmp_path):
    root,out,probes=_setup(tmp_path);probes['gpu']={'available':False}
    rec={'py':_rec(root,out,'py'),'cpp':_rec(root,out,'cpp')}
    got=run_auto_matrix(root,{'auto_backends':{},'gpu':{'provider':'intel'}},'FULL',out,probes=probes,science_override=rec)
    assert got['status']=='EXECUTION_CONTRACT_PASS'
    assert got['counted_backend_categories']==2
    assert got['scientific_gate_qualified'] is False
    assert 'gpu' not in got['executed_backend_categories']

def test_python_intel_pair_meets_two_of_three_without_cpp(tmp_path):
    root,out,probes=_setup(tmp_path);probes['cpp']={'available':False}
    rec={'py':_rec(root,out,'py'),'gpu':_rec(root,out,'gpu')}
    got=run_auto_matrix(root,{'auto_backends':{},'gpu':{'provider':'intel'}},'FULL',out,probes=probes,science_override=rec)
    assert got['status']=='EXECUTION_CONTRACT_PASS'
    assert got['policy']['selected_gpu_provider']=='intel'

def test_cuda_opt_in_not_counted_twice(tmp_path):
    root,out,probes=_setup(tmp_path)
    rec={'py':_rec(root,out,'py'),'gpu':_rec(root,out,'gpu',provider='cuda')}
    got=run_auto_matrix(root,{'auto_backends':{},'gpu':{'provider':'cuda'}},'FULL',out,probes=probes,science_override=rec)
    assert got['counted_backend_categories']==2
    assert 'cuda' not in got['executed_backend_categories']

def test_one_backend_blocks(tmp_path):
    root,out,probes=_setup(tmp_path)
    rec={'py':_rec(root,out,'py')}
    got=run_auto_matrix(root,{'auto_backends':{}},'FULL',out,probes=probes,science_override=rec)
    assert got['status']=='EXECUTION_CONTRACT_BLOCKED'
    assert got['counted_backend_categories']==1

def test_inconsistent_input_hash_blocks_pair(tmp_path):
    root,out,probes=_setup(tmp_path)
    rec={'py':_rec(root,out,'py'),'cpp':_rec(root,out,'cpp',input_sha='b'*64)}
    got=run_auto_matrix(root,{'auto_backends':{}},'FULL',out,probes=probes,science_override=rec)
    assert got['counted_backend_categories']==0

def test_inconsistent_final_time_blocks_pair(tmp_path):
    root,out,probes=_setup(tmp_path)
    rec={'py':_rec(root,out,'py',time=0.2),'cpp':_rec(root,out,'cpp',time=0.25)}
    got=run_auto_matrix(root,{'auto_backends':{}},'FULL',out,probes=probes,science_override=rec)
    assert got['counted_backend_categories']==0

def test_forged_source_hash_rejected(tmp_path):
    root,out,probes=_setup(tmp_path)
    rec={'py':_rec(root,out,'py'),'cpp':_rec(root,out,'cpp')}
    rec['cpp']['source_sha256']='0'*64
    got=run_auto_matrix(root,{'auto_backends':{}},'FULL',out,probes=probes,science_override=rec)
    assert got['scientific']['cpp']['status']=='REJECTED'
    assert got['counted_backend_categories']==1

def test_no_gpu_provider_substitution(tmp_path):
    root,out,probes=_setup(tmp_path)
    rec={'py':_rec(root,out,'py'),'gpu':_rec(root,out,'gpu',provider='cuda')}
    got=run_auto_matrix(root,{'auto_backends':{},'gpu':{'provider':'intel'}},'FULL',out,probes=probes,science_override=rec)
    assert got['scientific']['gpu']['status']=='REJECTED'
    assert got['counted_backend_categories']==1

def test_intel_and_cuda_are_not_two_categories(tmp_path):
    root,out,probes=_setup(tmp_path)
    rec={'gpu':_rec(root,out,'gpu')}
    rec['cuda']=rec['gpu'].copy()
    got=run_auto_matrix(root,{'auto_backends':{}},'FULL',out,probes=probes,science_override=rec)
    assert got['counted_backend_categories']==1

def test_disabling_minimum_refused(tmp_path):
    root,out,probes=_setup(tmp_path)
    with pytest.raises(ValueError,match='prohibits disabling'):
        run_auto_matrix(root,{'auto_backends':{'enabled':False}},'FULL',out,probes=probes,science_override={})

def test_atlas_absence_is_fail_closed(tmp_path, monkeypatch):
    """Isolate the absent atlas even on a host with SST_WORKBENCH_ROOT set.

    Empty configuration does not mean no atlas: on a real Workbench machine
    autodiscovery is expected to find E010. Build an isolated test workbench
    containing a recognisable adapter but deliberately no E010 payload.
    """
    root=tmp_path/'A123';root.mkdir()
    wb=tmp_path/'isolated_workbench'
    bridge=wb/'04_tools'/'A_geometry'/'PKLSA_Universal_Atlas_Adapter'/'pklsa_bridge'
    bridge.mkdir(parents=True)
    (bridge/'__init__.py').write_text('__version__ = "0.1.0"\n',encoding='utf8')
    monkeypatch.delenv('E010_ATLAS',raising=False)
    # Explicit workbench scope takes precedence over inherited environment.
    result=check_atlas(root,{},workbench=wb)
    assert result['status']=='BLOCKED' and result['no_silent_fallback']
    assert 'Pinned E010-v0.4.0 ZIP/index not found' in result['reason']


def test_atlas_missing_workbench_env_is_fail_closed(tmp_path, monkeypatch):
    """An invalid locator must never trigger silent fallback."""
    root=tmp_path/'A124';root.mkdir()
    monkeypatch.setenv('SST_WORKBENCH_ROOT',str(tmp_path/'nonexistent_workbench'))
    monkeypatch.delenv('E010_ATLAS',raising=False)
    result=check_atlas(root,{})
    assert result['status']=='BLOCKED' and result['no_silent_fallback']
    assert 'PKLSA_Universal_Atlas_Adapter' in result['reason']

