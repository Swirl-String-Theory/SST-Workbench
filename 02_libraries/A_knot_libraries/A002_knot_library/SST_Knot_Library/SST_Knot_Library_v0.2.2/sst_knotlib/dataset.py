from __future__ import annotations
import json
from pathlib import Path
from .formats import load_geometry, classify_non_geometry_file, file_sha256
from .registry import KAtlasSnapshot, infer_topology_hint_from_name
from .blind import geometry_sha256
from .geometry import resample_closed
from .providers import certify_geometry
from .sources import source_provider_info

DEFAULT_EXTENSIONS={'.txt','.xyz','.csv','.vect','.knot','.kp','.kpf'}


def scan_dataset(root, *, n_hash: int=512, certify: bool=False, provider: str='auto', extensions=None):
    root=Path(root); extset={x.lower() for x in (extensions or DEFAULT_EXTENSIONS)}; reg=KAtlasSnapshot(); rows=[]
    paths=sorted(p for p in root.rglob('*') if p.is_file() and (p.suffix.lower() in extset or p.name.lower() in {'fseries','ideal','ideal.txt'}))
    for path in paths:
        rel=str(path.relative_to(root)); hint=infer_topology_hint_from_name(rel)
        row={
            'path':str(path),'relative_path':rel,
            'topology_hint':hint,
            'topology_kind':hint.get('kind') if hint else None,
            'expected_topology':hint.get('id') if hint else None,
            'expected_components':hint.get('components_hint') if hint else None,
        }
        nong=classify_non_geometry_file(path)
        if nong:
            row.update({
                'load_status':'SKIPPED_METADATA','source_sha256':file_sha256(path),
                'metadata_role':nong['role'],'provider_id':nong['provider_id'],'reason':nong['reason'],
                'topology_certification':{'status':'UNVERIFIED','pass':False,'provider':'none'}
            })
            rows.append(row); continue
        try:
            a=load_geometry(path); pi=source_provider_info(a.source_family,str(path))
            row.update({
                'load_status':'OK','source_family':a.source_family,'source_format':a.source_format,
                'source_sha256':a.source_sha256,'components':len(a.components),'n_points':[len(c) for c in a.components],
                'provider_id':pi['provider_id'],'provider_name':pi['name'],'provider_class':pi['class'],
                'provider_catalog_id':pi['catalog_id'],'provider_catalog_sha256':pi['catalog_sha256'],
                'warnings':a.warnings,'metadata':a.metadata,
            })
            row['component_count_matches_hint']=(row['expected_components'] is None or len(a.components)==row['expected_components'])
            row['canonical_geometry_sha256']=[geometry_sha256(resample_closed(c,n_hash)) for c in a.components]
            kid=row['expected_topology'] if row['topology_kind']=='knot' else None
            row['katlas_registered']=bool(kid and reg.has(kid))
            if certify and len(a.components)==1 and kid and reg.has(kid):
                row['topology_certification']=certify_geometry(resample_closed(a.components[0],n_hash),kid,provider=provider,registry=reg).to_dict()
            else:
                note='no geometry topology provider executed'
                if row['topology_kind'] in {'link','torus'}: note='link/torus filename is an expected-topology hint only; no imported-geometry certification executed'
                row['topology_certification']={'status':'UNVERIFIED','pass':False,'provider':'none','notes':[note]}
        except Exception as e:
            row.update({'load_status':'ERROR','error':f'{type(e).__name__}: {e}'})
        rows.append(row)
    counts={s:sum(r.get('load_status')==s for r in rows) for s in ('OK','SKIPPED_METADATA','ERROR')}
    return {
        'root':str(root),'file_count':len(rows),'counts':counts,
        'katlas_snapshot_id':reg.snapshot_id,'katlas_snapshot_sha256':reg.sha256,'files':rows
    }


def write_inventory(path, report):
    Path(path).write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
