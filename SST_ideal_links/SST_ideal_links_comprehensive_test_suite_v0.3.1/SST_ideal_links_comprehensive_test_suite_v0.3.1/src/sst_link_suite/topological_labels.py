from __future__ import annotations

from itertools import permutations, product
from math import gcd
from functools import reduce
import numpy as np


def _permute_matrix(matrix: np.ndarray, perm: tuple[int, ...]) -> np.ndarray:
    index = np.asarray(perm, dtype=int)
    return matrix[np.ix_(index, index)]


def component_automorphisms(
    linking_matrix_rounded: np.ndarray,
    component_lengths: list[float] | np.ndarray,
    relative_length_tolerance: float = 2.5e-3,
) -> list[tuple[int, ...]]:
    """Enumerate component permutations preserving coarse oriented link data.

    The test preserves the rounded pair-linking matrix and component lengths.  It is a
    conservative numerical automorphism proxy, not a proof of the full link symmetry group.
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


def _apply_permutation(signs: tuple[int, ...], perm: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(int(signs[index]) for index in perm)


def circulation_sector_orbits(
    component_count: int,
    automorphisms: list[tuple[int, ...]],
    identify_global_reversal: bool = True,
) -> list[dict]:
    """Quotient all ± circulation assignments by component automorphisms and reversal."""
    sectors = [tuple(int(x) for x in row) for row in product((-1, 1), repeat=component_count)]
    unseen = set(sectors)
    orbits: list[dict] = []
    while unseen:
        seed = min(unseen)
        orbit = set()
        frontier = {seed}
        while frontier:
            current = frontier.pop()
            if current in orbit:
                continue
            orbit.add(current)
            images = {_apply_permutation(current, p) for p in automorphisms}
            if identify_global_reversal:
                images |= {tuple(-x for x in image) for image in images}
            frontier |= images - orbit
        unseen -= orbit
        representative = min(orbit)
        orbits.append({
            "representative": list(representative),
            "members": [list(x) for x in sorted(orbit)],
            "degeneracy": len(orbit),
            "circulation_class": (
                "co-oriented" if abs(sum(representative)) == component_count else "mixed"
            ),
        })
    return sorted(orbits, key=lambda row: tuple(row["representative"]))


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


def build_topological_label_ledger(
    linking_matrix: np.ndarray,
    component_lengths: list[float] | np.ndarray,
    integer_tolerance: float = 5e-3,
    relative_length_tolerance: float = 2.5e-3,
) -> dict:
    matrix = np.asarray(linking_matrix, dtype=float)
    rounded = np.rint(matrix).astype(int)
    upper = np.triu_indices(len(matrix), 1)
    integer_error = float(np.max(np.abs(matrix[upper] - rounded[upper]))) if len(matrix) > 1 else 0.0
    automorphisms = component_automorphisms(rounded, component_lengths, relative_length_tolerance)
    sector_orbits = circulation_sector_orbits(len(matrix), automorphisms, True)
    form = linking_form_invariants(rounded)
    return {
        "component_count": int(len(matrix)),
        "linking_matrix_numeric": matrix,
        "linking_matrix_rounded": rounded,
        "linking_integer_error": integer_error,
        "integer_lock_pass": bool(integer_error <= integer_tolerance),
        "linking_form": form,
        "component_automorphisms": [list(p) for p in automorphisms],
        "component_automorphism_order_proxy": len(automorphisms),
        "circulation_sector_orbits": sector_orbits,
        "independent_circulation_sector_count": len(sector_orbits),
        "higher_linking_invariant_required": bool(len(matrix) >= 3 and form["all_pairwise_linking_zero"]),
        "higher_linking_status": (
            "UNRESOLVED: pairwise Gauss linking is insufficient; a Milnor/multivariable "
            "Alexander computation is required."
            if len(matrix) >= 3 and form["all_pairwise_linking_zero"]
            else "Pairwise linking data are nonzero or the link has fewer than three components."
        ),
        "status": (
            "[HARD NUMERICAL] integer Gauss-linking and circulation-sector quotient; "
            "[DIAGNOSTIC] component automorphism proxy."
        ),
    }
