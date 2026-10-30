"""Host-side fail-closed DD32 policy tests. These DO NOT certify native GPU execution."""
import hashlib,json
from pathlib import Path
import pytest
from sst_falsifier.auto_backend_matrix import run_auto_matrix
from sst_falsifier.cuda_dd32 import build_worker,biot_savart
from sst_falsifier.sycl_worker import _exe

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def tree(tmp_path):
    root=tmp_path/'instance';out=root/'run';out.mkdir(parents=True)
    (root/'experiment').mkdir();(root/'native/cpp').mkdir(parents=True)
    (root/'native/cuda').mkdir(parents=True)
    (root/'native/cpp/sycl_worker.cpp').write_text('// code')
    (root/'native/cuda/cuda_dd32.cu').write_text('// code')
    (root/'experiment/py.py').write_text('// code')
    (root/'native/cpp/native.cpp').write_text('// code')
    (root/'build').mkdir()
    _exe(root).write_bytes(b'fake-native-for-unit-test')
    return root,out

def make_rec(root,out,kind,precision,backend):
    src=root/('native/cpp/sycl_worker.cpp' if backend=='sycl-native-dd32' else 'experiment/py.py')
    evidence=out/'backend_science'/f'{kind}.json';evidence.parent.mkdir(exist_ok=True)
    data={'actual_backend':backend,'executed':True,'input_sha256':'a'*64,'observable':[1.,2.,3.],
          'precision':precision,'physical_final_time':None,'device_type':'xpu'}
    if kind=='gpu':data['compiled_binary_sha256']=digest(_exe(root))
    evidence.write_text(json.dumps(data))
    return {'actual_backend':backend,'executed':True,'source_path':str(src),'source_sha256':digest(src),
           'evidence_path':str(evidence),'evidence_sha256':digest(evidence),'observable':data['observable'],
           'input_sha256':'a'*64}

def test_native_dd32_execution_is_accepted_with_binary_hash(tmp_path):
    root,out=tree(tmp_path)
    rec={'py':make_rec(root,out,'py','float64','python'),
         'gpu':make_rec(root,out,'gpu','dd32-fp32x2','sycl-native-dd32')}
    probes={'py':{'available':True},'cpp':{'available':False},
            'gpu':{'available':True,'native_worker':{'build':{'success':True}}}}
    actual=run_auto_matrix(root,{'gpu':{'provider':'intel','precision':'dd32'}},'FULL',out,
                           probes=probes,science_override=rec)
    assert actual['status']=='EXECUTION_CONTRACT_PASS'
    assert actual['counted_backend_categories']==2
    assert actual['scientific']['gpu']['precision']=='dd32-fp32x2'
    assert actual['policy']['gpu_precision']=='dd32'

def test_fp32_cannot_fulfil_dd32_policy(tmp_path):
    root,out=tree(tmp_path)
    rec={'py':make_rec(root,out,'py','float64','python'),
         'gpu':make_rec(root,out,'gpu','float32','sycl-native-dd32')}
    probes={'py':{'available':True},'cpp':{'available':False},
            'gpu':{'available':True,'native_worker':{'build':{'success':True}}}}
    actual=run_auto_matrix(root,{'gpu':{'provider':'intel','precision':'dd32'}},'FULL',out,
                           probes=probes,science_override=rec)
    assert actual['status']=='EXECUTION_CONTRACT_BLOCKED'
    assert 'DD32 precision policy violated' in actual['scientific']['gpu']['reason']

def test_wrong_native_binary_rejected(tmp_path):
    root,out=tree(tmp_path)
    rec={'py':make_rec(root,out,'py','float64','python'),
         'gpu':make_rec(root,out,'gpu','dd32-fp32x2','sycl-native-dd32')}
    evidence=out/'backend_science/gpu.json'
    e=json.loads(evidence.read_text());e['compiled_binary_sha256']='0'*64;evidence.write_text(json.dumps(e))
    rec['gpu']['evidence_sha256']=digest(evidence)
    probes={'py':{'available':True},'cpp':{'available':False},
            'gpu':{'available':True,'native_worker':{'build':{'success':True}}}}
    actual=run_auto_matrix(root,{'gpu':{'provider':'intel','precision':'dd32'}},'FULL',out,
                           probes=probes,science_override=rec)
    assert actual['status']=='EXECUTION_CONTRACT_BLOCKED'
    assert 'Native DD32 GPU binary differs' in actual['scientific']['gpu']['reason']

def test_cuda_dd32_does_not_fake_native_worker(tmp_path):
    r=build_worker(tmp_path)
    assert not r['success']
    assert 'Missing source' in r['error']

def test_dd32_default_in_new_gpu_template():
    from pathlib import Path
    txt=(Path(__file__).parents[1]/'instance_template/falsifier.toml').read_text()
    assert 'precision = "dd32"' in txt

def test_gpu_dd32_preflight_without_compiler_is_blocked(monkeypatch,tmp_path):
    import sst_falsifier.cuda_dd32 as module
    src=tmp_path/'native/cuda/cuda_dd32.cu'
    src.parent.mkdir(parents=True)
    src.write_text('// example')
    monkeypatch.setattr(module,'_nvcc',lambda:None)
    got=module.probe_worker(tmp_path)
    assert got['available'] is False
    assert 'nvcc' in got['build']['error']

def test_no_cuda_torch_fp32_substitute_when_dd32_configured(tmp_path):
    from sst_falsifier.auto_backend_matrix import _record
    root,out=tree(tmp_path)
    claim=make_rec(root,out,'gpu','float32','torch_cuda')
    assert _record('gpu',claim,{'available':True},root,out,'cuda','dd32')['status']=='REJECTED'

def test_dd32_a999_report_uses_precision_tokens():
    root=Path(__file__).parents[1]
    text=(root/'integration/a999_control/report.tex').read_text()
    assert '@@GPU_PRECISION_TEXT@@' in text
    assert '@@GPU_TOL_LATEX@@' in text
    script=(root/'tools/prepare_a999_e010.py').read_text()
    assert "'10^{-8}' if precision=='dd32'" in script
