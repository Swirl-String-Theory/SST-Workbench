from __future__ import annotations
import sys
from typing import Any
import numpy as np
from . import _config


def _load_cpp_backend(*, force_build: bool=False, build_verbose: bool=False):
    try:
        from .build_ext_if_needed import build_if_needed
        build_if_needed(force=force_build, verbose=build_verbose)
        return __import__(f"{_config.PACKAGE_NAME}.{_config.EXT_BASENAME}", fromlist=["*"])
    except Exception as exc:
        if build_verbose:
            print(f"{_config.LOG_PREFIX} load failed: {exc}", file=sys.stderr)
        return None


def backend_status() -> dict[str, Any]:
    mod=_load_cpp_backend(build_verbose=False)
    return {"available":mod is not None,"backend":"cpp-pybind11" if mod is not None else "python-fallback","version":mod.version() if mod is not None and hasattr(mod,"version") else None}


def analyze_geometry(points, component_counts, *, radius=-1.0, contact_tol=0.015, kink_tol=0.015,
                     local_exclusion_frac=0.02, threads=1, require_native=False, force_python=False,
                     force_build=False, build_verbose=False):
    P=np.ascontiguousarray(points,dtype=np.float64)
    C=np.ascontiguousarray(component_counts,dtype=np.int64)
    if not force_python:
        mod=_load_cpp_backend(force_build=force_build,build_verbose=build_verbose)
        if mod is not None:
            return mod.analyze_geometry(P,C,float(radius),float(contact_tol),float(kink_tol),float(local_exclusion_frac),int(threads))
    if require_native:
        raise RuntimeError("C++ pybind11 backend is required but unavailable. Run 5_run_install.cmd first.")
    from .fallback import analyze_geometry as fb
    return fb(P,C,radius=float(radius),contact_tol=float(contact_tol),kink_tol=float(kink_tol),local_exclusion_frac=float(local_exclusion_frac),threads=int(threads))
