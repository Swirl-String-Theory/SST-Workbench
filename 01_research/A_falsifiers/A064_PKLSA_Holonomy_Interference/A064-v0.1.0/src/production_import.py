"""Strict optional PKLSA E010 carrier manifest reader.

No filename-only discovery, no implicit approval of generated carriers.
Inputs are read-only; source files remain untouched.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from holonomy import load_points,sha256,gauss_link,interference_visibility

MANDATORY=('topology_id','carrier_id','geometry_sha256','provider_group','source_role','source_path','qualification_gate_pass')


def read_manifest(path):
    p=Path(path).resolve();root=p.parent
    d=json.loads(p.read_text(encoding='utf-8'))
    if d.get('schema')!='A064-PKLSA-MANIFEST-1':
        raise ValueError('Unsupported explicit manifest schema')
    if d.get('pklsa_version')!='0.4.0':
        raise ValueError('Current external contract pins PKLSA 0.4.0, not a silently substituted release')
    if d.get('release_schema')!='PKLSA-HIGH-RES-QUALIFICATION-4' or not d.get('publication_ready_geometry_layer',False):
        raise ValueError('PKLSA 0.4.0 release is not qualified; rejecting production admission')
    out=[]
    for case in d.get('carriers',[]):
        missing=[k for k in MANDATORY if k not in case]
        if missing: raise ValueError(f'Carrier missing {missing}')
        if not case['qualification_gate_pass']:
            raise ValueError(f'Unqualified carrier: {case["carrier_id"]}')
        if case['source_role'] in ('generated','derived','synthetic'):
            raise ValueError('Generated carriers not independent upstream evidence')
        rel=Path(case['source_path'])
        if rel.is_absolute() or '..' in rel.parts: raise ValueError('Explicit source_path must be relative and contained')
        resolved=(root/rel).resolve()
        if not resolved.is_relative_to(root):raise ValueError('Source escapes manifest root')
        if not resolved.is_file():raise FileNotFoundError(resolved)
        if sha256(resolved)!=case['geometry_sha256']: raise ValueError('Geometry SHA-256 mismatch')
        components=load_points(resolved)
        out.append((case,components))
    return out


def evaluate_external(manifest,order=4,charge=.5):
    carriers=read_manifest(manifest)
    records=[];votes={};geometry_count=0
    for entry,comps in carriers:
        geometry_count+=1
        key=(entry['topology_id'],entry['provider_group'])
        votes.setdefault(key,[]).append(entry['carrier_id'])
        for i in range(len(comps)):
            for j in range(i+1,len(comps)):
                a,b=comps[i],comps[j]
                v=gauss_link(a,b,order=order)
                prob,phase=interference_visibility(v,charge)
                records.append(dict(topology_id=entry['topology_id'],carrier_id=entry['carrier_id'],provider_group=entry['provider_group'],component_i=i,component_j=j,gauss_link=v,rounded_link=round(v),integer_error=abs(v-round(v)),toy_probability=prob,phase_rad=phase))
    groups={}
    for (topo,prov),ids in votes.items(): groups.setdefault(topo,set()).add(prov)
    provider_admission={topo:len(ps) for topo,ps in groups.items()}
    return dict(geometry_count=geometry_count,provider_groups_per_topology=provider_admission,records=records,independence_qualified_topologies=[t for t,n in provider_admission.items() if n>=2])
