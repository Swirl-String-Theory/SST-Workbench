from __future__ import annotations
from pathlib import Path
import json,hashlib
def read_json(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def write_json(p,obj):
 p=Path(p); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
def sha256_file(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""): h.update(b)
 return h.hexdigest()
