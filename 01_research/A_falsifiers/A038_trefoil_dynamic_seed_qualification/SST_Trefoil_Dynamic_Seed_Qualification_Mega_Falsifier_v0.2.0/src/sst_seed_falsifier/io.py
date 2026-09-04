from pathlib import Path
import numpy as np, re, json, hashlib

def read_xyz(path):
    rows=[]
    for line in Path(path).read_text(encoding='utf-8',errors='ignore').splitlines():
        s=line.strip().replace(',',' ')
        if not s or s.startswith(('#',';','//')): continue
        parts=s.split()
        vals=[]
        for p in parts:
            try: vals.append(float(p))
            except Exception: pass
        if len(vals)>=3: rows.append(vals[:3])
    x=np.asarray(rows,float)
    if x.ndim!=2 or x.shape[1]!=3 or len(x)<16: raise ValueError(f'not a usable XYZ curve: {path}')
    if np.linalg.norm(x[0]-x[-1])<1e-10: x=x[:-1]
    return x

def discover_sources(root,regex,extensions):
    pat=re.compile(regex,re.I); ex={e.lower() for e in extensions}; out=[]
    for p in Path(root).rglob('*'):
        if p.is_file() and p.suffix.lower() in ex and pat.search(p.name):
            try:
                x=read_xyz(p); out.append((p,x))
            except Exception: pass
    out.sort(key=lambda z:str(z[0]).lower())
    return out

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def geom_sha(x,decimals=12): return hashlib.sha256(np.round(np.asarray(x,float),decimals).tobytes()).hexdigest()
def _clean_json(x):
    import math
    if isinstance(x,float) and not math.isfinite(x): return None
    if isinstance(x,dict): return {k:_clean_json(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [_clean_json(v) for v in x]
    return x
def dump_json(path,obj):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(_clean_json(obj),indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
def load_json(path): return json.loads(Path(path).read_text(encoding='utf-8'))
