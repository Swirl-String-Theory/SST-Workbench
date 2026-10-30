"""v1.1.0 2-of-3 execution contract; hardware probes are NOT science evidence.

Categories: Python FP64, C++/pybind11, GPU (Intel XPU default / CUDA opt-in).
An absent adapter is a genuine blocked qualification, never fabricated execution.
"""
from __future__ import annotations
import hashlib, importlib.util, json, math, os, platform, sys
from pathlib import Path
from .util import write_json

BACKENDS=('py','cpp','gpu')
SCHEMA='SST-BACKEND-MATRIX-2OF3-v1.1.0'

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def _python_probe():
    try:
        import numpy as np
        x=np.ones((8,8,8),dtype=np.float64); y=np.fft.fftn(x)
        ok=bool(np.isfinite(y).all() and abs(y[0,0,0]-512)<1e-10)
        return {'available':ok,'status':'DEVICE_READY' if ok else 'BLOCKED','actual':'numpy.cpu','precision':'float64','numpy':np.__version__,'scientific_execution':False}
    except Exception as e:return {'available':False,'status':'BLOCKED','reason':f'{type(e).__name__}: {e}','scientific_execution':False}

def _cpp_probe(root):
    try:
        from .native_build import build_pybind
        found=importlib.util.find_spec('pybind11') is not None
        source=root/'native'/'cpp'/'native.cpp'
        if not found or not source.is_file():
            return {'available':False,'status':'BLOCKED','reason':'pybind11 or native.cpp missing','scientific_execution':False}
        build=None
        if os.environ.get('SST_DISABLE_NATIVE_AUTOBUILD','0')!='1':
            try:build=build_pybind(root,verbose=False).to_dict()
            except Exception as ex:build={'success':False,'error':f'{type(ex).__name__}: {ex}'}
        compiled=list((root/'native_ext').glob('_sst_native*.pyd'))+list((root/'native_ext').glob('_sst_native*.so'))
        abi=getattr(sys.implementation,'cache_tag','')
        if platform.system()=='Windows': compiled=[p for p in compiled if ('cp'+abi.replace('cpython-','')) in p.name]
        ready=bool(compiled and (build is None or build.get('success',False)))
        return {'available':ready,'status':'DEVICE_READY' if ready else 'BLOCKED',
                'source_sha256':digest(source),'modules':[{'path':p.name,'sha256':digest(p)} for p in compiled],
                'build':build,'scientific_execution':False,'note':'Compiled module presence does not verify a scientific kernel.'}
    except Exception as e:return {'available':False,'status':'BLOCKED','reason':f'{type(e).__name__}: {e}','scientific_execution':False}

def _gpu_probe(provider):
    if provider not in ('intel','cuda'):return {'available':False,'status':'BLOCKED','reason':'provider must be intel or cuda','scientific_execution':False}
    try:
        import torch
        if provider=='intel':
            if not getattr(torch.version,'xpu',None) or not hasattr(torch,'xpu') or not torch.xpu.is_available():raise RuntimeError('PyTorch XPU/device unavailable')
            device='xpu:0'; name=str(torch.xpu.get_device_name(0)); sync=torch.xpu.synchronize
        else:
            if not getattr(torch.version,'cuda',None) or not torch.cuda.is_available():raise RuntimeError('PyTorch CUDA/device unavailable')
            device='cuda:0';name=str(torch.cuda.get_device_name(0));sync=torch.cuda.synchronize
        x=torch.ones((8,8,8),device=device,dtype=torch.float32)
        y=torch.fft.fftn(x);sync()
        actual=float(y[0,0,0].real.cpu())
        ok=(abs(actual-512)<0.02 and y.device.type==('xpu' if provider=='intel' else 'cuda'))
        return {'available':bool(ok),'status':'DEVICE_READY' if ok else 'BLOCKED','provider':provider,'device':name,
                'device_type':str(y.device),'torch_version':str(torch.__version__),'precision':'float32',
                'fft_probe':actual,'scientific_execution':False,
                'note':'An FFT smoke-test is not proof of solver execution, parity, or FP64.'}
    except Exception as e:return {'available':False,'status':'BLOCKED','provider':provider,'reason':f'{type(e).__name__}: {e}','scientific_execution':False}

def probe_all(root,provider='intel'):
    return {'py':_python_probe(),'cpp':_cpp_probe(root),'gpu':_gpu_probe(provider)}

def _under(path,root):
    p=Path(path)
    p=(p if p.is_absolute() else root/p).resolve()
    if not p.is_relative_to(root.resolve()): raise ValueError('evidence path escapes audited tree')
    if not p.is_file():raise FileNotFoundError(f'missing evidence file: {p}')
    return p

def _record(kind,claimed,probe,root,out,provider):
    if not isinstance(claimed,dict):return {'status':'UNIMPLEMENTED','scientific_execution':False,'reason':'No executed scientific adapter record'}
    if claimed.get('executed') is not True:return {'status':'NOT_EXECUTED','scientific_execution':False,'reason':'executed != true'}
    actual=str(claimed.get('actual_backend','')).lower()
    types={'py':'python','cpp':'pybind11','gpu':'torch_xpu' if provider=='intel' else 'torch_cuda'}
    if actual!=types[kind]:return {'status':'REJECTED','scientific_execution':False,'reason':f'{kind} must identify actual_backend={types[kind]}, not {actual!r}'}
    if not probe.get('available'):return {'status':'BLOCKED','scientific_execution':False,'reason':'backend availability check failed'}
    try:
        src=_under(claimed['source_path'],root)
        ev=_under(claimed['evidence_path'],out)
        if claimed.get('source_sha256')!=digest(src):raise ValueError('source hash mismatch')
        if claimed.get('evidence_sha256')!=digest(ev):raise ValueError('execution evidence hash mismatch')
        payload=json.loads(ev.read_text(encoding='utf8'))
        if payload.get('actual_backend')!=types[kind] or payload.get('executed') is not True:raise ValueError('evidence backend/executed mismatch')
        if payload.get('input_sha256')!=claimed.get('input_sha256'):raise ValueError('input identity mismatch')
        observed=payload.get('observable'); expected=claimed.get('observable')
        if not isinstance(observed,list) or observed!=expected or not observed:raise ValueError('observable mismatch/empty')
        if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in observed):raise ValueError('observable not finite')
        if not isinstance(claimed.get('input_sha256'),str) or len(claimed['input_sha256'])!=64:raise ValueError('invalid input SHA-256')
        if not isinstance(payload.get('precision'),str) or not payload['precision']:raise ValueError('missing precision evidence')
        if 'physical_final_time' not in payload: raise ValueError('missing physical final time evidence (null allowed for static checks)')

        if kind=='cpp':
            if src.suffix.lower() not in ('.cpp','.cc','.cxx') or 'native' not in src.parts:
                raise ValueError('C++ source must be a native source file under the instance')
            modules=probe.get('modules',[])
            binary=payload.get('compiled_binary_sha256')
            if not binary or binary not in {m.get('sha256') for m in modules}:
                raise ValueError('Missing binary hash match with preflight-verified native pybind11 module')
        if kind=='gpu':
            required='xpu' if provider=='intel' else 'cuda'
            if payload.get('device_type')!=required:
                raise ValueError('GPU evidence missing required torch device_type='+required)

        return {'status':'EXECUTED','scientific_execution':True,'actual_backend':actual,'observable':observed,
                'input_sha256':claimed['input_sha256'],'source_sha256':digest(src),'evidence_sha256':digest(ev),
                'precision':payload['precision'],'physical_final_time':payload['physical_final_time'],
                'source_path':str(src.relative_to(root)),'evidence_path':str(ev.relative_to(out)),
                'scientific_gate_qualified':False}
    except (KeyError,FileNotFoundError,ValueError,TypeError,json.JSONDecodeError) as e:
        return {'status':'REJECTED','scientific_execution':False,'reason':f'{type(e).__name__}: {e}'}

def _science_adapter(root,cfg,mode,out,devices):
    source=root/'experiment'/'backend_matrix.py'
    if not source.is_file():return {},'UNIMPLEMENTED: experiment/backend_matrix.py missing'
    spec=importlib.util.spec_from_file_location('_sst_instance_science_1100',source)
    if spec is None or spec.loader is None:return {},'INVALID: cannot load adapter'
    mod=importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        fn=getattr(mod,'run_backend_matrix',None)
        if not callable(fn):return {},'UNIMPLEMENTED: run_backend_matrix missing'
        result=fn(root=root,cfg=cfg,mode=mode,output_dir=out/'backend_science',devices=devices)
        if not isinstance(result,dict):raise ValueError('Adapter must return a dictionary keyed by py, cpp, gpu')
        return result,'CALLED'
    except Exception as e:return {},f'ERROR: {type(e).__name__}: {e}'

def run_auto_matrix(root,cfg,mode,out,backend_manifest=None,*,probes=None,science_override=None):
    root=Path(root).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    cfg_backend=cfg.get('auto_backends',{})
    if cfg_backend.get('enabled',True) is not True: raise ValueError('v1.1.0 prohibits disabling the mandatory backend contract')
    minimum=int(cfg_backend.get('minimum_science_backends',2))
    if minimum!=2:raise ValueError('v1.1.0 requires precisely minimum_science_backends=2')
    provider=cfg.get('gpu',{}).get('provider','intel')
    if provider not in ('intel','cuda'): raise ValueError('GPU provider must be intel or cuda')
    devices=probes if probes is not None else probe_all(root,provider)
    science,adapter_state=(science_override,'TEST_INJECTION') if science_override is not None else _science_adapter(root,cfg,mode,out,devices)
    records={k:_record(k,science.get(k),devices.get(k,{}),root,out,provider) for k in BACKENDS}
    qualified=[k for k in BACKENDS if records[k]['scientific_execution']]
    inputs={records[k]['input_sha256'] for k in qualified}
    times={json.dumps(records[k]['physical_final_time'],sort_keys=True) for k in qualified}
    same_inputs=len(inputs)==1 and len(times)==1
    # Refuse to count executions with incompatible input identity or physical final time.
    result_count=len(qualified) if same_inputs else 0
    pairwise={}
    if len(qualified)>=2 and same_inputs:
        import numpy as np
        ref=np.array(records[qualified[0]]['observable'],dtype=float)
        for k in qualified[1:]:
            arr=np.array(records[k]['observable'],dtype=float)
            if arr.shape!=ref.shape:
                pairwise[k]={'status':'INCOMPATIBLE_SHAPE'};continue
            rel=float(np.linalg.norm(arr-ref)/max(np.linalg.norm(ref),1e-30))
            pairwise[k]={'relative_l2':rel,'status':'MEASURED_ONLY','reference':qualified[0]}
    status='EXECUTION_CONTRACT_PASS' if result_count>=2 else 'EXECUTION_CONTRACT_BLOCKED'
    matrix={'schema':SCHEMA,'framework_version':'1.1.0','mode':mode,'policy':{'minimum_science_backends':2,
            'selected_gpu_provider':provider,'no_implicit_fallback':True},'device_probes':devices,
            'adapter_status':adapter_state,'scientific':records,'executed_backend_categories':qualified,
            'counted_backend_categories':result_count,'same_input_and_time':same_inputs,'parity_diagnostics':pairwise,
            'status':status,'scientific_gate_qualified':False,
            'note':'2/3 establishes verified execution records, not hydrodynamic validity, numerical convergence or independent physical corroboration.'}
    write_json(out/'AUTO_BACKEND_MATRIX.json',matrix)
    return matrix
