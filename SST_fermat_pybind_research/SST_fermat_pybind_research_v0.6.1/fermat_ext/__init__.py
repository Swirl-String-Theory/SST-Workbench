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
from .geodesic import (
    ClockDomainError,
    certify_closed_orbit_convergence,
    certify_global_closed_orbit,
    certify_monodromy_convergence,
    compute_reduced_monodromy,
    integrate_ray,
    make_clock_evaluator,
    shoot_closed_orbit,
)
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
    "ClockDomainError",
    "make_clock_evaluator",
    "integrate_ray",
    "shoot_closed_orbit",
    "certify_closed_orbit_convergence",
    "certify_global_closed_orbit",
    "certify_monodromy_convergence",
    "compute_reduced_monodromy",
]
__version__ = "0.6.1"

from .multistart import collect_seed_family, multistart_closed_orbit_search, selected_seed_convergence, continue_selected_seed_in_epsilon

from .hole_bundle import (
    BundleGridDefinition, HoleBundleParameters, RigidMotionProjector,
    axis_direction_from_tilts, bundle_beta_and_jacobian, clock_chain,
    estimate_axial_hole_radius, evaluate_bundle_shape_residual,
    fit_rigid_motion, fourier_mode_projection, make_combined_clock_evaluator,
)
