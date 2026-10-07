from __future__ import annotations
from pathlib import Path
import atexit,json,os,platform,shutil,struct,subprocess,tempfile,threading,time
import numpy as np
from .backend_contract import BackendResult
from .util import sha256_file,canonical_json_sha256,write_json

MAGIC_REQ=0x32545353; MAGIC_RES=0x32525353; VERSION=2
CMD_BIOT_F32=2; CMD_BIOT_F64=3; CMD_QUIT=9
_LOCK=threading.RLock(); _PROCS={}; _INFOS={}; _ONEAPI_ENV_CACHE=None


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
        if "=" not in line or line.startswith("="):
            continue
        k,v=line.split("=",1)
        if k:
            env[k]=v
    return env

def _oneapi_env_script(cxx=None):
    """Locate the Intel oneAPI environment script on Windows.

    Supports both the classic component layout (setvars.bat) and the newer
    unified versioned layout (oneapi-vars.bat).
    """
    if platform.system().lower()!="windows": return None
    candidates=[]
    for key in ("ONEAPI_ROOT","ONEAPI_ROOT_DIR"):
        if os.environ.get(key):
            r=Path(os.environ[key])
            candidates += [r/"setvars.bat", r/"oneapi-vars.bat"]
    if cxx:
        try:
            cp=Path(cxx).resolve()
            for a in [cp.parent,*cp.parents]:
                if a.name.lower()=="oneapi":
                    candidates.append(a/"setvars.bat")
                    for x in a.glob("*/oneapi-vars.bat"):
                        candidates.append(x)
                    break
                if (a/"oneapi-vars.bat").exists():
                    candidates.append(a/"oneapi-vars.bat")
        except Exception: pass
    roots=[Path(r"C:\Program Files (x86)\Intel\oneAPI"),Path(r"C:\Program Files\Intel\oneAPI")]
    for r in roots:
        candidates.append(r/"setvars.bat")
        if r.exists():
            # Prefer newest version textually; exact version choice is still controlled
            # by ICPX/CXX when the caller supplied one.
            candidates += sorted(r.glob("*/oneapi-vars.bat"),reverse=True)
    seen=set()
    for p in candidates:
        q=str(p).lower()
        if q in seen: continue
        seen.add(q)
        if p.exists(): return p
    return None

def _with_oneapi_environment(cxx, base_env=None):
    """Return an environment with Intel compiler/linker variables initialized.

    Merely finding icpx.exe is insufficient on Windows: link.exe also needs the
    Intel LIB/PATH entries (e.g. the directory containing libmmd.lib).
    """
    env=dict(base_env or os.environ)
    if platform.system().lower()!="windows": return env,None
    # If the current shell is already initialized and contains libmmd.lib, keep it.
    for d in env.get("LIB","").split(";"):
        if d and (Path(d)/"libmmd.lib").exists(): return env,"existing-environment"
    script=_oneapi_env_script(cxx)
    if not script: return env,None
    # CALL setvars via a temporary wrapper .cmd.  Passing
    #   cmd /c call "C:\Program Files\...\setvars.bat" && set
    # as a single argv gets re-quoted by Windows list2cmdline and breaks on
    # spaces, leaving LIB unset (LNK1104 cannot open libmmd.lib).
    try:
        with tempfile.TemporaryDirectory(prefix="sst_oneapi_env_") as td:
            wrapper=Path(td)/"load_oneapi_env.cmd"
            wrapper.write_text(
                "@echo off\r\n"
                f'call "{script}" >nul\r\n'
                "if errorlevel 1 exit /b 1\r\n"
                "set\r\n",
                encoding="utf-8",
            )
            cp=subprocess.run(["cmd.exe","/d","/c",str(wrapper)],text=True,capture_output=True,env=env,timeout=120)
        if cp.returncode==0:
            newenv=_parse_cmd_environment(cp.stdout)
            if newenv:
                env.update(newenv)
                return env,str(script)
    except Exception: pass
    return env,str(script)


def _runtime_env(cxx=None):
    """Environment for building and launching the SYCL worker on Windows.

    The linked binary needs Intel runtime DLLs (and LIB during link).  Cache the
    imported oneAPI environment so probe/start do not re-run setvars each call.
    """
    global _ONEAPI_ENV_CACHE
    with _LOCK:
        if _ONEAPI_ENV_CACHE is None:
            env,_=_with_oneapi_environment(cxx or _icpx())
            _ONEAPI_ENV_CACHE=dict(env)
        out=dict(_ONEAPI_ENV_CACHE)
    out.setdefault("SYCL_CACHE_PERSISTENT","0")
    return out

def build_worker(instance_root,*,force=False,verbose=True):
    root=Path(instance_root).resolve(); src=_src(root); exe=_exe(root); exe.parent.mkdir(exist_ok=True); cxx=_icpx()
    if not cxx: return {"success":False,"error":"icpx not found"}
    try:
        ver=subprocess.run([cxx,"--version"],text=True,capture_output=True,timeout=8); cv=(ver.stdout or ver.stderr).splitlines()[0]
    except Exception: cv=None
    flags=["-fsycl","-fsycl-device-code-split=per_kernel","-O3","-std=c++17"]
    fp=canonical_json_sha256({"source_sha256":sha256_file(src),"compiler":cxx,"compiler_version":cv,"flags":flags,"protocol":VERSION})
    stamp=exe.parent/"SYCL_WORKER_BUILD.json"
    if not force and exe.exists() and stamp.exists():
        try:
            old=json.loads(stamp.read_text(encoding="utf-8"))
            if old.get("fingerprint_sha256")==fp: return {**old,"success":True}
        except Exception: pass
    if force: exe.unlink(missing_ok=True)
    build_env=_runtime_env(cxx)
    env_script=_oneapi_env_script(cxx) if platform.system().lower()=="windows" else None
    cp=subprocess.run([cxx,*flags,str(src),"-o",str(exe)],cwd=str(root),env=build_env,text=True,capture_output=True)
    if cp.returncode!=0 or not exe.exists():
        return {"success":False,"fingerprint_sha256":fp,"compiler":cxx,"compiler_version":cv,"flags":flags,"oneapi_env_script":str(env_script) if env_script else None,"lib":build_env.get("LIB"),"error":(cp.stdout+"\n"+cp.stderr)[-10000:]}
    d={"success":True,"artifact":str(exe),"fingerprint_sha256":fp,"compiler":cxx,"compiler_version":cv,"flags":flags,"oneapi_env_script":str(env_script) if env_script else None}; write_json(stamp,d); return d

def probe_worker(instance_root,*,force_build=False):
    root=Path(instance_root).resolve(); b=build_worker(root,force=force_build,verbose=False)
    if not b.get("success"): return {"available":False,"build":b}
    env=_runtime_env()
    try:
        cp=subprocess.run([str(_exe(root)),"--probe"],cwd=str(root),env=env,text=True,capture_output=True,timeout=30)
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
        env=_runtime_env()
        p=subprocess.Popen([str(_exe(root))],cwd=root,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0)
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
            p=_PROCS.pop(root,None)
            if not p: continue
            try:
                if p.poll() is None and p.stdin:
                    p.stdin.write(struct.pack("<IIIIQ",MAGIC_REQ,VERSION,CMD_QUIT,0,0)); p.stdin.flush(); p.wait(timeout=2)
            except Exception:
                try:p.kill()
                except Exception:pass
atexit.register(shutdown_worker)

def biot_savart(instance_root,points,queries,gamma=1.0,core=0.04,*,require_fp64=False):
    root=Path(instance_root).resolve(); p64=np.ascontiguousarray(points,dtype=np.float64); q64=np.ascontiguousarray(queries,dtype=np.float64)
    if p64.ndim!=2 or p64.shape[1]!=3 or q64.ndim!=2 or q64.shape[1]!=3: raise ValueError("points/queries must be Nx3")
    if core<=0: raise ValueError("core must be > 0")
    proc=_start(root); info=worker_info(root); use64=bool(info.get("fp64",False))
    if require_fp64 and not use64: raise RuntimeError("SYCL device has no native FP64")
    if not use64 and os.environ.get("SST_SYCL_ALLOW_FP32","0")!="1": raise RuntimeError("FP32 SYCL is screening only; set SST_SYCL_ALLOW_FP32=1 explicitly")
    dtype=np.float64 if use64 else np.float32; cmd=CMD_BIOT_F64 if use64 else CMD_BIOT_F32
    pp=np.ascontiguousarray(p64,dtype=dtype); qq=np.ascontiguousarray(q64,dtype=dtype); request_id=time.monotonic_ns() & ((1<<64)-1)
    hdr=struct.pack("<IIIIQQQdd",MAGIC_REQ,VERSION,cmd,0,request_id,pp.shape[0],qq.shape[0],float(gamma),float(core))
    t0=time.perf_counter()
    with _LOCK:
        proc.stdin.write(hdr); proc.stdin.write(pp.tobytes()); proc.stdin.write(qq.tobytes()); proc.stdin.flush()
        rh=_read_exact(proc.stdout,40)
        magic,ver,status,dtype_code,rid,nbytes,kernel_ns=struct.unpack("<IIIIQQQ",rh)
        if magic!=MAGIC_RES or ver!=VERSION or rid!=request_id: raise RuntimeError("bad SYCL worker response header")
        payload=_read_exact(proc.stdout,nbytes)
        if status!=0: raise RuntimeError(payload.decode("utf-8","replace"))
    wall_ms=(time.perf_counter()-t0)*1000.0; arr=np.frombuffer(payload,dtype=dtype).reshape((-1,3)).astype(np.float64,copy=False)
    label="sycl-worker-fp64" if use64 else "sycl-worker-fp32"; authority="CERTIFICATION" if use64 else "SCREENING_ONLY"
    br=info.get("build") or {}
    result=BackendResult("sycl",label,"float64" if use64 else "float32",authority,bool(np.isfinite(arr).all()),{"kernel_device_ms":kernel_ns/1e6,"end_to_end_ms":wall_ms,"is_gpu":bool(info.get("is_gpu")),"fp64":use64},sha256_file(_src(root)),br.get("fingerprint_sha256"),info.get("device_name"))
    return arr,result
