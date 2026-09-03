from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import numpy as np
from .version import __version__
from .formats import load_geometry
from .geometry import resample_closed, normalize_centerline
from .diagnostics import qualify_seed, convergence_report, linking_matrix
from .blind import geometry_sha256
from .registry import KAtlasSnapshot, infer_topology_hint_from_name, normalize_knot_id
from .providers import certify_geometry
from .models import KnotRecord
from .sources import source_provider_info


def make_knot_record(path, *, expected_topology: str|None=None, core_radius: float|None=None,
                     n: int=512, normalize_length: float|None=None, topology_provider: str='auto',
                     convergence_levels=(256,512,1024), format='auto') -> tuple[list[np.ndarray],KnotRecord]:
    asset=load_geometry(path,format=format)
    hint=infer_topology_hint_from_name(str(path))
    expected=normalize_knot_id(expected_topology) if expected_topology else (hint.get('id') if hint else None)
    registry=KAtlasSnapshot()
    ref=registry.get(expected).to_dict() if expected and registry.has(expected) else None
    canonical=[]
    component_geometry=[]
    qualifications=[]; convergences=[]
    for c in asset.components:
        p=resample_closed(c,n)
        if normalize_length is not None: p=normalize_centerline(p,float(normalize_length))
        canonical.append(p)
        component_geometry.append({'N':len(p),'geometry_sha256':geometry_sha256(p)})
        if core_radius is not None:
            qualifications.append(qualify_seed(p,float(core_radius),n=n))
            convergences.append(convergence_report(p,levels=convergence_levels))
    if len(canonical)==1 and expected:
        cert=certify_geometry(canonical[0],expected,provider=topology_provider,registry=registry).to_dict()
    elif expected and len(canonical)>1:
        cert={'status':'UNVERIFIED','pass':False,'expected_topology':expected,'provider':'none','notes':['multi-component imported-geometry certification is not implemented in v0.2.4']}
    else:
        cert={'status':'UNVERIFIED','pass':False,'expected_topology':expected,'provider':'none','notes':['no expected topology supplied or inferred']}
    spi=source_provider_info(asset.source_family,asset.source_path)
    geometry={
        'source_path':asset.source_path,'source_family':asset.source_family,'source_format':asset.source_format,
        'source_sha256':asset.source_sha256,'source_provider':spi,'warnings':asset.warnings,'metadata':asset.metadata,
        'component_count':len(canonical),'components':component_geometry,'resample_N':n,
        'normalized_length':normalize_length,
        'pairwise_linking_matrix':linking_matrix(canonical).tolist() if len(canonical)>1 else None,
    }
    record=KnotRecord(
        topology_expected=expected,topology_reference=ref,topology_certification=cert,geometry=geometry,
        qualification=qualifications[0] if len(qualifications)==1 else (qualifications or None),
        convergence=convergences[0] if len(convergences)==1 else (convergences or None),
        provenance={'knot_library':f'sst-knot-library/{__version__}','legacy_geometry_api':'sst_knotlib',
                    'katlas_snapshot_id':registry.snapshot_id,'katlas_snapshot_sha256':registry.sha256,'topology_hint':hint},
    )
    return canonical,record


def write_record(path, record: KnotRecord|dict):
    obj=record.to_dict() if hasattr(record,'to_dict') else record
    Path(path).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
