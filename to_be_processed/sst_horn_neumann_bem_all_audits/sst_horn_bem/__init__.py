"""SST horn-torus Neumann BEM audit package.

Research-track numerical audit harness for the exterior horn-torus Neumann
Dirichlet-energy problem.  It keeps kinetic, cavitation, and hollow-core total
energy factors separated.
"""

from .core import run_horn_bem, run_sweep
from .audits import run_panel_refinement, run_volume_refinement, run_offset_probe_audit, summarize_all

__all__ = [
    "run_horn_bem",
    "run_sweep",
    "run_panel_refinement",
    "run_volume_refinement",
    "run_offset_probe_audit",
    "summarize_all",
]
__version__ = "0.2.0-neumann-bem-all-audits"
