from pathlib import Path
import csv, hashlib, json
import numpy as np
from .geometry import canonicalize, curvature_torsion, bishop_frame
from .operator import torsional_operator_spectrum

TREFOIL_HASH='ffc31331fccaf10a3171e4ccbf3ec0043e56ff681f85cc8b8149932193d736d1'

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def _load_manifest(root):
    root=Path(root)
    jp=root/'manifests'/'CANDIDATES_FULL.jsonl'
    cp=root/'manifests'/'CANDIDATES_FULL.csv'
    if jp.exists():
        rows=[json.loads(line) for line in jp.read_text(encoding='utf-8').splitlines() if line.strip()]
    elif cp.exists():
        with cp.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    else:
        raise FileNotFoundError('missing CANDIDATES_FULL.jsonl/.csv')
    return rows

def load_trefoil_population(root, strict_hash=True):
    root=Path(root)
    bundle=root/'families'/'14_knot_3p1.npz'
    if not bundle.exists(): raise FileNotFoundError(bundle)
    digest=sha256_file(bundle)
    if strict_hash and digest != TREFOIL_HASH:
        raise ValueError(f'trefoil bundle SHA-256 mismatch: {digest}')
    with np.load(bundle,allow_pickle=False) as z:
        if 'points' not in z.files: raise KeyError('bundle missing points array')
        pts=np.asarray(z['points'],float)
    if pts.shape != (48,1,512,3): raise ValueError(f'unexpected points shape {pts.shape}')
    if not np.all(np.isfinite(pts)): raise ValueError('non-finite PKLSA points')
    rows=_load_manifest(root)
    family_rows=[]
    for r in rows:
        fam=str(r.get('family',r.get('family_name','')))
        cid=str(r.get('canonical_id',r.get('canonical','')))
        findex=str(r.get('family_index',r.get('family_idx','')))
        if fam=='knot_3.1' or cid=='3_1' or findex=='14': family_rows.append(r)
    if len(family_rows) != 48:
        raise ValueError(f'expected 48 trefoil manifest rows, got {len(family_rows)}')
    indices=[]
    for row in family_rows:
        raw=row.get('variant_index')
        if isinstance(raw,bool) or str(raw) not in {str(i) for i in range(48)}:
            raise ValueError('variant_index must be an integer in 0..47')
        if str(row.get('family','knot_3.1')) != 'knot_3.1' or str(row.get('canonical_id','3_1')) != '3_1' or str(row.get('family_index',14)) != '14':
            raise ValueError('inconsistent trefoil manifest labels')
        indices.append(int(raw))
    if sorted(indices) != list(range(48)):
        raise ValueError('require every variant_index 0..47 exactly once')
    return pts[:,0,:,:], digest

def geometry_screen(root, strict_hash=True, n_modes=8):
    pop,digest=load_trefoil_population(root,strict_hash=strict_hash)
    records=[]
    for i,p in enumerate(pop):
        q,L=canonicalize(p,512,1.0)
        kap,tau,ds,_=curvature_torsion(q)
        _,_,_,hol=bishop_frame(q)
        om=torsional_operator_spectrum(kap,tau,ds,n_modes=n_modes)
        records.append({
            'anonymous_index': i,
            'length_over_rms_radius': float(L),
            'kappa_mean': float(np.mean(kap)),
            'kappa_std': float(np.std(kap)),
            'tau_rms': float(np.sqrt(np.mean(tau*tau))),
            'bishop_holonomy_rad': hol,
            'candidate_operator_omega': [float(x) for x in om],
        })
    return {'bundle_sha256':digest,'count':len(records),'records':records,
            'interpretation':'geometry/operator predictions only; not dynamical evidence'}
