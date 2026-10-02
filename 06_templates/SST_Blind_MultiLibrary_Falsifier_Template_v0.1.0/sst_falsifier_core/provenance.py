from __future__ import annotations
from pathlib import Path
from .util import sha256_file

def inventory(root: str|Path, patterns=("*",), max_files=200000):
    root=Path(root); rows=[]
    if not root.exists(): return rows
    seen=set()
    for pattern in patterns:
        for p in root.rglob(pattern):
            if not p.is_file() or p in seen: continue
            seen.add(p)
            rows.append({"relpath":p.relative_to(root).as_posix(),"size":p.stat().st_size,"sha256":sha256_file(p)})
            if len(rows)>=max_files: raise RuntimeError("inventory max_files exceeded")
    return rows
