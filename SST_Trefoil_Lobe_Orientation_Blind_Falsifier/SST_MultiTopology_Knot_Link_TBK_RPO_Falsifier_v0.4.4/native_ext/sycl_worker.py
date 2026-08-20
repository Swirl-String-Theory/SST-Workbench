from __future__ import annotations
import atexit, json, os, platform, shutil, struct, subprocess, sys, threading
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'build'
EXE=BUILD/('sst_sycl_worker.exe' if platform.system().lower()=='windows' else 'sst_sycl_worker')
CPP=ROOT/'cpp'/'sycl_worker.cpp'
MAGIC_REQ=0x31545353
MAGIC_RES=0x52545353
CMD_F32=2
CMD_F64=3
CMD_QUIT=9
_LOCK=threading.RLock()
_PROC=None
_INFO=None

def _icpx():
    for x in (os.environ.get('ICPX'),os.environ.get('CXX'),'icpx'):
        if not x: continue
        p=Path(x)
        if p.exists(): return str(p)
        w=shutil.which(x)
        if w: return w
    for p in (Path(r'C:\Program Files (x86)\Intel\oneAPI\compiler\latest\bin\icpx.exe'),Path(r'C:\Program Files\Intel\oneAPI\compiler\latest\bin\icpx.exe')):
        if p.exists(): return str(p)
    return None

def build_worker(force=False,verbose=True):
    BUILD.mkdir(exist_ok=True)
    if EXE.exists() and not force and EXE.stat().st_mtime>=CPP.stat().st_mtime: return True
    cxx=_icpx()
    if not cxx:
        if verbose: print('[SST-SYCL-WORKER] icpx not found; call oneAPI setvars.bat first',file=sys.stderr)
        return False
    cmd=[cxx,'-fsycl','-fsycl-device-code-split=per_kernel','-O3','-std=c++17',str(CPP),'-o',str(EXE)]
    if verbose: print('[SST-SYCL-WORKER] compile:',' '.join(cmd),file=sys.stderr)
    cp=subprocess.run(cmd,cwd=str(ROOT),text=True,capture_output=True)
    if cp.returncode!=0:
        if verbose: print((cp.stdout+'\n'+cp.stderr)[-12000:],file=sys.stderr)
        return False
    return EXE.exists()

def probe_worker(force_build=False,verbose=False):
    if not build_worker(force=force_build,verbose=verbose): return {'available':False,'error':'build_failed'}
    env=os.environ.copy();env.setdefault('SYCL_CACHE_PERSISTENT','0')
    try:
        cp=subprocess.run([str(EXE),'--probe'],cwd=str(ROOT),env=env,text=True,capture_output=True,timeout=30)
        if cp.returncode!=0: return {'available':False,'returncode':cp.returncode,'stderr':cp.stderr.strip()}
        d=json.loads(cp.stdout.strip().splitlines()[-1]);d.update(available=True,transport='external_process',executable=str(EXE))
        return d
    except Exception as e: return {'available':False,'error':f'{type(e).__name__}: {e}'}

def _read_exact(stream,n):
    b=bytearray()
    while len(b)<n:
        z=stream.read(n-len(b))
        if not z: raise RuntimeError('SYCL worker terminated while reading response')
        b.extend(z)
    return bytes(b)

def _start():
    global _PROC,_INFO
    with _LOCK:
        if _PROC is not None and _PROC.poll() is None: return _PROC
        info=probe_worker(verbose=False)
        if not info.get('available'): raise RuntimeError(f'SYCL worker unavailable: {info}')
        env=os.environ.copy();env.setdefault('SYCL_CACHE_PERSISTENT','0')
        _PROC=subprocess.Popen([str(EXE)],cwd=str(ROOT),env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
        # Worker writes readiness to stderr so stdout remains purely binary.
        line=_PROC.stderr.readline().decode('utf-8','replace').strip()
        if not line.startswith('SST_WORKER_READY '):
            rc=_PROC.poll(); raise RuntimeError(f'SYCL worker did not become ready (rc={rc}): {line}')
        try: _INFO=json.loads(line[len('SST_WORKER_READY '):])
        except Exception: _INFO=info
        _INFO.update(available=True,transport='persistent_external_process',executable=str(EXE))
        return _PROC

def worker_info(start=False):
    global _INFO
    if start:
        try: _start()
        except Exception as e: return {'available':False,'error':f'{type(e).__name__}: {e}'}
    if _INFO is not None: return dict(_INFO)
    return probe_worker(verbose=False)

def shutdown_worker():
    global _PROC
    with _LOCK:
        p=_PROC;_PROC=None
        if p is None: return
        try:
            if p.poll() is None and p.stdin:
                p.stdin.write(struct.pack('<II',MAGIC_REQ,CMD_QUIT));p.stdin.flush()
                p.wait(timeout=2)
        except Exception:
            try:p.kill()
            except Exception:pass
atexit.register(shutdown_worker)

def biot_savart(points,queries,gamma=1.0,core=0.04,require_fp64=False):
    p64=np.ascontiguousarray(points,dtype=np.float64);q64=np.ascontiguousarray(queries,dtype=np.float64)
    if p64.ndim!=2 or p64.shape[1]!=3 or q64.ndim!=2 or q64.shape[1]!=3: raise ValueError('points/queries must be Nx3')
    proc=_start();info=worker_info()
    use64=bool(info.get('fp64',False))
    if require_fp64 and not use64: raise RuntimeError(f"SYCL device {info.get('device_name')} has no native FP64")
    if not use64 and os.environ.get('SST_SYCL_ALLOW_FP32','0')!='1':
        raise RuntimeError('SYCL device has no native FP64. Set SST_SYCL_ALLOW_FP32=1 only for explicitly labeled screening runs.')
    dtype=np.float64 if use64 else np.float32;cmd=CMD_F64 if use64 else CMD_F32
    pp=np.ascontiguousarray(p64,dtype=dtype);qq=np.ascontiguousarray(q64,dtype=dtype)
    hdr=struct.pack('<IIQQdd',MAGIC_REQ,cmd,pp.shape[0],qq.shape[0],float(gamma),float(core))
    with _LOCK:
        if proc.stdin is None or proc.stdout is None: raise RuntimeError('worker pipes unavailable')
        proc.stdin.write(hdr);proc.stdin.write(pp.tobytes(order='C'));proc.stdin.write(qq.tobytes(order='C'));proc.stdin.flush()
        rh=_read_exact(proc.stdout,16);magic,status,nbytes=struct.unpack('<IIQ',rh)
        if magic!=MAGIC_RES: raise RuntimeError('bad worker response magic')
        payload=_read_exact(proc.stdout,nbytes)
        if status!=0: raise RuntimeError(payload.decode('utf-8','replace'))
    arr=np.frombuffer(payload,dtype=dtype).reshape((-1,3)).astype(np.float64,copy=False)
    return arr,('sycl-worker-fp64' if use64 else 'sycl-worker-fp32')
