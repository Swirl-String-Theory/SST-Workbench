from __future__ import annotations
from pathlib import Path
from typing import Iterable
from .util import sha256_file, canonical_json_sha256, write_json

GENERATED_PARTS={"__pycache__",".pytest_cache","build",".venv"}
BINARY_SUFFIXES={".pyd",".dll",".exe",".lib",".exp",".obj",".pyc",".so",".dylib",".a",".o"}


def inventory(root: str|Path, *, exclude_parts: set[str]|None=None, max_files: int=200000):
    root=Path(root); rows=[]; excluded=GENERATED_PARTS | (exclude_parts or set())
    if not root.exists(): return rows
    for p in sorted(root.rglob("*")):
        if not p.is_file(): continue
        rel=p.relative_to(root)
        if any(part in excluded for part in rel.parts): continue
        rows.append({"relpath":rel.as_posix(),"size":p.stat().st_size,"sha256":sha256_file(p)})
        if len(rows)>=max_files: raise RuntimeError("inventory max_files exceeded")
    return rows


def make_manifest(root: str|Path, out_path: str|Path, *, schema="SST-FILE-MANIFEST-2"):
    files=inventory(root)
    core={"schema":schema,"root":str(Path(root).resolve()),"files":files}
    core["manifest_sha256"]=canonical_json_sha256({"schema":schema,"files":files})
    write_json(out_path,core); return core


def find_release_contamination(root: str|Path):
    root=Path(root); hits=[]
    for p in root.rglob("*"):
        rel=p.relative_to(root)
        if any(part in {"__pycache__",".pytest_cache",".venv","build"} or part.endswith("-outputs") for part in rel.parts):
            hits.append(rel.as_posix()); continue
        if p.is_file() and p.suffix.lower() in BINARY_SUFFIXES:
            hits.append(rel.as_posix())
    return sorted(set(hits))
