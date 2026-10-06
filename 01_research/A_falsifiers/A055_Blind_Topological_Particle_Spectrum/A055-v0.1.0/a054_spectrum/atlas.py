from __future__ import annotations
from pathlib import Path
from .util import load_json
PAIR={0:2,2:0,1:3,3:1}

def load_atlas(root: Path):
    raw=load_json(root/"data"/"atlas_pd.json")
    out=[]
    for kind in ("knots","links"):
        for x in raw[kind]:
            y=dict(x); y["kind"]="knot" if kind=="knots" else "link"
            out.append(y)
    return out

def validate_pd(rec):
    pd=rec["pd"]; c=rec["crossings"]
    if len(pd)!=c:
        raise ValueError(f'{rec["id"]}: PD crossings mismatch')
    occ={}
    for ci,x in enumerate(pd):
        if len(x)!=4: raise ValueError(f'{rec["id"]}: bad crossing')
        for pi,lbl in enumerate(x):
            occ.setdefault(lbl,[]).append((ci,pi))
    expected=set(range(1,2*c+1))
    if set(occ)!=expected or any(len(v)!=2 for v in occ.values()):
        raise ValueError(f'{rec["id"]}: labels not 1..2c exactly twice')
    return occ

def component_cycles(rec):
    occ=validate_pd(rec)
    pd=rec["pd"]
    edge_partner={}
    for lbl,nodes in occ.items():
        a,b=nodes
        edge_partner[a]=b; edge_partner[b]=a
    visited=set(); cycles=[]
    for ci in range(len(pd)):
        for pi in range(4):
            start=(ci,pi)
            if start in visited: continue
            cur=start; segs=[]; nodes=[]
            while True:
                if cur in visited and cur!=start:
                    raise ValueError(f'{rec["id"]}: malformed degree-2 traversal')
                visited.add(cur); nodes.append(cur)
                across=(cur[0],PAIR[cur[1]])
                visited.add(across)
                segs.append(("cross",cur,across))
                other=edge_partner[across]
                segs.append(("edge",across,other))
                cur=other
                if cur==start: break
            cycles.append(segs)
    return cycles
