from __future__ import annotations
from pathlib import Path
import hashlib,json,secrets,shutil
import numpy as np
from .geometry import read_xyz,resample_closed

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def prepare(input_dir,out_dir,pattern,n_points):
    inp=Path(input_dir); out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    priv=out.parent/'private_reveal'; priv.mkdir(parents=True,exist_ok=True)
    files=sorted(inp.rglob(pattern))
    if not files:
        cps = {}
        for q in inp.rglob("*_i*.txt"):
            import re
            m = re.search(r"_i(\d+)\.txt$", q.name)
            if m: cps[m.group(1)] = cps.get(m.group(1), 0) + 1
        detail = ", ".join(f"i{k}={v}" for k,v in sorted(cps.items())) or "no *_i*.txt checkpoints"
        raise FileNotFoundError(f"no files matching {pattern} under {inp}; available: {detail}")
    salt=secrets.token_hex(16); items=[]
    for p in files:
        x=resample_closed(read_xyz(p),n_points)
        geom_hash=sha256_bytes(np.ascontiguousarray(x,dtype='<f8').tobytes())
        blind_hash=sha256_bytes((salt+geom_hash).encode())
        items.append((blind_hash,p,x,geom_hash))
    items.sort(key=lambda q:q[0])
    reveal=[]; public=[]
    for i,(_,p,x,gh) in enumerate(items,1):
        bid=f"B{i:04d}"; np.save(out/f"{bid}.npy",x)
        public.append({"blind_id":bid,"geometry_sha256":gh,"n":len(x)})
        reveal.append({"blind_id":bid,"source":str(p.resolve()),"source_name":p.name,"geometry_sha256":gh})
    (out/'sealed_manifest.json').write_text(json.dumps({"items":public},indent=2),encoding='utf-8')
    rk={"salt":salt,"items":reveal}; rtxt=json.dumps(rk,indent=2)
    (priv/'reveal_key.json').write_text(rtxt,encoding='utf-8')
    (out/'reveal_key_sha256.txt').write_text(sha256_bytes(rtxt.encode())+'\n',encoding='utf-8')
    return len(items)
