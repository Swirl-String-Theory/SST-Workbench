from __future__ import annotations
from ._config import VERSION as __version__


def load_native(force_build: bool = False, verbose: bool = False):
    from .build_ext_if_needed import build_if_needed
    build_if_needed(force=force_build, verbose=verbose)
    try:
        from . import _native
        return _native
    except Exception:
        return None


def backend_info() -> dict:
    mod = load_native(force_build=False, verbose=False)
    if mod is None:
        return {"backend": "python", "version": __version__, "openmp": False, "threads": 1}
    return dict(mod.backend_info())
