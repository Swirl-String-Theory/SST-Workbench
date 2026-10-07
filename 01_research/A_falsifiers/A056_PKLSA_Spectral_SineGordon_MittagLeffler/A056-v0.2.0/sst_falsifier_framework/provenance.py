from __future__ import annotations
from pathlib import Path
import hashlib, json, os, platform, sys, subprocess

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def tree_manifest(root, exclude_parts=(".venv","build","__pycache__",".pytest_cache")):
    root=Path(root); rows=[]
    for p in sorted(root.rglob("*")):
        if not p.is_file() or any(x in exclude_parts for x in p.parts): continue
        rows.append({"path":p.relative_to(root).as_posix(),"bytes":p.stat().st_size,"sha256":sha256_file(p)})
    return rows

def write_manifest(root,out):
    rows=tree_manifest(root)
    Path(out).write_text(json.dumps({"schema":"SST-FILE-MANIFEST-1","files":rows},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return rows

def environment_snapshot():
    return {
      "python":sys.version.replace("\n"," "),"platform":platform.platform(),"machine":platform.machine(),
      "processor":platform.processor(),"executable":sys.executable,
      "omp_num_threads":os.environ.get("OMP_NUM_THREADS"),
      "oneapi_device_selector":os.environ.get("ONEAPI_DEVICE_SELECTOR"),
      "sycl_cache_persistent":os.environ.get("SYCL_CACHE_PERSISTENT"),
    }
