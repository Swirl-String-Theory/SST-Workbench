from __future__ import annotations
import sys
from typing import Any
from . import _config

_BACKEND = None
_BACKEND_NAME = None


def load_backend(*, force_python: bool = False, skip_build: bool = False,
                 force_build: bool = False, build_verbose: bool = False):
    global _BACKEND, _BACKEND_NAME
    if force_python:
        from . import fallback
        return fallback, "python"
    if _BACKEND is not None and not force_build:
        return _BACKEND, _BACKEND_NAME
    if not skip_build:
        try:
            from .build_ext_if_needed import build_if_needed
            build_if_needed(force=force_build, verbose=build_verbose)
        except Exception as exc:
            if build_verbose:
                print(f"{_config.LOG_PREFIX} build attempt failed: {exc}", file=sys.stderr)
    try:
        mod = __import__(f"{_config.PACKAGE_NAME}.{_config.EXT_BASENAME}", fromlist=["*"])
        _BACKEND, _BACKEND_NAME = mod, "cpp"
        return mod, "cpp"
    except Exception as exc:
        if build_verbose:
            print(f"{_config.LOG_PREFIX} native import failed: {exc}", file=sys.stderr)
        from . import fallback
        _BACKEND, _BACKEND_NAME = fallback, "python"
        return fallback, "python"


def backend_info(**kwargs: Any) -> dict[str, Any]:
    mod, name = load_backend(**kwargs)
    info = {"backend": name}
    if hasattr(mod, "backend_info"):
        try:
            info.update(dict(mod.backend_info()))
        except Exception:
            pass
    return info
