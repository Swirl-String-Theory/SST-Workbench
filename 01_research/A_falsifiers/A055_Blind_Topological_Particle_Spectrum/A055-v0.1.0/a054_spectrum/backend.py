from __future__ import annotations
from .kernels import measure_python
try:
    import a054_native as _native
except Exception:
    _native=None

def backend_name(force_python=False):
    return "python" if force_python or _native is None else "cpp"

def measure(components, core=0.03, force_python=False):
    if not force_python and _native is not None:
        return dict(_native.measure(components, core))
    return measure_python(components, core)

def native_available():
    return _native is not None
