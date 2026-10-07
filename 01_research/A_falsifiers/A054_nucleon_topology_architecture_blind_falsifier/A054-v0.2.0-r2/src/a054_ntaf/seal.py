from __future__ import annotations
from pathlib import Path
import hashlib,json

def sha256_file(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def sha256_json_obj(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def seal_files(paths):
    return {str(Path(p).name):sha256_file(Path(p)) for p in paths}
