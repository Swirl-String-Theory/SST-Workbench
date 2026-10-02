from __future__ import annotations

from itertools import permutations, product
from math import gcd
from functools import reduce
import numpy as np

from .link_catalog import known_link_metadata


def _permute_matrix(matrix: np.ndarray, perm: tuple[int, ...]) -> np.ndarray:
    index = np.asarray(perm, dtype=int)
    return matrix[np.ix_(index, index)]


def component_automorphisms(
    linking_matrix_rounded: np.ndarray,
    component_lengths: list[float] | np.ndarray,
    relative_length_tolerance: float = 2.5e-3,
) -> list[tuple[int, ...]]:
    """Candidate permutations preserving coarse pair-linking and length data.

    These permutations are reported as a diagnostic proxy only. They are not used to
    quotient circulation sectors because they do not prove a geometric/topological
    automorphism of the embedded link.
    """
    matrix = np.asarray(linking_matrix_rounded, dtype=int)
    lengths = np.asarray(component_lengths, dtype=float)
    m = len(lengths)
    scale = max(float(np.mean(np.abs(lengths))), 1e-300)
    out: list[tuple[int, ...]] = []
    for perm in permutations(range(m)):
        if not np.array_equal(_permute_matrix(matrix, perm), matrix):
            continue
        if np.max(np.abs(lengths[np.asarray(perm)] - lengths)) / scale > relative_length_tolerance:
            continue
        out.append(tuple(int(x) for x in perm))
    return out or [tuple(range(m))]


def circulation_sectors(component_count: int) -> list[dict]:
    """Return every one of the 2^m circulation assignments.

    Global reversal partners are recorded but not quotiented out. This avoids silently
    identifying sectors before the physical equivalence has been established.
    """
    rows = []
    for signs in product((-1, 1), repeat=component_count):
        signs = tuple(int(x) for x in signs)
        rows.append({
            "representative": list(signs),
            "members": [list(signs)],
            "degeneracy": 1,
            "circulation_class": "co-oriented" if abs(sum(signs)) == component_count else "mixed",
            "global_reversal_partner": [int(-x) for x in signs],
            "quotient_applied": False,
        })
    return rows


def linking_form_invariants(linking_matrix_rounded: np.ndarray) -> dict:
    matrix = np.asarray(linking_matrix_rounded, dtype=int)
    eigenvalues = np.linalg.eigvalsh(matrix.astype(float))
    rank = int(np.linalg.matrix_rank(matrix.astype(float), tol=1e-12))
    offdiag = [abs(int(matrix[i, j])) for i in range(len(matrix)) for j in range(i + 1, len(matrix))]
    nonzero = [value for value in offdiag if value]
    linking_gcd = reduce(gcd, nonzero) if nonzero else 0
    return {
        "rank": rank,
        "nullity": int(len(matrix) - rank),
        "determinant": int(round(np.linalg.det(matrix))) if len(matrix) else 1,
        "eigenvalues": eigenvalues,
        "offdiagonal_gcd": int(linking_gcd),
        "total_abs_pair_linking_integer": int(sum(offdiag)),
        "all_pairwise_linking_zero": bool(not any(nonzero)),
    }


def _higher_linking_requirement(component_count: int, all_pairwise_zero: bool) -> tuple[bool, str | None, str]:
    if component_count < 2 or not all_pairwise_zero:
        return False, None, "Pairwise Gauss linking contains nonzero information or the object has fewer than two components."
    if component_count == 2:
        family = "multivariable Alexander/Conway and Sato-Levine-type information"
    elif component_count == 3:
        family = "Milnor mu-bar invariants, especially triple-linking mu-bar_123"
    else:
        family = "higher Milnor/multivariable link invariants"
    return True, family, (
        "UNRESOLVED NUMERICALLY: all pairwise Gauss-linking numbers vanish, so pairwise linking "
        f"does not identify the link. Required family: {family}."
    )


def build_topological_label_ledger(
    linking_matrix: np.ndarray,
    component_lengths: list[float] | np.ndarray,
    link_id: str | None = None,
    integer_tolerance: float = 5e-3,
    relative_length_tolerance: float = 2.5e-3,
    topology_sample_n: int | None = None,
) -> dict:
    matrix = np.asarray(linking_matrix, dtype=float)
    rounded = np.rint(matrix).astype(int)
    upper = np.triu_indices(len(matrix), 1)
    integer_error = float(np.max(np.abs(matrix[upper] - rounded[upper]))) if len(matrix) > 1 else 0.0
    automorphisms = component_automorphisms(rounded, component_lengths, relative_length_tolerance)
    sectors = circulation_sectors(len(matrix))
    form = linking_form_invariants(rounded)
    required, required_family, unresolved_status = _higher_linking_requirement(
        len(matrix), form["all_pairwise_linking_zero"]
    )
    catalog = known_link_metadata(link_id or "")
    if required and catalog.get("common_name"):
        higher_status = (
            f"[CATALOG-IDENTIFIED] {catalog['common_name']}; "
            f"{unresolved_status} The higher invariant is not numerically computed by v0.3.3."
        )
    else:
        higher_status = unresolved_status
    return {
        "link_id": link_id,
        "common_name": catalog.get("common_name"),
        "catalog_identity_status": catalog.get("identity_status"),
        "component_count": int(len(matrix)),
        "topology_sample_n": int(topology_sample_n) if topology_sample_n is not None else None,
        "linking_matrix_numeric": matrix,
        "linking_matrix_rounded": rounded,
        "linking_integer_error": integer_error,
        "integer_lock_pass": bool(integer_error <= integer_tolerance),
        "linking_form": form,
        "component_automorphisms_proxy": [list(p) for p in automorphisms],
        "component_automorphism_order_proxy": len(automorphisms),
        "automorphism_quotient_applied": False,
        "circulation_sector_orbits": sectors,
        "independent_circulation_sector_count": len(sectors),
        "all_circulation_sector_count": len(sectors),
        "higher_linking_invariant_required": bool(required),
        "higher_linking_required_family": catalog.get("higher_invariant_family") or required_family,
        "higher_linking_invariant_computed": bool(catalog.get("higher_invariant_computed", False)),
        "catalog_milnor_mu123_abs": catalog.get("catalog_milnor_mu123_abs"),
        "catalog_milnor_status": catalog.get("catalog_milnor_status"),
        "higher_linking_status": higher_status,
        "pair_linking_sector_resolved": bool(integer_error <= integer_tolerance),
        "status": (
            "[HARD NUMERICAL] integer Gauss-linking and all 2^m circulation assignments; "
            "[DIAGNOSTIC ONLY] candidate component automorphisms; no automorphism quotient applied."
        ),
    }
