from __future__ import annotations
import importlib
import os
from typing import Any

_backend = None
_attempted = False

def backend(force_build: bool = False):
    global _backend, _attempted
    if _backend is not None: return _backend
    if _attempted and not force_build: return None
    _attempted = True
    try:
        _backend = importlib.import_module("native_ext._native")
        return _backend
    except Exception:
        pass
    if os.environ.get("SST_NATIVE_SKIP_BUILD", "0") == "1": return None
    try:
        from .build_ext_if_needed import build_if_needed
        if build_if_needed(force=force_build, verbose=os.environ.get("SST_NATIVE_QUIET","0")!="1"):
            importlib.invalidate_caches()
            _backend = importlib.import_module("native_ext._native")
            return _backend
    except Exception:
        return None
    return None

def set_num_threads(n: int) -> None:
    b=backend()
    if b is not None and hasattr(b,"set_num_threads"):
        b.set_num_threads(int(n))

def backend_info() -> dict[str, Any]:
    b=backend()
    if b is None:
        return {"backend":"python","native":False,"openmp":False,"threads":1}
    try: return dict(b.backend_info())
    except Exception: return {"backend":"cpp","native":True}
