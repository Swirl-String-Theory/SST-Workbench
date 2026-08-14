from __future__ import annotations
import hashlib, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HASH_FILE = ROOT / ".native_build_hash"


def digest() -> str:
    h=hashlib.sha256()
    for p in [ROOT/"cpp"/"native.cpp", ROOT/"setup.py"]:
        h.update(p.read_bytes())
    h.update(sys.version.encode())
    return h.hexdigest()


def built_module_exists() -> bool:
    return any((ROOT/"sst_einstein").glob("_native*.pyd")) or any((ROOT/"sst_einstein").glob("_native*.so"))


def build(force: bool=False) -> None:
    d=digest()
    if not force and built_module_exists() and HASH_FILE.exists() and HASH_FILE.read_text().strip()==d:
        print("[native] hash unchanged; build skipped")
        return
    env=os.environ.copy()
    cmd=[sys.executable,"setup.py","build_ext","--inplace"]
    print("[native] building C++17/pybind11 backend; OpenMP=",env.get("SST_OPENMP","1"))
    try:
        subprocess.run(cmd,cwd=ROOT,env=env,check=True)
    except subprocess.CalledProcessError:
        if env.get("SST_OPENMP","1") not in {"0","false","False"}:
            print("[native] OpenMP build failed; retrying without OpenMP")
            env["SST_OPENMP"]="0"
            subprocess.run(cmd,cwd=ROOT,env=env,check=True)
        else:
            raise
    HASH_FILE.write_text(d+"\n")
    print("[native] build complete")

if __name__=="__main__":
    build(force="--force" in sys.argv)
