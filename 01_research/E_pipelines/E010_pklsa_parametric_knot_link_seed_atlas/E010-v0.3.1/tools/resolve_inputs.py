from __future__ import annotations
from pathlib import Path
import argparse, json, os


def first_existing(items):
    for p in items:
        if p and Path(p).exists(): return str(Path(p).resolve())
    return None


def find_base_in_repo(root: Path):
    names=('SST_Parametric_Knot_Link_Seed_Atlas_v0.2.0.zip','SST_Parametric_Knot_Link_Seed_Atlas_v0.2.0')
    # Prefer shallow, deterministic matches; avoid environments and output trees.
    hits=[]
    for p in root.rglob('SST_Parametric_Knot_Link_Seed_Atlas_v0.2.0*'):
        if p.name not in names: continue
        low={x.lower() for x in p.parts}
        if '.venv' in low or 'site-packages' in low or '__pycache__' in low: continue
        try: depth=len(p.relative_to(root).parts)
        except Exception: depth=999
        hits.append((depth,0 if p.suffix.lower()=='.zip' else 1,str(p),p))
    return str(sorted(hits)[0][-1].resolve()) if hits else None

ap=argparse.ArgumentParser()
ap.add_argument('--builder-root',required=True); ap.add_argument('--workbench-root'); ap.add_argument('--base')
a=ap.parse_args(); br=Path(a.builder_root).resolve()
wb=first_existing([a.workbench_root, os.environ.get('SST_WORKBENCH'), br.parent])
base_candidates=[a.base,os.environ.get('PKLSA_V020')]
if wb:
    w=Path(wb)
    base_candidates += [
        w/'SST_Parametric_Knot_Link_Seed_Atlas_v0.2.0.zip',
        w/'SST_Parametric_Knot_Link_Seed_Atlas_v0.2.0',
        w/'Knot_Library'/'SST_Parametric_Knot_Link_Seed_Atlas_v0.2.0.zip',
        w/'Knot_Library'/'SST_Parametric_Knot_Link_Seed_Atlas_v0.2.0',
    ]
base=first_existing(base_candidates)
if not base and wb:
    base=find_base_in_repo(Path(wb))
print(json.dumps({'workbench_root':wb,'base_v020':base},ensure_ascii=False))
if not wb or not base: raise SystemExit(3)
