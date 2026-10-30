"""Native CUDA DD32 (FP32x2) Biot-Savart reference adapter.

Development backend, requires nvcc 12.x, MSVC x64 on Windows and an NVIDIA GPU.
No torch-based FP32 fallback. A preflight is not scientific execution evidence.
"""
from __future__ import annotations
import hashlib,json,os,platform,shutil,struct,subprocess,tempfile
from pathlib import Path
import numpy as np
from .backend_contract import BackendResult
from .util import sha256_file,write_json

SOURCE_REL=Path('native/cuda/cuda_dd32.cu')

def _nvcc():
    env=os.environ.get('SST_NVCC')
    if env: return shutil.which(env) or (str(Path(env)) if Path(env).is_file() else None)
    from_path=shutil.which('nvcc')
    if from_path:return from_path
    cuda_path=os.environ.get('CUDA_PATH')
    if cuda_path:
        p=Path(cuda_path)/'bin'/('nvcc.exe' if os.name=='nt' else 'nvcc')
        if p.is_file():return str(p)
    return None

def _build_env():
    if os.name=='nt':
        from .sycl_worker import _with_msvc_environment
        env,_=_with_msvc_environment()
        return env
    return dict(os.environ)

def executable(root):return Path(root)/'build'/('sst_cuda_dd32.exe' if os.name=='nt' else 'sst_cuda_dd32')

def build_worker(root,*,force=False):
    root=Path(root).resolve();src=root/SOURCE_REL;exe=executable(root)
    if not src.is_file():return {'success':False,'error':f'Missing source {SOURCE_REL}'}
    nvcc=_nvcc()
    if not nvcc:return {'success':False,'error':'nvcc 12.x not found; CUDA DD32 requires native compiler'}
    arch=os.environ.get('SST_CUDA_ARCH','sm_61')
    if not (arch.startswith('sm_') and arch[3:].isdigit()):return {'success':False,'error':'invalid SST_CUDA_ARCH'}
    flags=['-std=c++17','-O3',f'-arch={arch}','--ftz=false','--prec-div=true','--prec-sqrt=true']
    if os.name=='nt':flags+=['-Xcompiler=/fp:precise']
    cv=subprocess.run([nvcc,'--version'],capture_output=True,text=True,timeout=30)
    version=(cv.stdout+'\n'+cv.stderr).strip().splitlines()[-1]
    if 'release 13.' in version:return {'success':False,'error':'CUDA 13 unsupported for GTX 1060/Pascal','compiler_version':version}
    fingerprint=hashlib.sha256(json.dumps({'sha256':sha256_file(src),'nvcc':nvcc,'version':version,'flags':flags},sort_keys=True).encode()).hexdigest()
    stamp=exe.parent/'CUDA_DD32_BUILD.json'
    if not force and exe.exists() and stamp.is_file():
        try:
            old=json.loads(stamp.read_text())
            if old['fingerprint_sha256']==fingerprint and old['binary_sha256']==sha256_file(exe):return old
        except (KeyError,ValueError):pass
    exe.parent.mkdir(parents=True,exist_ok=True)
    cp=subprocess.run([nvcc,*flags,str(src),'-o',str(exe)],cwd=root,env=_build_env(),capture_output=True,text=True,timeout=240)
    if cp.returncode!=0 or not exe.is_file():return {'success':False,'error':(cp.stdout+'\n'+cp.stderr)[-6000:],'returncode':cp.returncode,'compiler_version':version}
    result={'success':True,'source_sha256':sha256_file(src),'binary_sha256':sha256_file(exe),
            'fingerprint_sha256':fingerprint,'compiler':nvcc,'compiler_version':version,'flags':flags,'precision':'dd32-fp32x2'}
    write_json(stamp,result);return result

def probe_worker(root):
    b=build_worker(root)
    if not b.get('success'):return {'available':False,'build':b,'precision':'dd32-fp32x2'}
    try:
        cp=subprocess.run([str(executable(root)),'--probe'],capture_output=True,text=True,timeout=45,env=_build_env())
        if cp.returncode:raise RuntimeError((cp.stderr or cp.stdout)[-2000:])
        info=json.loads(cp.stdout.strip());info.update({'build':b,'binary_sha256':b['binary_sha256'],
                      'precision':'dd32-fp32x2','available':True,'provider':'cuda'})
        return info
    except (ValueError,RuntimeError,subprocess.TimeoutExpired) as ex:
        return {'available':False,'build':b,'error':f'{type(ex).__name__}: {ex}'}

def biot_savart(root,points,queries,gamma=1.0,core=0.04,*,require=True,timeout=1200):
    root=Path(root).resolve()
    p=np.ascontiguousarray(points,dtype=np.float64);q=np.ascontiguousarray(queries,dtype=np.float64)
    if p.ndim!=2 or q.ndim!=2 or p.shape[1]!=3 or q.shape[1]!=3 or len(p)<3 or len(q)<1:
        raise ValueError('Expected points Nx3 and queries Mx3')
    if not (np.isfinite(p).all() and np.isfinite(q).all() and np.isfinite(gamma) and np.isfinite(core) and core>0):
        raise ValueError('Nonfinite input or nonpositive core')
    info=probe_worker(root)
    if not info.get('available'):raise RuntimeError('CUDA DD32 unavailable: '+json.dumps(info,default=str))
    with tempfile.TemporaryDirectory(prefix='sst_cuda_dd32_') as d:
        input_path=Path(d)/'input.bin';output_path=Path(d)/'result.bin'
        with input_path.open('wb') as f:
            f.write(b'SSTDD321');f.write(struct.pack('<IIdd',len(p),len(q),float(gamma),float(core)))
            f.write(p.tobytes());f.write(q.tobytes())
        cp=subprocess.run([str(executable(root)),str(input_path),str(output_path)],cwd=root,env=_build_env(),
                         capture_output=True,text=True,timeout=timeout)
        if cp.returncode:raise RuntimeError('CUDA DD32 execution failed: '+(cp.stderr or cp.stdout)[-3000:])
        b=output_path.read_bytes()
        if len(b)!=len(q)*3*8:raise RuntimeError('Invalid CUDA DD32 output length')
        out=np.frombuffer(b,dtype='<f8').reshape(len(q),3).copy()
        if not np.isfinite(out).all():raise RuntimeError('Nonfinite CUDA DD32 result')
    result=BackendResult('cuda','cuda-native-dd32','dd32-fp32x2','SCREENING_ONLY',True,
                         {'ieee_fp64':False,'transport':'fp64-host/fp32x2-device/fp64-host',
                          'binary_sha256':info['binary_sha256'],'compute_capability':info.get('compute_capability')},
                         sha256_file(root/SOURCE_REL),info['build']['fingerprint_sha256'],info.get('device_name'))
    return out,result
