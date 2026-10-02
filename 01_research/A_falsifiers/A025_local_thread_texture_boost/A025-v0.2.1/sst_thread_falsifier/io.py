from __future__ import annotations
import json, re
from pathlib import Path
import numpy as np

SUPPORTED={".txt",".xyz",".dat",".csv",".vect",".json"}
_FLOAT_RE=re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _parse_text(path):
    text=Path(path).read_text(encoding="utf-8",errors="ignore")
    if text.lstrip().startswith("VECT") or path.suffix.lower()==".vect":
        return _parse_vect(text)
    comps=[]; cur=[]
    for line in text.splitlines():
        s=line.strip()
        if not s:
            if len(cur)>=3: comps.append(np.asarray(cur,float)); cur=[]
            continue
        if s.startswith(("#",";","//")): continue
        vals=[float(x) for x in _FLOAT_RE.findall(s)]
        if len(vals)>=3:
            cur.append(vals[:3])
    if len(cur)>=3: comps.append(np.asarray(cur,float))
    if not comps: raise ValueError("no XYZ components found")
    return comps


def _parse_vect(text):
    lines=[ln.strip() for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    if not lines or lines[0].upper()!="VECT":
        raise ValueError("not VECT")
    hdr=[int(float(x)) for x in _FLOAT_RE.findall(lines[1])]
    if len(hdr)<2: raise ValueError("bad VECT header")
    ncomp,nvert=hdr[0],hdr[1]
    counts=[int(float(x)) for x in _FLOAT_RE.findall(lines[2])]
    if len(counts)<ncomp: raise ValueError("bad VECT component counts")
    counts=[abs(x) for x in counts[:ncomp]]
    vals=[]
    for ln in lines[4:]:
        x=[float(z) for z in _FLOAT_RE.findall(ln)]
        if len(x)>=3: vals.append(x[:3])
        if len(vals)>=nvert: break
    if len(vals)<sum(counts): raise ValueError("VECT has too few vertices")
    P=np.asarray(vals,float)
    out=[]; k=0
    for n in counts:
        out.append(P[k:k+n]); k+=n
    return out


def _parse_json(path):
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(obj,list):
        a=np.asarray(obj,float)
        if a.ndim==2 and a.shape[1]>=3: return [a[:,:3]]
        if a.ndim==3 and a.shape[2]>=3: return [np.asarray(x)[:,:3] for x in a]
    for key in ("components","curves"):
        if key in obj:
            return [np.asarray(x,float)[:,:3] for x in obj[key]]
    for key in ("points","xyz","centerline"):
        if key in obj:
            return [np.asarray(obj[key],float)[:,:3]]
    raise ValueError("unsupported JSON geometry schema")


def load_components(path):
    path=Path(path)
    return _parse_json(path) if path.suffix.lower()==".json" else _parse_text(path)


def discover_dataset(root, max_files=0):
    root=Path(root)
    if not root.exists(): raise FileNotFoundError(root)
    files=[]
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix.lower() in SUPPORTED:
            name=p.name.lower()
            if name.endswith(("summary.json","report.json","config.json")): continue
            files.append(p)
            if max_files and len(files)>=max_files: break
    return files
