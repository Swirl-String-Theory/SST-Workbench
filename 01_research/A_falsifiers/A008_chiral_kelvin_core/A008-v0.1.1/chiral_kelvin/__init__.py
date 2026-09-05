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
]

__version__ = "0.1.1"
