from __future__ import annotations
import numpy as np
from dataclasses import replace
from .models import FourierComponent, IdealLink
from .fourier import sample_component
from .geometry import component_geometry

# Acceptance gates for ideal-knot / ideal-link input records.
#
# Motivation.  v0.2.0 reported curvature, bending and torsion statistics
# without ever checking that the declared tube diameter D is compatible with
# the reconstructed centreline.  In the v0.2.0 full run every one of the 129
# completed links had max_curvature_Dinv > 2, i.e. the declared thickness was
# not attainable, yet nothing in the pipeline flagged it.  The overshoot is
# dominated by high-mode ringing in the truncated Fourier representation
# (see curvature_mode_convergence), so the affected columns are properties of
# the representation rather than of the underlying tight configuration.


def _truncate(component: FourierComponent, n_max: int) -> FourierComponent:
    keep = min(int(n_max) + 1, component.A.shape[0])
    return replace(component, A=component.A[:keep].copy(), B=component.B[:keep].copy())


def _arclength_and_length(r: np.ndarray) -> tuple[np.ndarray, float]:
    seg = np.linalg.norm(np.diff(r, axis=0, append=r[:1]), axis=1)
    return np.concatenate(([0.0], np.cumsum(seg)[:-1])), float(seg.sum())


def nonlocal_self_min_distance(r: np.ndarray, window: float) -> float:
    """Minimum distance between points separated by more than `window` in arclength."""
    arc, total = _arclength_and_length(r)
    d = np.linalg.norm(r[:, None, :] - r[None, :, :], axis=2)
    sep = np.abs(arc[:, None] - arc[None, :])
    sep = np.minimum(sep, total - sep)
    d[sep <= min(window, total / 2.5)] = np.inf
    finite = np.isfinite(d)
    return float(d[finite].min()) if finite.any() else float("inf")


def thickness_gate(
    component_results: list[dict],
    contacts: dict,
    diameter: float,
    tolerance: float = 1e-3,
) -> dict:
    """Is the declared diameter D attainable by the reconstructed centreline?

    Three constraints, all in units of D:
      curvature   a <= 1 / kappa_max
      self-contact  a <= dcsd_self / 2
      mutual contact a <= dcsd_mutual / 2
    with a = D / 2 the tube radius.  D_allowed = 2 * min(...).
    """
    kappa_max = max(x["curvature_max_Dinv"] for x in component_results)
    self_min = min(
        (x["sampled_nonlocal_min_distance_D"] for x in contacts.get("self_components", [])),
        default=float("inf"),
    )
    mutual_min = min(
        (x["refined_min_distance_D"] for x in contacts.get("mutual_pairs", [])),
        default=float("inf"),
    )
    a_curv = 1.0 / max(kappa_max, 1e-30)
    a_self = 0.5 * self_min
    a_mutual = 0.5 * mutual_min
    a_allowed = min(a_curv, a_self, a_mutual)
    d_allowed = 2.0 * a_allowed
    binding = min(
        (("curvature", a_curv), ("self_contact", a_self), ("mutual_contact", a_mutual)),
        key=lambda kv: kv[1],
    )[0]
    over = max(
        (x.get("arclength_fraction_over_curvature_bound", 0.0) for x in component_results),
        default=0.0,
    )
    return {
        "declared_diameter_D": float(diameter),
        "allowed_diameter_D": float(d_allowed),
        "diameter_deficit_ratio": float(d_allowed / max(diameter, 1e-30)),
        "binding_constraint": binding,
        "kappa_max_Dinv": float(kappa_max),
        "nonlocal_self_min_D": float(self_min),
        "mutual_min_D": float(mutual_min),
        "max_arclength_fraction_over_curvature_bound": float(over),
        "curvature_spectral_tail_fraction": float(
            max((x.get("curvature_spectral_tail_fraction", 0.0) for x in component_results), default=0.0)
        ),
        "passes": bool(d_allowed >= diameter * (1.0 - tolerance)),
    }


def curvature_mode_convergence(
    link: IdealLink,
    cutoffs: list[int] | tuple[int, ...] = (12, 20, 30, 50, 100),
    n: int = 4096,
) -> dict:
    """Max curvature and bending integral as a function of the mode cutoff.

    If kappa_max collapses towards the thickness bound as high modes are
    removed, the overshoot in the full record is truncation ringing and the
    curvature columns of the untruncated record must not be interpreted as
    geometric properties.
    """
    rows = []
    full_max = max(int(c.A.shape[0]) - 1 for c in link.components)
    for n_max in list(cutoffs) + [full_max]:
        kappa, bending, length = 0.0, 0.0, 0.0
        for component in link.components:
            sample = sample_component(_truncate(component, n_max), n)
            geo = component_geometry(sample, link.diameter)
            kappa = max(kappa, geo["curvature_max_Dinv"])
            bending += geo["bending_integral_Dinv"]
            length += geo["numerical_length_D"]
        rows.append({
            "n_max": int(n_max),
            "max_curvature_Dinv": float(kappa),
            "khat_max": float(kappa * link.diameter),
            "total_bending_integral_Dinv": float(bending),
            "total_length_D": float(length),
            "within_thickness_bound": bool(kappa * link.diameter <= 2.0),
        })
    converged = [r["n_max"] for r in rows if r["within_thickness_bound"]]
    return {
        "rows": rows,
        "largest_cutoff_within_bound": int(max(converged)) if converged else None,
        "full_record_within_bound": bool(rows[-1]["within_thickness_bound"]),
    }
