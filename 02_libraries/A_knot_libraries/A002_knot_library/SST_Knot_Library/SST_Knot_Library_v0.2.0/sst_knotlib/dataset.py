from __future__ import annotations
import json
from pathlib import Path
from .formats import load_geometry
from .registry import KAtlasSnapshot, infer_knot_id_from_name
from .blind import geometry_sha256
from .geometry import resample_closed
from .providers import certify_geometry
from .library_root import sources_root, find_knot_library_root

DEFAULT_EXTENSIONS={'.txt','.xyz','.csv','.vect','.knot','.kp','.kpf'}


def default_sources_root():
    """Default scan root: Knot_Library/Sources when discoverable."""
    lib=find_knot_library_root()
    if lib is None:
        raise FileNotFoundError('Knot_Library/Sources not found; pass an explicit root to scan-dataset')
    return sources_root(lib)


def scan_dataset(root=None, *, n_hash: int=512, certify: bool=False, provider: str='auto', extensions=None):
    root=Path(root) if root is not None else default_sources_root()
    extset={x.lower() for x in (extensions or DEFAULT_EXTENSIONS)}; reg=KAtlasSnapshot(); rows=[]
    for path in sorted(p for p in root.rglob('*') if p.is_file() and (p.suffix.lower() in extset or p.name.lower() in {'fseries','ideal','ideal.txt'})):
        row={'path':str(path),'relative_path':str(path.relative_to(root)),'expected_topology':infer_knot_id_from_name(str(path.relative_to(root)))}
        try:
            a=load_geometry(path)
            row.update({'load_status':'OK','source_family':a.source_family,'source_format':a.source_format,
                        'source_sha256':a.source_sha256,'components':len(a.components),'n_points':[len(c) for c in a.components],
                        'provider_id':a.provider_id,'provider_name':a.provider_name,'provider_class':a.provider_class,
                        'warnings':a.warnings})
            row['canonical_geometry_sha256']=[geometry_sha256(resample_closed(c,n_hash)) for c in a.components]
            kid=row['expected_topology']; row['katlas_registered']=bool(kid and reg.has(kid))
            if certify and len(a.components)==1 and kid and reg.has(kid):
                row['topology_certification']=certify_geometry(resample_closed(a.components[0],n_hash),kid,provider=provider,registry=reg).to_dict()
            else:
                row['topology_certification']={'status':'UNVERIFIED','pass':False,'provider':'none'}
        except Exception as e:
            row.update({'load_status':'ERROR','error':f'{type(e).__name__}: {e}'})
        rows.append(row)
    return {'root':str(root),'file_count':len(rows),'katlas_snapshot_id':reg.snapshot_id,'katlas_snapshot_sha256':reg.sha256,'files':rows}


def write_inventory(path, report):
    Path(path).write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
