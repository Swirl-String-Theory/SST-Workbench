"""Load explicitly built pybind11 CPU kernel. Never silently fall back to Python."""
from importlib import import_module

def load_cpp():
    try:
        return import_module('native_ext._sst_native')
    except ImportError as exc:
        raise RuntimeError('CPP_NOT_BUILT: run python tools/build_native.py, install pybind11; no Python fallback') from exc
