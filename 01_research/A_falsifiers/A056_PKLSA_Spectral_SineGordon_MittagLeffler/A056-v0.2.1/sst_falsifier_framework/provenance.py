from __future__ import annotations
from pathlib import Path
import hashlib, json, os, platform, sys, subprocess, shutil


def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()


def _sha256_json(obj) -> str:
    payload=json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def tree_manifest(root, exclude_parts=(".venv","build","__pycache__",".pytest_cache")):
    root=Path(root); rows=[]
    for p in sorted(root.rglob("*")):
        if not p.is_file() or any(x in exclude_parts for x in p.parts):
            continue
        rows.append({"path":p.relative_to(root).as_posix(),"bytes":p.stat().st_size,"sha256":sha256_file(p)})
    return rows


def write_manifest(root,out):
    rows=tree_manifest(root)
    Path(out).write_text(json.dumps({"schema":"SST-FILE-MANIFEST-1","files":rows},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return rows


def environment_snapshot():
    return {
      "python":sys.version.replace("\n"," "),"python_implementation":platform.python_implementation(),
      "python_compiler":platform.python_compiler(),"platform":platform.platform(),"machine":platform.machine(),
      "processor":platform.processor(),"executable":sys.executable,
      "omp_num_threads":os.environ.get("OMP_NUM_THREADS"),
      "oneapi_device_selector":os.environ.get("ONEAPI_DEVICE_SELECTOR"),
      "sycl_cache_persistent":os.environ.get("SYCL_CACHE_PERSISTENT"),
    }


def _run_version(executable: str, args: list[str]) -> dict:
    try:
        r=subprocess.run([executable,*args],text=True,capture_output=True,timeout=10)
        text=(r.stdout+"\n"+r.stderr).strip()
        return {"returncode":r.returncode,"text":text[:12000]}
    except Exception as e:
        return {"returncode":None,"text":"","error":repr(e)}


def resolve_compiler(kind="host"):
    """Resolve the compiler executable that is expected to build this backend.

    Host detection deliberately does not use ``platform.python_compiler()`` as
    the extension compiler fingerprint.  On Windows that string describes the
    Python interpreter build, not necessarily the compiler invoked by setuptools.
    """
    env_candidates=[]
    if kind=="sycl":
        env_candidates += [os.environ.get("DPCPP"),os.environ.get("CXX")]
        names=["icpx","icx","dpcpp"]
    elif os.name=="nt":
        env_candidates += [os.environ.get("CXX"),os.environ.get("CC")]
        names=["cl","clang-cl","clang++","g++"]
    else:
        env_candidates += [os.environ.get("CXX"),os.environ.get("CC")]
        names=["c++","g++","clang++"]
    for c in [x for x in env_candidates if x]+names:
        path=shutil.which(c) if not Path(c).exists() else str(Path(c).resolve())
        if path:
            return str(Path(path).resolve())
    return None


def compiler_probe(kind="host", executable=None):
    exe=executable or resolve_compiler(kind)
    if not exe:
        return {"kind":kind,"available":False,"executable":None,"fingerprint":None}
    name=Path(exe).name.lower()
    attempts=[["/Bv"],["/?"]] if name in {"cl.exe","cl"} else [["--version"],["-v"]]
    version=None
    for args in attempts:
        info=_run_version(exe,args)
        if info.get("text"):
            version={"args":args,**info}; break
    stat=Path(exe).stat() if Path(exe).exists() else None
    payload={
        "kind":kind,"available":True,"executable":str(Path(exe).resolve()),
        "executable_size":stat.st_size if stat else None,
        "executable_mtime_ns":stat.st_mtime_ns if stat else None,
        "version":version,
    }
    # Do not hash large compiler binaries.  The fingerprint binds resolved path,
    # stat metadata and version banner; source/flags are bound in build_fingerprint.
    payload["fingerprint"]=_sha256_json(payload)
    return payload


def build_fingerprint(*, compiler: dict, source_files, flags, python_abi=None, compile_time_identity=None):
    src=[]
    for p in map(Path,source_files):
        src.append({"path":p.as_posix(),"sha256":sha256_file(p)})
    payload={
      "schema":"SST-BUILD-FINGERPRINT-2",
      "compiler":compiler,
      "sources":src,
      "flags":list(flags),
      "python_abi":python_abi or {"version":platform.python_version(),"implementation":platform.python_implementation()},
      "compile_time_identity":compile_time_identity,
    }
    return {**payload,"fingerprint":_sha256_json(payload)}


def load_json_if_exists(path):
    p=Path(path)
    if not p.exists(): return None
    return json.loads(p.read_text(encoding="utf-8"))
