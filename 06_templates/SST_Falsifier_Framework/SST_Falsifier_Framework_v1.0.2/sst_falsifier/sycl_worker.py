from __future__ import annotations
from pathlib import Path
import atexit,json,os,platform,shutil,struct,subprocess,threading,time
import numpy as np
from .backend_contract import BackendResult
from .util import sha256_file,canonical_json_sha256,write_json

MAGIC_REQ=0x32545353; MAGIC_RES=0x32525353; VERSION=3
CMD_BIOT_F32=2; CMD_BIOT_F64=3; CMD_BIOT_DD32=4; CMD_QUIT=9
_LOCK=threading.RLock(); _PROCS={}; _INFOS={}


def _exe(root): return Path(root)/"build"/("sst_sycl_worker.exe" if platform.system().lower()=="windows" else "sst_sycl_worker")
def _src(root): return Path(root)/"native"/"cpp"/"sycl_worker.cpp"

def _icpx():
    for x in (os.environ.get("ICPX"),os.environ.get("CXX"),"icpx"):
        if not x: continue
        p=Path(x)
        if p.exists(): return str(p)
        q=shutil.which(x)
        if q: return q
    for p in (Path(r"C:\Program Files (x86)\Intel\oneAPI\compiler\latest\bin\icpx.exe"),Path(r"C:\Program Files\Intel\oneAPI\compiler\latest\bin\icpx.exe")):
        if p.exists(): return str(p)
    return None


def _parse_cmd_environment(text):
    env={}
    for line in text.splitlines():
        if "=" not in line or line.startswith("="): continue
        k,v=line.split("=",1)
        if k: env[k]=v
    return env

def _oneapi_env_script(cxx=None):
    if platform.system().lower()!="windows": return None
    candidates=[]
    for key in ("ONEAPI_ROOT","ONEAPI_ROOT_DIR"):
        if os.environ.get(key):
            r=Path(os.environ[key]); candidates += [r/"setvars.bat", r/"oneapi-vars.bat"]
    if cxx:
        try:
            cp=Path(cxx).resolve()
            for a in [cp.parent,*cp.parents]:
                if a.name.lower()=="oneapi":
                    candidates.append(a/"setvars.bat"); candidates += sorted(a.glob("*/oneapi-vars.bat"),reverse=True); break
                if (a/"oneapi-vars.bat").exists(): candidates.append(a/"oneapi-vars.bat")
        except Exception: pass
    for r in (Path(r"C:\Program Files (x86)\Intel\oneAPI"),Path(r"C:\Program Files\Intel\oneAPI")):
        candidates.append(r/"setvars.bat")
        if r.exists(): candidates += sorted(r.glob("*/oneapi-vars.bat"),reverse=True)
    seen=set()
    for p in candidates:
        q=str(p).lower()
        if q in seen: continue
        seen.add(q)
        if p.exists(): return p
    return None

def _with_oneapi_environment(cxx, base_env=None):
    env=dict(base_env or os.environ)
    if platform.system().lower()!="windows": return env,None
    for d in env.get("LIB","").split(";"):
        if d and (Path(d)/"libmmd.lib").exists(): return env,"existing-environment"
    script=_oneapi_env_script(cxx)
    if not script: return env,None
    cmd=f'call "{script}" >nul && set'
    try:
        cp=subprocess.run(["cmd.exe","/d","/s","/c",cmd],text=True,capture_output=True,env=env,timeout=120)
        if cp.returncode==0:
            newenv=_parse_cmd_environment(cp.stdout)
            if newenv: env.update(newenv); return env,str(script)
    except Exception: pass
    return env,str(script)


def build_worker(instance_root,*,force=False,verbose=True):
    root=Path(instance_root).resolve(); src=_src(root); exe=_exe(root); exe.parent.mkdir(exist_ok=True); cxx=_icpx()
    if not cxx: return {"success":False,"error":"icpx not found"}
    build_env,env_script=_with_oneapi_environment(cxx)
    try:
        ver=subprocess.run([cxx,"--version"],text=True,capture_output=True,timeout=8,env=build_env); cv=(ver.stdout or ver.stderr).splitlines()[0]
    except Exception: cv=None
    # DD32 relies on error-free transforms. Reassociation/fast-math would invalidate them.
    flags=["-fsycl","-fsycl-device-code-split=per_kernel","-O3","-std=c++17","-fp-model=precise"]
    fp=canonical_json_sha256({"source_sha256":sha256_file(src),"compiler":cxx,"compiler_version":cv,"flags":flags,"protocol":VERSION})
    stamp=exe.parent/"SYCL_WORKER_BUILD.json"
    if not force and exe.exists() and stamp.exists():
        try:
            old=json.loads(stamp.read_text(encoding="utf-8"))
            if old.get("fingerprint_sha256")==fp: return {**old,"success":True}
        except Exception: pass
    if force: exe.unlink(missing_ok=True)
    cp=subprocess.run([cxx,*flags,str(src),"-o",str(exe)],cwd=str(root),env=build_env,text=True,capture_output=True)
    if cp.returncode!=0 or not exe.exists():
        return {"success":False,"fingerprint_sha256":fp,"compiler":cxx,"compiler_version":cv,"flags":flags,"oneapi_env_script":env_script,"lib":build_env.get("LIB"),"error":(cp.stdout+"\n"+cp.stderr)[-10000:]}
    d={"success":True,"artifact":str(exe),"fingerprint_sha256":fp,"compiler":cxx,"compiler_version":cv,"flags":flags,"oneapi_env_script":env_script}; write_json(stamp,d); return d


def _worker_env(info=None):
    env=os.environ.copy(); env.setdefault("SYCL_CACHE_PERSISTENT","0")
    cxx=((info or {}).get("build") or {}).get("compiler") or _icpx()
    if cxx:
        env,_=_with_oneapi_environment(cxx,env)
    return env

def probe_worker(instance_root,*,force_build=False):
    root=Path(instance_root).resolve(); b=build_worker(root,force=force_build,verbose=False)
    if not b.get("success"): return {"available":False,"build":b}
    try:
        cp=subprocess.run([str(_exe(root)),"--probe"],cwd=str(root),env=_worker_env({"build":b}),text=True,capture_output=True,timeout=30)
        if cp.returncode!=0: return {"available":False,"returncode":cp.returncode,"stderr":cp.stderr.strip(),"build":b}
        d=json.loads(cp.stdout.strip().splitlines()[-1]); d.update(available=True,transport="external_process",build=b); return d
    except Exception as e: return {"available":False,"error":f"{type(e).__name__}: {e}","build":b}

def _read_exact(stream,n):
    b=bytearray()
    while len(b)<n:
        z=stream.read(n-len(b))
        if not z: raise RuntimeError("SYCL worker terminated")
        b.extend(z)
    return bytes(b)

def _start(instance_root):
    root=str(Path(instance_root).resolve())
    with _LOCK:
        p=_PROCS.get(root)
        if p is not None and p.poll() is None: return p
        info=probe_worker(root)
        if not info.get("available"): raise RuntimeError(f"SYCL worker unavailable: {info}")
        p=subprocess.Popen([str(_exe(root))],cwd=root,env=_worker_env(info),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
        line=p.stderr.readline().decode("utf-8","replace").strip()
        if not line.startswith("SST_WORKER_READY "): raise RuntimeError(f"worker not ready: {line}")
        wi=json.loads(line[len("SST_WORKER_READY "):]); wi.update(available=True,transport="persistent_external_process",build=info.get("build")); _PROCS[root]=p; _INFOS[root]=wi; return p

def worker_info(instance_root,start=False):
    root=str(Path(instance_root).resolve())
    if start:
        try:_start(root)
        except Exception as e:return {"available":False,"error":f"{type(e).__name__}: {e}"}
    return dict(_INFOS[root]) if root in _INFOS else probe_worker(root)

def shutdown_worker(instance_root=None):
    roots=list(_PROCS) if instance_root is None else [str(Path(instance_root).resolve())]
    for root in roots:
        with _LOCK:
            p=_PROCS.pop(root,None); _INFOS.pop(root,None)
            if not p: continue
            try:
                if p.poll() is None and p.stdin:
                    p.stdin.write(struct.pack("<IIIIQ",MAGIC_REQ,VERSION,CMD_QUIT,0,0)); p.stdin.flush(); p.wait(timeout=2)
            except Exception:
                try:p.kill()
                except Exception:pass
atexit.register(shutdown_worker)


def biot_savart(instance_root,points,queries,gamma=1.0,core=0.04,*,require_fp64=False,precision="auto"):
    """Run the SYCL Biot--Savart backend.

    precision: auto | fp32 | dd32 | fp64
      dd32 = double-single / FP32x2 (~48 nominal significand bits), NOT IEEE FP64.
    """
    root=Path(instance_root).resolve(); p64=np.ascontiguousarray(points,dtype=np.float64); q64=np.ascontiguousarray(queries,dtype=np.float64)
    if p64.ndim!=2 or p64.shape[1]!=3 or q64.ndim!=2 or q64.shape[1]!=3: raise ValueError("points/queries must be Nx3")
    if core<=0: raise ValueError("core must be > 0")
    if precision not in {"auto","fp32","dd32","fp64"}: raise ValueError("precision must be auto|fp32|dd32|fp64")
    proc=_start(root); info=worker_info(root); native64=bool(info.get("fp64",False))
    if require_fp64: precision="fp64"
    if precision=="auto": precision="fp64" if native64 else "fp32"
    if precision=="fp64" and not native64: raise RuntimeError("SYCL device has no native FP64")
    if precision=="fp32" and os.environ.get("SST_SYCL_ALLOW_FP32","0")!="1": raise RuntimeError("FP32 SYCL is screening only; set SST_SYCL_ALLOW_FP32=1 explicitly")

    if precision=="fp32":
        pp=np.ascontiguousarray(p64,dtype=np.float32); qq=np.ascontiguousarray(q64,dtype=np.float32); cmd=CMD_BIOT_F32; in_dtype=np.float32
    elif precision=="fp64":
        pp=p64; qq=q64; cmd=CMD_BIOT_F64; in_dtype=np.float64
    else:  # DD32 keeps FP64 transport until worker-host hi/lo split.
        pp=p64; qq=q64; cmd=CMD_BIOT_DD32; in_dtype=np.float64

    request_id=time.monotonic_ns() & ((1<<64)-1)
    hdr=struct.pack("<IIIIQQQdd",MAGIC_REQ,VERSION,cmd,0,request_id,pp.shape[0],qq.shape[0],float(gamma),float(core))
    t0=time.perf_counter()
    with _LOCK:
        proc.stdin.write(hdr); proc.stdin.write(pp.tobytes()); proc.stdin.write(qq.tobytes()); proc.stdin.flush()
        rh=_read_exact(proc.stdout,40)
        magic,ver,status,dtype_code,rid,nbytes,kernel_ns=struct.unpack("<IIIIQQQ",rh)
        if magic!=MAGIC_RES or ver!=VERSION or rid!=request_id: raise RuntimeError("bad SYCL worker response header")
        payload=_read_exact(proc.stdout,nbytes)
        if status!=0: raise RuntimeError(payload.decode("utf-8","replace"))
    wall_ms=(time.perf_counter()-t0)*1000.0

    if dtype_code==1: out_dtype=np.float32
    elif dtype_code in {2,3}: out_dtype=np.float64
    else: raise RuntimeError(f"unknown SYCL response dtype code {dtype_code}")
    arr=np.frombuffer(payload,dtype=out_dtype).reshape((-1,3)).astype(np.float64,copy=False)
    if precision=="fp64": label="sycl-worker-fp64"; pclass="float64"; authority="CERTIFICATION"
    elif precision=="dd32": label="sycl-worker-dd32"; pclass="dd32-fp32x2"; authority="SCREENING_ONLY"
    else: label="sycl-worker-fp32"; pclass="float32"; authority="SCREENING_ONLY"
    br=info.get("build") or {}
    metrics={"kernel_device_ms":kernel_ns/1e6,"end_to_end_ms":wall_ms,"is_gpu":bool(info.get("is_gpu")),"native_fp64":native64,"precision_mode":precision}
    if precision=="dd32": metrics.update({"ieee_fp64":False,"nominal_significand_bits":48,"exponent_range":"binary32","transport":"fp64-host-to-fp32x2-device-to-fp64-host"})
    result=BackendResult("sycl",label,pclass,authority,bool(np.isfinite(arr).all()),metrics,sha256_file(_src(root)),br.get("fingerprint_sha256"),info.get("device_name"))
    return arr,result
