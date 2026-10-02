"""SST dark-knot Rayleigh / rocking / breathing audit harness."""

from .core import (
    run,
    run_audit,
    run_sweep,
    run_all_checks,
    write_csv,
    write_json,
    load_vertices_csv,
    save_vertices_csv,
)

__all__ = [
    "run",
    "run_audit",
    "run_sweep",
    "run_all_checks",
    "write_json",
    "write_csv",
    "load_vertices_csv",
    "save_vertices_csv",
]

__version__ = "0.2.0-research-track"
