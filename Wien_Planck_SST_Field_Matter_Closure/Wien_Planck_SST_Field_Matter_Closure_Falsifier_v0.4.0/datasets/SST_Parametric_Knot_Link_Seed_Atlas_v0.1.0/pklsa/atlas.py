from __future__ import annotations
from pathlib import Path
import json, numpy as np
ROOT=Path(__file__).resolve().parents[1]
def catalog(): return json.loads((ROOT/'CATALOG_49.json').read_text(encoding='utf-8'))['entries']
def iter_candidates():
    with (ROOT/'manifests'/'CANDIDATES_FULL.jsonl').open(encoding='utf-8') as f:
        for line in f:
            if line.strip(): yield json.loads(line)
def get(candidate_id:str):
    row=next((r for r in iter_candidates() if r['candidate_id']==candidate_id),None)
    if row is None: raise KeyError(candidate_id)
    fam=row['family'].replace('.','p'); bundle=ROOT/'families'/f"{row['family_index']:02d}_{fam}.npz"
    z=np.load(bundle,allow_pickle=False); return row,z['points'][row['variant_index']].astype(float)
def write_xyz(candidate_id:str,path):
    row,pts=get(candidate_id); path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='\n') as f:
        f.write(f"# PKLSA v0.1.0 candidate={candidate_id} family={row['family']} components={len(pts)}\n")
        for ci,P in enumerate(pts):
            if ci: f.write('\ncomponent\n')
            for x,y,z in P: f.write(f"{x:.17g} {y:.17g} {z:.17g}\n")
    return path
