from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from .core import run_horn_bem

TWOPI = 2.0 * math.pi


def _delta_rows(rows: List[Dict[str, Any]], key: str = "chi_K") -> List[Dict[str, Any]]:
    prev = None
    out = []
    for row in rows:
        r = dict(row)
        if prev is None:
            r[f"delta_{key}_from_previous"] = float("nan")
            r[f"rel_delta_{key}_from_previous"] = float("nan")
        else:
            d = float(row[key]) - float(prev[key])
            r[f"delta_{key}_from_previous"] = d
            r[f"rel_delta_{key}_from_previous"] = d / max(1e-30, abs(float(prev[key])))
        out.append(r)
        prev = row
    return out


def run_panel_refinement(
    lambda_: float = 1.2,
    panel_grids: Sequence[Tuple[int, int]] = ((8, 16), (12, 24), (16, 32)),
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """Refine BEM panel grid while keeping volume grid fixed."""
    rows: List[Dict[str, Any]] = []
    for n_eta, n_phi in panel_grids:
        r = run_horn_bem(lambda_=lambda_, bem=True, bem_n_eta=n_eta, bem_n_phi=n_phi, **kwargs)
        r["audit_kind"] = "panel_refinement"
        r["panel_grid"] = f"{n_eta}x{n_phi}"
        rows.append(r)
    return _delta_rows(rows, "chi_K")


def run_volume_refinement(
    lambda_: float = 1.2,
    n_volumes: Sequence[int] = (14, 18, 22),
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    """Refine volume integration grid while keeping BEM panel grid fixed."""
    rows: List[Dict[str, Any]] = []
    for nv in n_volumes:
        r = run_horn_bem(lambda_=lambda_, n_volume=nv, bem=True, **kwargs)
        r["audit_kind"] = "volume_refinement"
        r["volume_grid"] = nv
        rows.append(r)
    return _delta_rows(rows, "chi_K")


def run_offset_probe_audit(
    lambda_: float = 1.2,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Run one BEM case and surface its built-in one-sided offset probe."""
    r = run_horn_bem(lambda_=lambda_, bem=True, **kwargs)
    return {
        "audit_kind": "offset_boundary_probe",
        "lambda_": r.get("lambda_"),
        "solver_kind": r.get("solver_kind"),
        "bem_panels": r.get("bem_panels"),
        "neumann_boundary_error": r.get("neumann_boundary_error"),
        "neumann_boundary_error_direct_probe": r.get("neumann_boundary_error_direct_probe"),
        "offset_probe_min_error": r.get("offset_probe_min_error"),
        "offset_probe_max_error": r.get("offset_probe_max_error"),
        "offset_probe_last_error": r.get("offset_probe_last_error"),
        "gate_offset_probe_pass": r.get("gate_offset_probe_pass"),
        "offset_probe": r.get("offset_probe", []),
        "full_result": r,
    }


def summarize_all(
    ring: Dict[str, Any],
    bem: Dict[str, Any],
    sweep: List[Dict[str, Any]],
    panel: List[Dict[str, Any]],
    volume: List[Dict[str, Any]],
    offset: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "route": "Route-K horn-torus exterior Neumann Dirichlet-energy audit",
        "lambda_reference": bem.get("lambda_"),
        "ring_only_neumann_error": ring.get("neumann_boundary_error"),
        "bem_neumann_error": bem.get("neumann_boundary_error"),
        "ring_only_chi_K": ring.get("chi_K"),
        "bem_chi_K": bem.get("chi_K"),
        "bem_chi_cav": bem.get("chi_cav"),
        "bem_chi_E_hollow": bem.get("chi_E_hollow"),
        "ring_near_2pi_was_boundary_artifact": bool(
            ring.get("gate_neumann_pass") is False and abs(float(ring.get("residual_kinetic_to_2pi", 999))) < 0.15
        ),
        "hollow_total_2pi_falsified_if_cavitation_counts": all(bool(r.get("analytic_total_horn_falsifies_2pi")) and not bool(r.get("gate_total_2pi_pass")) for r in sweep),
        "kinetic_2pi_pass_any_sweep": any(bool(r.get("gate_kinetic_2pi_pass")) for r in sweep),
        "panel_refinement_last_rel_delta_chi_K": panel[-1].get("rel_delta_chi_K_from_previous") if panel else None,
        "volume_refinement_last_rel_delta_chi_K": volume[-1].get("rel_delta_chi_K_from_previous") if volume else None,
        "offset_probe_last_error": offset.get("offset_probe_last_error"),
        "recommended_next_status": "Use only as audit data until panel, volume, and offset-probe convergence are stable.",
    }
