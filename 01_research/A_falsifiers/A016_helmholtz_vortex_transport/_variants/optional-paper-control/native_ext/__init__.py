"""Helmholtz-SST native backend facade.

Imports are deliberately lazy so ``python -m native_ext.build_ext_if_needed``
does not preload the build submodule through package initialization.
"""
from __future__ import annotations

__version__ = "0.1.1"
__all__ = [
    "backend_info", "polyline_stats", "interaction_energy", "biot_savart",
    "gauss_linking", "min_segment_distance", "doubly_critical_distance",
]

def __getattr__(name: str):
    if name in __all__:
        from . import core
        return getattr(core, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
