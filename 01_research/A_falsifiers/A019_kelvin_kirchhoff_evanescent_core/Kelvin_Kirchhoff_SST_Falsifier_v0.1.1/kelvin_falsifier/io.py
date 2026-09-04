from __future__ import annotations
import csv, json, hashlib
from pathlib import Path
import numpy as np


def read_components(path: str|Path) -> list[np.ndarray]:
    path=Path(path); comps=[]; cur=[]
    for line in path.read_text(encoding='utf-8',errors='ignore').splitlines():
        s=line.strip()
        if not s:
            if cur:
                comps.append(np.asarray(cur,float)); cur=[]
            continue
        if s.startswith('#'): continue
        p=s.replace(',',' ').split()
        if len(p)<3: continue
        try: cur.append([float(p[0]),float(p[1]),float(p[2])])
        except ValueError: continue
    if cur: comps.append(np.asarray(cur,float))
    comps=[c for c in comps if len(c)>=3]
    if not comps: raise ValueError(f'No XYZ components parsed from {path}')
    return comps


def read_json(path: str|Path, default=None):
    p=Path(path)
    if not p.exists(): return default
    return json.loads(p.read_text(encoding='utf-8'))


def sha256_file(path: str|Path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()


def discover_cases(knots_dir: str|Path, selection: list[str]|None=None):
    kd=Path(knots_dir)
    files=sorted(kd.glob('*_final.txt'))
    if selection:
        wanted=set(selection)
        files=[f for f in files if f.name in wanted or f.stem in wanted]
        missing=[x for x in selection if not any((f.name==x or f.stem==x) for f in files)]
        if missing: raise FileNotFoundError(f'Missing requested datasets in {kd}: {missing}')
    out=[]
    for f in files:
        metrics=read_json(f.with_suffix('.metrics.json'),{}) or {}
        thickness=metrics.get('thickness')
        if thickness is None and metrics.get('length') and metrics.get('ropelength'):
            thickness=float(metrics['length'])/float(metrics['ropelength'])
        out.append({
            'path':str(f.resolve()), 'filename':f.name, 'sha256':sha256_file(f),
            'metrics_path':str(f.with_suffix('.metrics.json').resolve()) if f.with_suffix('.metrics.json').exists() else None,
            'thickness':None if thickness is None else float(thickness),
            'rr_residual':metrics.get('residual'), 'rr_edge_cv':metrics.get('edge_length_cv'),
            'rr_ropelength':metrics.get('ropelength'), 'rr_length':metrics.get('length'),
            'component_count':metrics.get('component_count'), 'vertices_per_component':metrics.get('vertices_per_component'),
        })
    if not out: raise FileNotFoundError(f'No *_final.txt datasets found in {kd}')
    return out


def write_json(path,data):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(data,indent=2,sort_keys=False),encoding='utf-8')


def write_csv(path,rows):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    if not rows: p.write_text('',encoding='utf-8'); return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)
