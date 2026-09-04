from __future__ import annotations
from pathlib import Path
import math
import numpy as np

def parse_xyz(path: str | Path)->list[np.ndarray]:
    path=Path(path); comps=[]; cur=[]
    for ln,raw in enumerate(path.read_text(encoding='utf-8-sig',errors='replace').splitlines(),1):
        s=raw.strip()
        if not s:
            if cur: comps.append(np.asarray(cur,float)); cur=[]
            continue
        if s.startswith('#'): continue
        f=s.replace(',',' ').split()
        if len(f)<3: raise ValueError(f'{path}:{ln}: expected x y z')
        p=[float(f[0]),float(f[1]),float(f[2])]
        if not all(math.isfinite(v) for v in p): raise ValueError(f'{path}:{ln}: nonfinite coordinate')
        cur.append(p)
    if cur: comps.append(np.asarray(cur,float))
    if not comps: raise ValueError(f'{path}: no coordinates')
    return comps

def write_xyz(path: str | Path,components:list[np.ndarray])->None:
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    blocks=[]
    for c in components:
        blocks.append('\n'.join(f'{x:.17g} {y:.17g} {z:.17g}' for x,y,z in np.asarray(c)))
    p.write_text('\n\n'.join(blocks)+'\n',encoding='utf-8')

def write_vect(path: str | Path,components:list[np.ndarray])->None:
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    comps=[np.asarray(c,float) for c in components]
    colors=[(0.20,0.65,1.00,1.0),(1.00,0.45,0.25,1.0),(0.35,0.85,0.45,1.0),(0.80,0.45,1.00,1.0)]
    lines=['VECT',f'{len(comps)} {sum(len(c) for c in comps)} {len(comps)}',
           ' '.join(str(-len(c)) for c in comps),
           ' '.join('1' for _ in comps)]
    for c in comps:
        lines.extend(f'{x:.17g} {y:.17g} {z:.17g}' for x,y,z in c)
    for i in range(len(comps)):
        lines.append(' '.join(str(v) for v in colors[i%len(colors)]))
    p.write_text('\n'.join(lines)+'\n',encoding='utf-8')

def parse_vect(path: str | Path)->list[np.ndarray]:
    toks=[]
    for raw in Path(path).read_text(encoding='utf-8-sig',errors='replace').splitlines():
        s=raw.strip()
        if s and not s.startswith('#'): toks.extend(s.split())
    if not toks or toks[0].upper()!='VECT': raise ValueError('not a VECT file')
    k=1; nc=int(toks[k]); nv=int(toks[k+1]); ncol=int(toks[k+2]); k+=3
    counts=[int(toks[k+i]) for i in range(nc)]; k+=nc
    k+=nc # color counts
    pts=np.asarray([float(toks[k+i]) for i in range(3*nv)],float).reshape(nv,3)
    out=[]; pos=0
    for count in counts:
        n=abs(count); out.append(pts[pos:pos+n].copy()); pos+=n
    return out
