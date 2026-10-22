#!/usr/bin/env python3
"""Opt-in independent KnotPlot/Gilbert provider-family dynamics.

Explicit source contracts only. No guessed file names or topology crosswalk.
Coordinates are uncalibrated. This does not classify any geometries as empirical.
"""
from __future__ import annotations
import json, hashlib, math
from pathlib import Path
import numpy as np
from fourier_atlas_adapter import sha256_file


def arclength_resample(x,n):
    arr=np.asarray(x,dtype=float)
    if arr.ndim!=2 or arr.shape[1]!=3 or len(arr)<n or not np.isfinite(arr).all():raise ValueError('invalid 3D source geometry')
    if np.linalg.norm(arr[0]-arr[-1]) < 1e-10*np.linalg.norm(np.ptp(arr,axis=0)):
        arr=arr[:-1]
    edge=np.linalg.norm(np.roll(arr,-1,axis=0)-arr,axis=1)
    if min(edge)<=0:raise ValueError('degenerate source geometry')
    cumulative=np.concatenate([[0.],np.cumsum(edge)])
    xp=np.concatenate([arr,arr[:1]])
    target=np.arange(n)*cumulative[-1]/n
    return np.column_stack([np.interp(target,cumulative,xp[:,k]) for k in range(3)])


def audit_external_carriers(manifest,workbench,c005,out,epsilon,final_time):
    """Check 2+ distinct independently generated model families and run genuine C005.

    Source manifest format: {"schema":"sst.a003.external-carriers/1","carriers":[
      {"name":"...","workbench_rel_path":"...","sha256":"64 hex",
      "seed":"fibonacci_torus_F3|fibonacci_torus_F4", "provider_group":"knotplot|gilbert|...",
      "independence_group":"...", "source_role":"computed_geometry_not_empirical"}]}
    """
    if manifest is None:return {'status':'UNRESOLVED','reason':'No independent external carrier manifest supplied; A003 analytic seeds are NOT independent datasets',
        'external_carriers_tested':0,'empirical_carriers':0}
    path=Path(manifest).resolve()
    if not path.is_file():return {'status':'UNRESOLVED','reason':'External carrier manifest missing'}
    m=json.loads(path.read_text('utf-8'))
    if m.get('schema')!='sst.a003.external-carriers/1' or not isinstance(m.get('carriers'),list):raise RuntimeError('invalid external source contract')
    if workbench is None or c005 is None:return {'status':'UNRESOLVED','reason':'Workbench or C005 missing'}
    from g6_pklsa_temporal_v030 import c005_callable,rk4
    from g6_dynamic_qualification_v031 import snapshot_screen
    roots=Path(workbench).resolve()
    if len(m['carriers'])>8:raise RuntimeError('external carrier budget exceeded')
    rhs,meta=c005_callable(c005,epsilon)
    rows=[];groups=set();providers=set();used=set()
    for item in m['carriers']:
        rel=Path(item.get('workbench_rel_path',''))
        if rel.is_absolute() or '..' in rel.parts:raise RuntimeError('unsafe external geometry path')
        src=(roots/rel).resolve()
        if not src.is_relative_to(roots) or not src.is_file():raise RuntimeError('external geometry not found inside Workbench')
        digest=sha256_file(src)
        if len(item.get('sha256',''))!=64 or item['sha256']!=digest:raise RuntimeError('external carrier byte hash mismatch')
        group=item.get('independence_group');provider=item.get('provider_group');seed=item.get('seed')
        if not isinstance(group,str) or not group or not isinstance(provider,str) or not provider or provider=='a003_analytic_seed_atlas':
            raise RuntimeError('no admissible provenance group')
        if seed not in ('fibonacci_torus_F3','fibonacci_torus_F4'):raise RuntimeError('unsupported topology family; no guessed crosswalk')
        if item.get('source_role')!='computed_geometry_not_empirical':raise RuntimeError('external source role must disclaim empirical independence')
        if (group,digest) in used:raise RuntimeError('duplicate carrier counted as independent')
        used.add((group,digest));groups.add(group);providers.add(provider)
        raw=np.loadtxt(src,dtype=float,comments='#')
        if raw.ndim!=2 or raw.shape[1]!=3:raise RuntimeError('source must be strict 3-column xyz file')
        try:
            a=arclength_resample(raw,150);b=arclength_resample(raw,300)
            end_a,_=rk4(rhs,a,final_time,16);end_b,_=rk4(rhs,b,final_time,16)
            screens=[snapshot_screen(x,seed) for x in (a,end_a,b,end_b)]
            diag=all(all(z['comparison']=='PASS_DIAGRAM_DETERMINANT' for z in r['diagrams']) for r in screens)
            clearance=all(r['near_segment_clearance']['clear_of_segment_contact'] for r in screens)
            rms=float(np.sqrt(np.mean(np.sum((end_a-end_b[::2])**2,axis=1))))
            rows.append({'name':item['name'],'source_sha256':digest,'source_file':str(src),
                'source_group':group,'provider_group':provider,'seed':seed,'geometry_record_count':len(raw),
                'geometry_has_no_ambiguous_projection':all(not z['nearly_degenerate_crossings'] for r in screens for z in r['diagrams']),
                'diagram_endpoints_pass':diag,'sampled_segment_clearance_pass':clearance,
                'rms_spatial_150_300':rms,'T':final_time,'epsilon':epsilon,
                'status':'PASS_BOUNDED_DIAGNOSTIC_ONLY' if diag and clearance else 'FAIL_TOPOLOGY_OR_CLEARANCE',
                'certified_topological_identity':False})
        except (ValueError,IndexError) as exc:
            rows.append({'name':item.get('name'), 'source_sha256':digest,
                'status':'UNRESOLVED','reason':type(exc).__name__+': '+str(exc)})
    result={'schema':'sst.a003.g6-independent-geometry/1','source_manifest_sha256':sha256_file(path),
       'external_carriers_tested':len(rows),'distinct_independence_groups':len(groups),
       'distinct_provider_groups':len(providers),'empirical_carriers':0,
       'rows':rows,'status':'PASS_DIAGNOSTIC_ONLY' if len(groups)>=2 and len(providers)>=2 and
          all(z['status']=='PASS_BOUNDED_DIAGNOSTIC_ONLY' for z in rows) else
          'FAIL_SOURCE_TOPOLOGY' if any(z['status'].startswith('FAIL') for z in rows) else 'UNRESOLVED',
       'note':'Independent computed source geometries, not empirical replication or full Euler dynamics.'}
    Path(out,'G6_EXTERNAL_CARRIER_DIAGNOSTICS.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
