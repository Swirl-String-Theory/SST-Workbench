from __future__ import annotations
import json, platform, sys
from pathlib import Path
import numpy as np
from .version import __version__
from .registry import KAtlasSnapshot
from .providers import provider_status
from .sources import source_catalog


def _release_identity():
    root=Path(__file__).resolve().parent.parent
    p=root/'RELEASE.json'
    if p.is_file():
        try:
            d=json.loads(p.read_text(encoding='utf-8'))
            declared=str(d.get('version'))
            return {'release_file':str(p),'declared_version':declared,'runtime_version':__version__,'match':declared==__version__,'release':d}
        except Exception as e:
            return {'release_file':str(p),'declared_version':None,'runtime_version':__version__,'match':False,'error':f'{type(e).__name__}: {e}'}
    # Installed non-editable wheels may not preserve repository-root metadata.
    return {'release_file':str(p),'declared_version':None,'runtime_version':__version__,'match':None,'note':'RELEASE.json not present in installation root'}


def runtime_attestation():
    reg=KAtlasSnapshot(); cat=source_catalog(); prov=provider_status(); rel=_release_identity()
    info={
        'format':'SST-KNOT-LIBRARY-RUNTIME-2.2',
        'knot_library':f'sst-knot-library/{__version__}',
        'legacy_module':'sst_knotlib',
        'release_identity':rel,
        'python_version':sys.version.split()[0],
        'python_implementation':platform.python_implementation(),
        'platform':platform.platform(),
        'numpy_version':np.__version__,
        'katlas_snapshot_id':reg.snapshot_id,
        'katlas_snapshot_sha256':reg.sha256,
        'source_catalog_id':cat['catalog_id'],
        'source_catalog_sha256':cat['_sha256'],
        'providers':prov,
        'native_backend_imported':False,'native_backend_module':None,'openmp_enabled':False,
    }
    try:
        from . import _sstknot_native as native
        info['native_backend_imported']=True
        info['native_backend_module']=str(getattr(native,'__file__',None))
        info['openmp_enabled']=bool(getattr(native,'openmp_enabled',False))
    except Exception as exc: info['native_import_error']=f'{type(exc).__name__}: {exc}'
    return info


def write_runtime_attestation(path):
    info=runtime_attestation(); Path(path).write_bytes((json.dumps(info,indent=2,ensure_ascii=False)+'\n').encode('utf-8')); return info
