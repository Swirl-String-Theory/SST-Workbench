from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class Gate:
    gate_id: str
    name: str
    status: str
    epistemic_status: str
    metrics: dict[str, Any]
    threshold: dict[str, Any]
    blocker: bool = True
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def status(condition: bool | None) -> str:
    if condition is None:
        return "NOT_RUN"
    return "PASS" if condition else "FAIL"


DEFAULT_THRESHOLDS = {
    "H0_edge_ratio_max": 1.05,
    "H0_source_length_relative_max": 0.005,
    "H0_source_diameter_relative_max": 0.03,
    "H1_contact_completeness_min": 0.95,
    "H1_contact_orth_rms_max": 0.08,
    "H2_inverse_rms_max": 0.01,
    "H2_winding_required": 1,
    "H3_billiard_closure_max": 2e-3,
    "H3_lower_period_min": 1e-2,
    "H3_unique_points_min": 9,
    "H3_paired_orbit_hausdorff_max": 0.02,
    "H4_force_compatibility_max": 0.20,
    "H4_ill_conditioned_fraction_max": 0.05,
    "H4_local_balance_max": 0.10,
    "H5_relative_equilibrium_max": 0.25,
    "H6_force_shape_residual_max": 0.35,
    "H6_tension_cv_max": 0.50,
    "H6_binormal_leakage_max": 0.25,
    "H6_alignment_min": 0.50,
    "H7_core_sweep_pass_fraction_min": 0.60,
    "H8_nonlocal_force_shape_residual_max": 0.50,
    "H8_nonlocal_alignment_min": 0.50,
}
