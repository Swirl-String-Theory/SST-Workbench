"""SST horn-torus Neumann BEM audit package.

This package is a research-track numerical audit harness, not a canon proof.
It solves a boundary-corrected exterior Neumann candidate field

    v_N = v_ring + grad psi

where v_ring carries the circulation and psi is a single-valued single-layer
Laplace correction chosen to reduce n·v on the torus boundary.
"""

from .core import run_horn_bem, run_sweep

__all__ = ["run_horn_bem", "run_sweep"]
__version__ = "0.1.0-neumann-bem"
