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

def closure_gap_ratio(x):
    x=np.asarray(x,float)
    internal=np.linalg.norm(np.diff(x,axis=0),axis=1)
    scale=float(np.median(internal)) if len(internal) else 0.0
    return float(np.linalg.norm(x[0]-x[-1])/max(scale,1e-15))

def component_gap_ratio(x):
    internal=np.linalg.norm(np.diff(np.asarray(x,float),axis=0),axis=1)
    return float(np.max(internal)/max(float(np.median(internal)),1e-15)) if len(internal) else float('inf')

def discover_sources(root,regex,extensions,match_mode='fullmatch',reject_name_prefixes=('link_',),require_closed=True,closure_gap_ratio_max=3.0,component_gap_ratio_max=5.0):
    pat=re.compile(regex,re.I); ex={e.lower() for e in extensions}; out=[]
    for p in Path(root).rglob('*'):
        if not p.is_file() or p.suffix.lower() not in ex: continue
        stem=p.stem
        if any(stem.lower().startswith(str(prefix).lower()) for prefix in reject_name_prefixes): continue
        matched=pat.fullmatch(stem) if str(match_mode).lower()=='fullmatch' else pat.search(p.name)
        if not matched: continue
        try:
            x=read_xyz(p)
            if require_closed and closure_gap_ratio(x)>float(closure_gap_ratio_max): continue
            if component_gap_ratio(x)>float(component_gap_ratio_max): continue
            out.append((p,x))
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
