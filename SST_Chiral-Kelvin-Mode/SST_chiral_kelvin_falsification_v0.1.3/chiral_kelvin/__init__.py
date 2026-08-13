"""SST chiral Kelvin falsification package."""

from .core import (
    biot_savart_velocity,
    build_normal_operator,
    filament_energy,
    four_state_energy_check,
    gamma0,
    jacobian_action,
    make_ring,
    make_torus_trefoil,
    mirror_x,
    mode_table,
    run_audit,
    spectral_symmetry_checks,
    write_csv,
    write_json,
)

from .convergence import (
    compare_resolutions,
    group_degenerate_modes,
    match_groups,
    matcher_self_check,
    ring_fourier_label,
    run_convergence_campaign,
    solve_mode_bundle,
    subspace_circularities,
)

from .convergence_v012 import (
    core_resolution,
    eigen_condition_numbers,
    arclength_fourier_fingerprint,
    group_matching_clusters,
    match_clusters,
    matcher_self_check_v012,
    run_convergence_campaign_v012,
)

from .conclusions import (
    CONCLUSIONS,
    build_conclusions_summary,
    write_conclusions_summary,
)

__all__ = [
    "gamma0",
    "make_ring",
    "make_torus_trefoil",
    "mirror_x",
    "biot_savart_velocity",
    "jacobian_action",
    "filament_energy",
    "build_normal_operator",
    "mode_table",
    "four_state_energy_check",
    "spectral_symmetry_checks",
    "run_audit",
    "write_json",
    "write_csv",
    "solve_mode_bundle",
    "group_degenerate_modes",
    "subspace_circularities",
    "ring_fourier_label",
    "match_groups",
    "compare_resolutions",
    "matcher_self_check",
    "run_convergence_campaign",
    "core_resolution",
    "eigen_condition_numbers",
    "arclength_fourier_fingerprint",
    "group_matching_clusters",
    "match_clusters",
    "matcher_self_check_v012",
    "run_convergence_campaign_v012",
    "CONCLUSIONS",
    "build_conclusions_summary",
    "write_conclusions_summary",
]

__version__ = "0.1.3"
