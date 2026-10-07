from __future__ import annotations
from pathlib import Path
import hashlib, json, os, platform, subprocess, sys

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path: str | Path) -> str:
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20), b""):
            h.update(block)
    return h.hexdigest()

def canonical_json_bytes(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",",":"), ensure_ascii=False)+"\n").encode("utf-8")

def canonical_json_sha256(obj) -> str:
    return sha256_bytes(canonical_json_bytes(obj))

def write_json(path: str | Path, obj) -> None:
    p=Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, sort_keys=True)+"\n", encoding="utf-8")

def environment_record() -> dict:
    return {"python":sys.version,"platform":platform.platform(),"executable":sys.executable,
            "cwd":os.getcwd(),"omp_num_threads":os.environ.get("OMP_NUM_THREADS"),
            "sst_backend":os.environ.get("SST_BACKEND")}
