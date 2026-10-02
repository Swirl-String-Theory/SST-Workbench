from __future__ import annotations
import json, platform, sys
from pathlib import Path
import numpy as np
from .version import __version__
from .registry import KAtlasSnapshot
from .providers import provider_status


def runtime_attestation():
    reg=KAtlasSnapshot()
    info={
        'format':'SST-KNOT-LIBRARY-RUNTIME-2.0',
        'knot_library':f'sst-knot-library/{__version__}',
        'legacy_module':'sst_knotlib',
        'python_version':sys.version.split()[0],
        'python_implementation':platform.python_implementation(),
        'platform':platform.platform(),
        'numpy_version':np.__version__,
        'katlas_snapshot_id':reg.snapshot_id,
        'katlas_snapshot_sha256':reg.sha256,
        'providers':provider_status(),
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
