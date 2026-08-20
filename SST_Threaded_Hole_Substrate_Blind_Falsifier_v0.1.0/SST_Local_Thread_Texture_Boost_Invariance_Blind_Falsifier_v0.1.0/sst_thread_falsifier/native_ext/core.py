from __future__ import annotations
import os
from . import fallback

_BACKEND = None
_NATIVE = None


def _load(force_python=False, skip_build=False, force_build=False):
    global _BACKEND, _NATIVE
    if force_python:
        _BACKEND = "python"
        _NATIVE = None
        return
    if not skip_build:
        try:
            from .build_ext_if_needed import build
            build(force=force_build, strict=False, quiet=True)
        except Exception:
            pass
    try:
        from . import _native
        _NATIVE = _native
        _BACKEND = "cpp"
    except Exception:
        _NATIVE = None
        _BACKEND = "python"


def backend_name():
    if _BACKEND is None:
        _load(force_python=os.environ.get("SST_FORCE_PYTHON") == "1")
    return _BACKEND


def biot_savart(points, component_offsets, gamma=1.0, core_radius=0.05,
                 force_python=False, skip_build=False, force_build=False):
    if force_python:
        return fallback.biot_savart(points, component_offsets, gamma, core_radius)
    if _BACKEND is None or force_build:
        _load(False, skip_build, force_build)
    if _NATIVE is not None:
        return _NATIVE.biot_savart(points, component_offsets, gamma, core_radius)
    return fallback.biot_savart(points, component_offsets, gamma, core_radius)
