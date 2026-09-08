from __future__ import annotations
import sys
from . import _config

_BACKEND=None
_BACKEND_NAME=None

def load_backend(*, force_python=False, force_build=False, build_verbose=False):
    global _BACKEND,_BACKEND_NAME
    if force_python:
        from . import fallback
        return fallback,"python"
    if _BACKEND is not None:
        return _BACKEND,_BACKEND_NAME
    try:
        from .build_ext_if_needed import build_if_needed
        build_if_needed(force=force_build, verbose=build_verbose)
        mod=__import__(f"{_config.PACKAGE_NAME}.{_config.EXT_BASENAME}",fromlist=["*"])
        _BACKEND,_BACKEND_NAME=mod,"cpp"
    except Exception as exc:
        print(f"{_config.LOG_PREFIX} native unavailable: {exc}; using Python fallback",file=sys.stderr)
        from . import fallback
        _BACKEND,_BACKEND_NAME=fallback,"python"
    return _BACKEND,_BACKEND_NAME
