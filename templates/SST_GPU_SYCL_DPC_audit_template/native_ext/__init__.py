"""GPU-first SYCL/DPC++ pybind11 audit template (Arc / Level Zero)."""

from .core import run, run_all_checks, run_audit, run_sweep, run_tiny, write_csv, write_json

__all__ = [
    "run",
    "run_audit",
    "run_sweep",
    "run_all_checks",
    "run_tiny",
    "write_json",
    "write_csv",
]
__version__ = "0.1.0-template"
