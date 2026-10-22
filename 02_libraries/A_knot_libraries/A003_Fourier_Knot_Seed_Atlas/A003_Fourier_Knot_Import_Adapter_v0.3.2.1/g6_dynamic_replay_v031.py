#!/usr/bin/env python3
"""v0.3.1 forensic replay of *existing* v0.3.0 initial/final saved polygons.
Never promotes 2 snapshot endpoints as five-snapshot topology certification.
"""
from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from a003_diagnostic_v027 import json_write
from g6_dynamic_qualification_v031 import snapshot_screen,SEEDS

def run_replay(run:Path,out:Path):
    summary=run/'G6_TEMPORAL_SUMMARY.json'
    archive=run/'G6_TEMPORAL_TRAJECTORIES.npz'
    if not summary.is_file() or not archive.is_file():raise FileNotFoundError('both v0.3.0 summary and trajectory NPZ required')
    info=json.loads(summary.read_text(encoding='utf-8'))
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    evidence=info.get('temporal',{}).get('trajectory_npz_sha256')
    if not evidence or evidence!=digest:raise RuntimeError('prior v0.3.0 NPZ SHA does not match signed summary field')
    data=np.load(archive,allow_pickle=False)
    rows=[]
    for sid in SEEDS:
        for n in (150,300,600):
            for stage in ('initial','final'):
                key=f'{sid}_N{n}_{stage}'
                if key not in data:raise RuntimeError('missing v0.3.0 stage '+key)
                r=snapshot_screen(data[key],sid)
                rows.append({'seed':sid,'N':n,'stage':stage,
                   'near_contact':not r['near_segment_clearance']['clear_of_segment_contact'],
                   'nonlocal_min_distance':r['nonlocal_segment_clearance']['min_distance'],
                   'min_full_segment_distance':r['near_segment_clearance']['min_distance'],
                   'diagram_determinants':[d['determinant'] for d in r['diagrams']],
                   'diagram_statuses':[d['comparison'] for d in r['diagrams']]})
    result={'schema':'sst.a003.g6.v030-endpoint-replay/1','source_version':'0.3.0',
      'source_trajectory_sha256':digest,'source_summary_sha256':hashlib.sha256(summary.read_bytes()).hexdigest(),
      'status':'PASS_ENDPOINT_DIAGNOSTIC_ONLY' if all(not x['near_contact'] and all(v=='PASS_DIAGRAM_DETERMINANT' for v in x['diagram_statuses']) for x in rows) else 'FAIL_OR_UNRESOLVED_ENDPOINT_DIAGNOSTIC',
      'records':rows,'count':len(rows),
      'not_five_snapshots':True,'not_a_new_finite_core_run':True,'continuous_topology_certified':False}
    out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():raise FileExistsError(out)
    json_write(out,result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--v030-run',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    x=p.parse_args();res=run_replay(x.v030_run,x.out)
    print(json.dumps({'status':res['status'],'count':res['count'],'out':str(x.out)},indent=2))
