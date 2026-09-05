from __future__ import annotations
import json
import platform
import sys
from pathlib import Path
import numpy as np
from .version import __version__


def runtime_attestation():
    info = {
        "format": "SST-KNOT-GEOMETRY-RUNTIME-1.0",
        "geometry_library": f"sst-knot-geometry/{__version__}",
        "python_version": sys.version.split()[0],
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "numpy_version": np.__version__,
        "native_backend_imported": False,
        "native_backend_module": None,
        "openmp_enabled": False,
    }
    try:
        from . import _sstknot_native as native
        info["native_backend_imported"] = True
        info["native_backend_module"] = str(getattr(native, "__file__", None))
        info["openmp_enabled"] = bool(getattr(native, "openmp_enabled", False))
    except Exception as exc:
        info["native_import_error"] = f"{type(exc).__name__}: {exc}"
    return info


def write_runtime_attestation(path):
    info = runtime_attestation()
    Path(path).write_bytes((json.dumps(info, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    return info
