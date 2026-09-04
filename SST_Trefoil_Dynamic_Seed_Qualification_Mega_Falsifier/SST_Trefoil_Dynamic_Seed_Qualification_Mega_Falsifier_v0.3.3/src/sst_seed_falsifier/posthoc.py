"""Read-only post-hoc S37B diagnostic for an existing v0.3.0 public campaign.

This is intentionally *not* a replacement for a prospective v0.3.1 run.  It exists so
an already completed v0.3.0 campaign can be used to diagnose the S37 failure without
re-running S20-S35.  It never reads sealed identities and never promotes to S40.
"""
from __future__ import annotations
import argparse, hashlib
from pathlib import Path
import numpy as np
from .io import load_json,dump_json,geom_sha
from .evidence import file_sha256,object_sha256
from .mesh_closure import run_resolution,classify_resolution_ladder


def run(source,dest,cfg):
    source=Path(source).resolve(); dest=Path(dest).resolve()
    if dest.exists() and any(dest.iterdir()): raise FileExistsError('REFUSING_TO_OVERWRITE_POSTHOC_DIAGNOSTIC')
    dest.mkdir(parents=True,exist_ok=True)
    manifest=load_json(source/'public_manifest.json')
    public={r['candidate_id']:r for r in manifest.get('candidates',[])}
    core=load_json(source/'stage35_core_robustness'/'results.json')
    ids=[r['candidate_id'] for r in core if bool(r.get('qualified',False))]
    if not ids: raise ValueError('NO_S35_CORE_QUALIFIED_CANDIDATES_IN_SOURCE')
    ladder=[int(n) for n in cfg.get('mesh_closure_resolution_ladder',[64,96,128,192])]
    T=float(cfg.get('mesh_closure_t_final',1.2)); rows=[]; att=[]
    for cid in ids:
        gp=source/'geometries'/f'{cid}.npy'
        x=np.load(gp); gh=geom_sha(x)
        if cid not in public or gh!=public[cid].get('geom_sha'): raise ValueError(f'SOURCE_GEOMETRY_COMMITMENT_MISMATCH:{cid}')
        per=[run_resolution(x,cfg,n,T) for n in ladder]
        rows.append({'candidate_id':cid,'source_group_id':public[cid].get('source_group_id','G_UNKNOWN'),
                     'resolution_ladder':per,'closure':classify_resolution_ladder(per,cfg),
                     'diagnostic_only':True,'promotion_to_s40_allowed':False})
        att.append({'candidate_id':cid,'geometry_file_sha256':file_sha256(gp),'geometry_commitment':gh})
    source_files={}
    for rel in ('public_manifest.json','stage35_core_robustness/results.json','stage35_core_robustness/summary.json','stage37_mesh_gauge/results.json','stage37_mesh_gauge/summary.json','BLIND_CHAIN_SUMMARY.json','EVIDENCE_MANIFEST.json'):
        p=source/rel
        if p.exists(): source_files[rel]=file_sha256(p)
    counts={}
    for r in rows: counts[r['closure']['status']]=counts.get(r['closure']['status'],0)+1
    report={
        'format':'SST-TREFOIL-V031-POSTHOC-S37B-1','provenance_mode':'POSTHOC_DIAGNOSTIC_NOT_PREREGISTERED',
        'source_campaign':str(source),'source_public_file_sha256':source_files,'source_candidate_attestation':att,
        'source_candidate_attestation_sha256':object_sha256(att),'resolution_ladder':ladder,'target_t_final':T,
        'n_tested':len(rows),'status_counts':counts,'diagnostic_only':True,'promotion_to_s40_allowed':False,
        'physics_verdict':'INDETERMINATE','warning':'Post-hoc diagnostic only; cannot retroactively certify S37A or authorize S40.',
    }
    dump_json(dest/'results.json',rows); dump_json(dest/'summary.json',report)
    return report


def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('source_campaign'); ap.add_argument('dest'); ap.add_argument('config')
    a=ap.parse_args(argv); cfg=load_json(a.config); r=run(a.source_campaign,a.dest,cfg); print(r); return 0

if __name__=='__main__': raise SystemExit(main())
