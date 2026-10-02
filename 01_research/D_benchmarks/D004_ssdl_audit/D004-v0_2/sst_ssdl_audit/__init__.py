"""SST SSDL (Separatrix Surface-Density Lift) audit package.

Research-track numerical/analytic audit harness for:
- Route A: spherical exterior monopole DtN projector normalization
- Route B: Planck-normal normal-stack / mode-count normalization

This package is intentionally labeled Research Track. It checks the operator
and counting structure, but it does not prove the open constitutive lemmas:
L1: rho_Lambda couples as isotropic normal separatrix source.
L2: Omega_L0 is the correct projection factor or must be replaced.
L3: ell_P is the correct normal resolution thickness.
"""

from .core import run_ssdl_audit, run_route_a_dtn, run_route_b_mode_count

__all__ = ["run_ssdl_audit", "run_route_a_dtn", "run_route_b_mode_count"]
__version__ = "0.2.0-ssdl-audit"
