"""GPU-first SYCL/OpenMP backend for Kelvin-Joule SST."""
from .core import run_smoke,native_info,resolve_backend
__version__="0.1.0"
__all__=["run_smoke","native_info","resolve_backend"]
