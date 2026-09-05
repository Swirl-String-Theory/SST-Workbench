"""Standalone SST Fermat research package; no SSTcore dependency."""

from .core import analyze_profile, sweep_profiles, write_csv, write_json
from .knot_catalog import DEFAULT_KNOT_IDS, available_knots, sample_ideal_knot
from .knot_scan import (
    field_convergence_ladder,
    scan_catalog_knot,
    scan_catalog_matrix,
    scan_softening_matrix,
    scan_torus_knot,
    torus_knot,
)
from .resolution import resolution_plan
from .certification import (
    build_bifurcation_atlas,
    certify_candidate_convergence,
    estimate_reach_diagnostic,
    scan_stationary_candidates,
    symmetry_field_audit,
)

__all__ = [
    "analyze_profile",
    "sweep_profiles",
    "scan_catalog_knot",
    "scan_catalog_matrix",
    "scan_torus_knot",
    "scan_softening_matrix",
    "field_convergence_ladder",
    "resolution_plan",
    "torus_knot",
    "sample_ideal_knot",
    "available_knots",
    "DEFAULT_KNOT_IDS",
    "write_json",
    "write_csv",
    "scan_stationary_candidates",
    "certify_candidate_convergence",
    "build_bifurcation_atlas",
    "estimate_reach_diagnostic",
    "symmetry_field_audit",
]
__version__ = "0.4.1"
