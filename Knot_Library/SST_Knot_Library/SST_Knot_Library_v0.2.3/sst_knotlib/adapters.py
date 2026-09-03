from __future__ import annotations
from typing import Any, Dict
import numpy as np
from .geometry import resample_closed
from .diagnostics import qualify_seed, convergence_report
from .blind import geometry_sha256
from .version import __version__
from .registry import KAtlasSnapshot, normalize_knot_id
from .providers import certify_geometry


def prepare_for_falsifier(points: np.ndarray, *, core_radius: float, n: int = 512,
                           source_family: str = 'unknown', source_parameters: Dict[str,Any] | None = None,
                           convergence_levels=(256,512,1024), expected_topology: str|None=None,
                           topology_provider: str='auto', require_topology_certified: bool=False):
    """Canonical pre-dynamics adapter used by downstream falsifiers.

    The geometry is frozen before physics/outcome analysis. An expected topology is never treated
    as certified merely because of a filename or caller label.
    """
    p=resample_closed(points,n)
    q=qualify_seed(p,core_radius=core_radius,n=n)
    conv=convergence_report(p,levels=convergence_levels)
    reg=KAtlasSnapshot(); expected=normalize_knot_id(expected_topology)
    if expected:
        cert=certify_geometry(p,expected,provider=topology_provider,registry=reg).to_dict()
    else:
        cert={'status':'UNVERIFIED','pass':False,'provider':'none','expected_topology':None,'notes':['no expected topology supplied']}
    if require_topology_certified and cert.get('status')!='CERTIFIED':
        raise ValueError(f'topology is not CERTIFIED: {cert.get("status")} via {cert.get("provider")}')
    provenance={
        'knot_library':f'sst-knot-library/{__version__}',
        'legacy_geometry_api':'sst_knotlib',
        'source_family':source_family,
        'source_parameters':source_parameters or {},
        'resample_N':n,
        'core_radius':core_radius,
        'geometry_sha256':geometry_sha256(p),
        'expected_topology':expected,
        'topology_certification':cert,
        'katlas_snapshot_id':reg.snapshot_id,
        'katlas_snapshot_sha256':reg.sha256,
        'qualification':q,
        'convergence':conv,
    }
    return p,provenance
