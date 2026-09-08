"""
SST chiral Kelvin falsification pack v0.1.2.1.

Numerical hardening layer on top of the validated v0.1.1 solver.

This module deliberately does NOT replace the hydrodynamic kernel.
It addresses the v0.1.1 convergence result:

    implementation_ok = True
    physical_interpretation_ready = False

by adding:

* core-resolution diagnostics;
* near-degenerate subspace clustering;
* arclength Fourier fingerprints;
* left/right eigenvalue conditioning;
* subspace-level N -> N' tracking;
* separate numerical and physical interpretation gates.

The analytic torus trefoil remains FROZEN GEOMETRY.
It is therefore never promoted to a physical mode spectrum in v0.1.2.1.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .convergence import (
    OMEGA_K,
    branch_sign,
    classify_mode,
    coefficient_to_3d,
    normalized_arclength,
    node_arclength_weights,
    periodic_interp_complex,
    solve_mode_bundle,
    subspace_circularities,
)

from .core import (
    write_csv,
    write_json,
)


# ---------------------------------------------------------------------------
# v0.1.2 numerical policy
# ---------------------------------------------------------------------------

# Strict equality criterion for diagonalising circularity in a genuine
# degenerate eigenspace.
TRUE_DEGENERACY_TOL = 1.0e-8

# Broader N -> N' identity cluster.
#
# This is intentionally distinct from TRUE_DEGENERACY_TOL.  The purpose is
# to absorb small discretisation-induced eigenvalue splittings before
# comparing eigenspaces.
DEFAULT_MATCHING_CLUSTER_TOL = 1.0e-3

DEFAULT_MATCH_OVERLAP = 0.80
DEFAULT_FREQ_REL_TOL = 0.15
DEFAULT_CIRCULARITY_TOL = 0.15
DEFAULT_FINGERPRINT_SIMILARITY = 0.85

CORE_RESOLVED_MAX = 0.5
CORE_DIAGNOSTIC_MAX = 2.0

# v0.1.3 wavelength-resolution policy.
#
# PPW is an engineering convergence gate, not a theorem.
WAVELENGTH_RESOLVED_PPW = 12.0
WAVELENGTH_DIAGNOSTIC_PPW = 8.0


# ---------------------------------------------------------------------------
# Basic geometry diagnostics
# ---------------------------------------------------------------------------

def segment_lengths(points: np.ndarray) -> np.ndarray:
    x = np.asarray(points, dtype=float)
    return np.linalg.norm(
        np.roll(x, -1, axis=0) - x,
        axis=1,
    )


def core_resolution(
    points: np.ndarray,
    core_a: float,
) -> dict[str, Any]:
    r"""
    Core sampling diagnostic

        eta_a = max_j Delta s_j / a.

    Policy:

        eta_a <= 0.5  -> RESOLVED
        eta_a <= 2.0  -> DIAGNOSTIC
        otherwise     -> UNDERRESOLVED
    """

    if core_a <= 0.0:
        raise ValueError("core_a must be positive.")

    ds = segment_lengths(points)

    eta_max = float(np.max(ds) / core_a)
    eta_mean = float(np.mean(ds) / core_a)

    if eta_max <= CORE_RESOLVED_MAX:
        status = "RESOLVED"
    elif eta_max <= CORE_DIAGNOSTIC_MAX:
        status = "DIAGNOSTIC"
    else:
        status = "UNDERRESOLVED"

    return {
        "eta_a_max": eta_max,
        "eta_a_mean": eta_mean,
        "max_segment_m": float(np.max(ds)),
        "mean_segment_m": float(np.mean(ds)),
        "core_a_m": float(core_a),
        "status": status,
        "resolved": status == "RESOLVED",
    }


# ---------------------------------------------------------------------------
# Arclength Fourier fingerprints
# ---------------------------------------------------------------------------

def arclength_fourier_fingerprint(
    q3d: np.ndarray,
    points: np.ndarray,
    *,
    max_m: int | None = None,
) -> np.ndarray:
    r"""
    Geometry-independent mode fingerprint

        P_m = | int q(s) exp(-2 pi i m s/L) ds |^2.

    +/-m are folded together because this quantity is used as a mode-identity
    diagnostic rather than as the chiral observable itself.
    """

    q3d = np.asarray(q3d, dtype=complex)

    n = len(q3d)
    s = normalized_arclength(points)
    weights = node_arclength_weights(points)

    if max_m is None:
        # v0.1.2.1 used a hard m_max=24 ceiling.
        #
        # That caused high-frequency modes at N=96 to pile up
        # at the same reported dominant Fourier index.
        #
        # v0.1.3 therefore uses the full Nyquist-safe range.
        max_m = max(
            1,
            n // 2 - 1,
        )

    powers = []

    for m in range(max_m + 1):
        phase_p = np.exp(
            -2j * np.pi * m * s
        )

        amp_p = np.sum(
            (weights * phase_p)[:, None] * q3d,
            axis=0,
        )

        power = float(
            np.vdot(amp_p, amp_p).real
        )

        if m > 0:
            phase_m = np.exp(
                +2j * np.pi * m * s
            )

            amp_m = np.sum(
                (weights * phase_m)[:, None] * q3d,
                axis=0,
            )

            power += float(
                np.vdot(amp_m, amp_m).real
            )

        powers.append(power)

    fp = np.asarray(
        powers,
        dtype=float,
    )

    total = float(np.sum(fp))

    if total > 0.0:
        fp /= total

    return fp


def mode_ppw(
    n_points: int,
    dominant_m: int,
) -> float:
    r"""
    Points per dominant wavelength:

        PPW = N / m_dom.

    m=0 has no finite wavelength and is represented by +inf.
    """

    if dominant_m <= 0:
        return float("inf")

    return float(
        n_points
        / dominant_m
    )


def wavelength_resolution_status(
    ppw: float,
) -> str:

    if not np.isfinite(ppw):
        return "NOT_APPLICABLE"

    if ppw >= WAVELENGTH_RESOLVED_PPW:
        return "RESOLVED"

    if ppw >= WAVELENGTH_DIAGNOSTIC_PPW:
        return "DIAGNOSTIC"

    return "UNDERRESOLVED"


def fingerprint_similarity(
    a: np.ndarray,
    b: np.ndarray,
) -> float:
    """
    Cosine similarity between two non-negative Fourier-power vectors.
    """

    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)

    n = min(len(a), len(b))

    if n == 0:
        return 0.0

    a = a[:n]
    b = b[:n]

    denominator = float(
        np.linalg.norm(a)
        * np.linalg.norm(b)
    )

    if denominator == 0.0:
        return 0.0

    return float(
        np.clip(
            np.dot(a, b) / denominator,
            0.0,
            1.0,
        )
    )


# ---------------------------------------------------------------------------
# Left/right eigenvector conditioning
# ---------------------------------------------------------------------------

def eigen_condition_numbers(
    operator: np.ndarray,
    eigenvalues: np.ndarray,
    right_vectors: np.ndarray,
) -> np.ndarray:
    r"""
    Compute

        kappa_i =
            ||x_i|| ||y_i||
            ----------------
              |y_i^H x_i|

    where x_i and y_i are right and left eigenvectors.

    Large kappa means that a small operator perturbation may strongly rotate
    the numerical eigenvector even when the eigenvalue remains relatively
    stable.
    """

    A = np.asarray(operator)

    left_values, left_vectors = np.linalg.eig(
        A.conj().T
    )

    result = np.empty(
        len(eigenvalues),
        dtype=float,
    )

    for i, lam in enumerate(eigenvalues):
        # A^H y = conj(lambda) y.
        j = int(
            np.argmin(
                np.abs(
                    left_values
                    - np.conjugate(lam)
                )
            )
        )

        x = np.asarray(
            right_vectors[:, i],
            dtype=complex,
        )

        y = np.asarray(
            left_vectors[:, j],
            dtype=complex,
        )

        numerator = float(
            np.linalg.norm(x)
            * np.linalg.norm(y)
        )

        denominator = float(
            abs(np.vdot(y, x))
        )

        result[i] = (
            numerator / denominator
            if denominator > 0.0
            else float("inf")
        )

    return result


# ---------------------------------------------------------------------------
# Enrich v0.1.1 bundle
# ---------------------------------------------------------------------------

def solve_mode_bundle_v012(
    geometry: str,
    n: int,
    *,
    core_factor: float = 1.0,
    force_python: bool = False,
    force_build: bool = False,
) -> dict[str, Any]:

    bundle = solve_mode_bundle(
        geometry,
        n,
        core_factor=core_factor,
        force_python=force_python,
        force_build=force_build,
    )

    eigenvalues = np.asarray(
        [
            mode["lambda"]
            for mode in bundle["modes"]
        ],
        dtype=complex,
    )

    right_vectors = np.column_stack(
        [
            mode["vector"]
            for mode in bundle["modes"]
        ]
    )

    condition_numbers = eigen_condition_numbers(
        bundle["operator"],
        eigenvalues,
        right_vectors,
    )

    for i, mode in enumerate(bundle["modes"]):
        mode["fingerprint"] = (
            arclength_fourier_fingerprint(
                mode["q3d"],
                bundle["points"],
            )
        )

        mode["dominant_m"] = int(
            np.argmax(
                mode["fingerprint"]
            )
        )

        mode["ppw"] = mode_ppw(
            bundle["N"],
            mode["dominant_m"],
        )

        mode["wavelength_status"] = (
            wavelength_resolution_status(
                mode["ppw"]
            )
        )

        mode["condition_number"] = float(
            condition_numbers[i]
        )

    bundle["core_resolution"] = (
        core_resolution(
            bundle["points"],
            bundle["core_a"],
        )
    )

    # Important epistemic distinction.
    #
    # The analytic circle is a legitimate translating relative-equilibrium
    # benchmark.  The analytic torus trefoil in this release is not.
    bundle["equilibrium_status"] = (
        "relative_equilibrium_reference"
        if geometry == "ring"
        else "frozen_geometry_only"
    )

    return bundle


# ---------------------------------------------------------------------------
# Near-degenerate clusters
# ---------------------------------------------------------------------------

def _relative_complex_distance(
    a: complex,
    b: complex,
) -> float:

    scale = max(
        abs(a),
        abs(b),
        1.0e-12,
    )

    return float(
        abs(a - b) / scale
    )


def group_matching_clusters(
    bundle: dict[str, Any],
    *,
    tolerance: float = DEFAULT_MATCHING_CLUSTER_TOL,
) -> list[dict[str, Any]]:

    modes = bundle["modes"]
    unused = set(range(len(modes)))

    groups = []

    while unused:
        seed_index = min(unused)
        seed = modes[seed_index]

        members = {seed_index}

        # Transitive cluster growth.
        changed = True

        while changed:
            changed = False

            for candidate_index in list(
                unused - members
            ):
                candidate = modes[candidate_index]

                if (
                    candidate["branch_sign"]
                    != seed["branch_sign"]
                ):
                    continue

                candidate_hat = (
                    candidate["lambda"]
                    / OMEGA_K
                )

                for member_index in members:
                    member_hat = (
                        modes[member_index]["lambda"]
                        / OMEGA_K
                    )

                    if (
                        _relative_complex_distance(
                            candidate_hat,
                            member_hat,
                        )
                        <= tolerance
                    ):
                        members.add(
                            candidate_index
                        )

                        changed = True
                        break

        for index in members:
            unused.discard(index)

        selected = [
            modes[index]
            for index in sorted(members)
        ]

        basis = np.column_stack(
            [
                mode["vector"]
                for mode in selected
            ]
        )

        Q, _ = np.linalg.qr(basis)

        lambda_mean = complex(
            np.mean(
                [
                    mode["lambda"]
                    for mode in selected
                ]
            )
        )

        sigma_mean = float(
            np.real(lambda_mean)
        )

        omega_mean = float(
            -np.imag(lambda_mean)
        )

        strict_true_degeneracy = all(
            _relative_complex_distance(
                selected[0]["lambda"] / OMEGA_K,
                mode["lambda"] / OMEGA_K,
            )
            <= TRUE_DEGENERACY_TOL
            for mode in selected[1:]
        )

        if strict_true_degeneracy:
            circularities = (
                subspace_circularities(Q)
            )
        else:
            circularities = np.sort(
                np.asarray(
                    [
                        mode["circularity"]
                        for mode in selected
                    ],
                    dtype=float,
                )
            )

        fingerprints = np.vstack(
            [
                mode["fingerprint"]
                for mode in selected
            ]
        )

        fingerprint = np.mean(
            fingerprints,
            axis=0,
        )

        if np.sum(fingerprint) > 0:
            fingerprint /= np.sum(
                fingerprint
            )

        conditions = np.asarray(
            [
                mode["condition_number"]
                for mode in selected
            ],
            dtype=float,
        )

        ppw_values = np.asarray(
            [
                mode["ppw"]
                for mode in selected
            ],
            dtype=float,
        )

        finite_ppw = ppw_values[
            np.isfinite(ppw_values)
        ]

        cluster_ppw = (
            float(np.min(finite_ppw))
            if len(finite_ppw)
            else float("inf")
        )

        cluster_wavelength_status = (
            wavelength_resolution_status(
                cluster_ppw
            )
        )

        finite_conditions = conditions[
            np.isfinite(conditions)
        ]

        groups.append(
            {
                "group_id":
                    len(groups),

                "member_indices":
                    [
                        int(mode["index"])
                        for mode in selected
                    ],

                "dimension":
                    int(len(selected)),

                "lambda_mean":
                    lambda_mean,

                "sigma_mean":
                    sigma_mean,

                "omega_mean":
                    omega_mean,

                "sigma_hat":
                    sigma_mean / OMEGA_K,

                "omega_hat":
                    omega_mean / OMEGA_K,

                "classification":
                    classify_mode(
                        sigma_mean,
                        omega_mean,
                    ),

                "branch_sign":
                    branch_sign(
                        sigma_mean,
                        omega_mean,
                    ),

                "basis":
                    Q,

                "circularity_eigs":
                    circularities,

                "fingerprint":
                    fingerprint,

                "dominant_m":
                    int(
                        np.argmax(
                            fingerprint
                        )
                    ),

                "ppw":
                    cluster_ppw,

                "wavelength_status":
                    cluster_wavelength_status,

                "condition_number_median":
                    (
                        float(
                            np.median(
                                finite_conditions
                            )
                        )
                        if len(finite_conditions)
                        else float("inf")
                    ),

                "condition_number_max":
                    (
                        float(
                            np.max(
                                finite_conditions
                            )
                        )
                        if len(finite_conditions)
                        else float("inf")
                    ),

                "strict_true_degeneracy":
                    bool(
                        strict_true_degeneracy
                    ),
            }
        )

    return groups


# ---------------------------------------------------------------------------
# Principal-angle subspace matching
# ---------------------------------------------------------------------------

def _cluster_basis_3d(
    cluster: dict[str, Any],
    bundle: dict[str, Any],
) -> list[np.ndarray]:

    Q = cluster["basis"]

    return [
        coefficient_to_3d(
            Q[:, column],
            bundle["e1"],
            bundle["e2"],
        )
        for column
        in range(Q.shape[1])
    ]


def _weighted_flat_matrix(
    fields: list[np.ndarray],
    points: np.ndarray,
) -> np.ndarray:

    weights = node_arclength_weights(
        points
    )

    sqrt_w = np.sqrt(weights)

    return np.column_stack(
        [
            (
                np.asarray(
                    field,
                    dtype=complex,
                )
                * sqrt_w[:, None]
            ).reshape(-1)
            for field in fields
        ]
    )


def subspace_overlap_v012(
    low_cluster: dict[str, Any],
    low_bundle: dict[str, Any],
    high_cluster: dict[str, Any],
    high_bundle: dict[str, Any],
) -> dict[str, Any]:

    low_fields = _cluster_basis_3d(
        low_cluster,
        low_bundle,
    )

    high_fields = _cluster_basis_3d(
        high_cluster,
        high_bundle,
    )

    s_low = normalized_arclength(
        low_bundle["points"]
    )

    s_high = normalized_arclength(
        high_bundle["points"]
    )

    low_interpolated = [
        periodic_interp_complex(
            s_low,
            field,
            s_high,
        )
        for field in low_fields
    ]

    A = _weighted_flat_matrix(
        low_interpolated,
        high_bundle["points"],
    )

    B = _weighted_flat_matrix(
        high_fields,
        high_bundle["points"],
    )

    QA, _ = np.linalg.qr(A)
    QB, _ = np.linalg.qr(B)

    principal_cosines = np.linalg.svd(
        QA.conj().T @ QB,
        compute_uv=False,
    )

    principal_cosines = np.clip(
        np.real(principal_cosines),
        0.0,
        1.0,
    )

    dimension_penalty = (
        min(A.shape[1], B.shape[1])
        / max(A.shape[1], B.shape[1])
    )

    return {
        "mean_overlap":
            float(
                np.mean(principal_cosines)
                * dimension_penalty
            ),

        "minimum_overlap":
            float(
                np.min(principal_cosines)
                * dimension_penalty
            ),

        "principal_cosines":
            principal_cosines,
    }


def _relative_frequency_error(
    a: float,
    b: float,
) -> float:

    scale = max(
        abs(a),
        abs(b),
        1.0e-300,
    )

    return float(
        abs(abs(a) - abs(b))
        / scale
    )


def _circularity_error(
    a: np.ndarray,
    b: np.ndarray,
) -> float:

    a = np.sort(
        np.asarray(a, dtype=float)
    )

    b = np.sort(
        np.asarray(b, dtype=float)
    )

    if len(a) != len(b):
        return float("inf")

    if len(a) == 0:
        return 0.0

    return float(
        np.max(
            np.abs(a - b)
        )
    )


def match_clusters(
    low_bundle: dict[str, Any],
    high_bundle: dict[str, Any],
    *,
    matching_cluster_tol: float = DEFAULT_MATCHING_CLUSTER_TOL,
) -> list[dict[str, Any]]:

    low_clusters = group_matching_clusters(
        low_bundle,
        tolerance=matching_cluster_tol,
    )

    high_clusters = group_matching_clusters(
        high_bundle,
        tolerance=matching_cluster_tol,
    )

    candidates = []

    for low in low_clusters:
        for high in high_clusters:

            if (
                low["branch_sign"]
                != high["branch_sign"]
            ):
                continue

            overlap = subspace_overlap_v012(
                low,
                low_bundle,
                high,
                high_bundle,
            )

            freq_error = (
                _relative_frequency_error(
                    low["omega_mean"],
                    high["omega_mean"],
                )
            )

            fp_similarity = (
                fingerprint_similarity(
                    low["fingerprint"],
                    high["fingerprint"],
                )
            )

            score = (
                0.60 * overlap["mean_overlap"]
                + 0.25 * fp_similarity
                + 0.15
                * max(
                    0.0,
                    1.0 - min(freq_error, 1.0),
                )
            )

            candidates.append(
                (
                    score,
                    low,
                    high,
                    overlap,
                    freq_error,
                    fp_similarity,
                )
            )

    candidates.sort(
        key=lambda row: row[0],
        reverse=True,
    )

    used_low = set()
    used_high = set()

    matches = []

    for (
        score,
        low,
        high,
        overlap,
        freq_error,
        fp_similarity,
    ) in candidates:

        if low["group_id"] in used_low:
            continue

        if high["group_id"] in used_high:
            continue

        used_low.add(low["group_id"])
        used_high.add(high["group_id"])

        circ_error = _circularity_error(
            low["circularity_eigs"],
            high["circularity_eigs"],
        )

        same_dimension = (
            low["dimension"]
            == high["dimension"]
        )

        numerically_trackable = bool(
            same_dimension
            and
            overlap["mean_overlap"]
                >= DEFAULT_MATCH_OVERLAP
            and
            freq_error
                <= DEFAULT_FREQ_REL_TOL
            and
            circ_error
                <= DEFAULT_CIRCULARITY_TOL
            and
            fp_similarity
                >= DEFAULT_FINGERPRINT_SIMILARITY
        )

        low_core = (
            low_bundle[
                "core_resolution"
            ]["status"]
        )

        high_core = (
            high_bundle[
                "core_resolution"
            ]["status"]
        )

        low_wave = (
            low["wavelength_status"]
        )

        high_wave = (
            high["wavelength_status"]
        )

        # This is intentionally strict.
        #
        # v0.1.2.1 is NOT allowed to promote the frozen trefoil even if its
        # numerical spectrum converges.
        equilibrium_ready = (
            low_bundle[
                "equilibrium_status"
            ]
            == "relative_equilibrium_reference"
            and
            high_bundle[
                "equilibrium_status"
            ]
            == "relative_equilibrium_reference"
        )

        physical_allowed = bool(
            numerically_trackable
            and
            low_core == "RESOLVED"
            and
            high_core == "RESOLVED"
            and
            low_wave == "RESOLVED"
            and
            high_wave == "RESOLVED"
            and
            equilibrium_ready
        )

        matches.append(
            {
                "low_group":
                    low["group_id"],

                "high_group":
                    high["group_id"],

                "low_dimension":
                    low["dimension"],

                "high_dimension":
                    high["dimension"],

                "low_members":
                    low["member_indices"],

                "high_members":
                    high["member_indices"],

                "low_omega_hat":
                    low["omega_hat"],

                "high_omega_hat":
                    high["omega_hat"],

                "frequency_rel_error":
                    freq_error,

                "overlap":
                    overlap["mean_overlap"],

                "minimum_overlap":
                    overlap["minimum_overlap"],

                "fingerprint_similarity":
                    fp_similarity,

                "low_dominant_m":
                    low["dominant_m"],

                "high_dominant_m":
                    high["dominant_m"],

                "low_ppw":
                    low["ppw"],

                "high_ppw":
                    high["ppw"],

                "low_wavelength_status":
                    low_wave,

                "high_wavelength_status":
                    high_wave,

                "low_circularity_eigs":
                    low["circularity_eigs"],

                "high_circularity_eigs":
                    high["circularity_eigs"],

                "circularity_error":
                    circ_error,

                "low_condition_number_max":
                    low["condition_number_max"],

                "high_condition_number_max":
                    high["condition_number_max"],

                "low_class":
                    low["classification"],

                "high_class":
                    high["classification"],

                "low_core_status":
                    low_core,

                "high_core_status":
                    high_core,

                "equilibrium_ready":
                    equilibrium_ready,

                "score":
                    float(score),

                "numerically_trackable":
                    numerically_trackable,

                "physical_interpretation_allowed":
                    physical_allowed,
            }
        )

    return matches


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def _fmt_array(values) -> str:
    return ";".join(
        f"{float(value):.12g}"
        for value in values
    )


def _fmt_ints(values) -> str:
    return ";".join(
        str(int(value))
        for value in values
    )


def public_cluster_rows(
    bundle: dict[str, Any],
    *,
    tolerance: float,
) -> list[dict[str, Any]]:

    rows = []

    for cluster in group_matching_clusters(
        bundle,
        tolerance=tolerance,
    ):
        rows.append(
            {
                "cluster_id":
                    cluster["group_id"],

                "dimension":
                    cluster["dimension"],

                "members":
                    _fmt_ints(
                        cluster[
                            "member_indices"
                        ]
                    ),

                "classification":
                    cluster["classification"],

                "omega_hat":
                    cluster["omega_hat"],

                "sigma_hat":
                    cluster["sigma_hat"],

                "dominant_m":
                    cluster["dominant_m"],

                "ppw":
                    cluster["ppw"],

                "wavelength_status":
                    cluster[
                        "wavelength_status"
                    ],

                "circularity_eigs":
                    _fmt_array(
                        cluster[
                            "circularity_eigs"
                        ]
                    ),

                "condition_number_median":
                    cluster[
                        "condition_number_median"
                    ],

                "condition_number_max":
                    cluster[
                        "condition_number_max"
                    ],

                "strict_true_degeneracy":
                    cluster[
                        "strict_true_degeneracy"
                    ],

                "core_eta_a_max":
                    bundle[
                        "core_resolution"
                    ]["eta_a_max"],

                "core_status":
                    bundle[
                        "core_resolution"
                    ]["status"],

                "equilibrium_status":
                    bundle[
                        "equilibrium_status"
                    ],
            }
        )

    return rows


def public_match_rows(
    matches: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    rows = []

    for match in matches:
        row = dict(match)

        row["low_members"] = _fmt_ints(
            row["low_members"]
        )

        row["high_members"] = _fmt_ints(
            row["high_members"]
        )

        row["low_circularity_eigs"] = (
            _fmt_array(
                row[
                    "low_circularity_eigs"
                ]
            )
        )

        row["high_circularity_eigs"] = (
            _fmt_array(
                row[
                    "high_circularity_eigs"
                ]
            )
        )

        rows.append(row)

    return rows


def _energy_relative_error(
    low: float,
    high: float,
) -> float:

    return float(
        abs(high - low)
        /
        max(
            abs(low),
            abs(high),
            1.0e-300,
        )
    )


def _safe_fraction(
    numerator: int,
    denominator: int,
) -> float:
    return (
        float(numerator) / float(denominator)
        if denominator > 0
        else 0.0
    )


def _resolved_eligible(
    row: dict[str, Any],
) -> bool:
    """
    True only when both ends of a matched branch satisfy the
    explicitly adopted spatial-resolution gates.

        eta_a <= 0.5
        PPW   >= 12

    Underresolved high-m branches therefore do not dilute the
    resolved-subset convergence fraction.
    """

    return bool(
        row["low_core_status"] == "RESOLVED"
        and row["high_core_status"] == "RESOLVED"
        and row["low_wavelength_status"] == "RESOLVED"
        and row["high_wavelength_status"] == "RESOLVED"
    )


def _physical_eligible(
    row: dict[str, Any],
) -> bool:
    return bool(
        _resolved_eligible(row)
        and row["equilibrium_ready"]
    )


# ---------------------------------------------------------------------------
# Self-check
# ---------------------------------------------------------------------------

def matcher_self_check_v012(
    *,
    matching_cluster_tol:
        float = DEFAULT_MATCHING_CLUSTER_TOL,
    force_python: bool = False,
    force_build: bool = False,
) -> dict[str, Any]:

    first = solve_mode_bundle_v012(
        "ring",
        16,
        force_python=force_python,
        force_build=force_build,
    )

    second = solve_mode_bundle_v012(
        "ring",
        16,
        force_python=force_python,
        force_build=False,
    )

    matches = match_clusters(
        first,
        second,
        matching_cluster_tol=
            matching_cluster_tol,
    )

    if not matches:
        return {
            "ok": False,
            "reason": "No self matches.",
        }

    minimum_overlap = min(
        row["overlap"]
        for row in matches
    )

    minimum_fingerprint = min(
        row["fingerprint_similarity"]
        for row in matches
    )

    return {
        "minimum_self_overlap":
            float(minimum_overlap),

        "minimum_fingerprint_similarity":
            float(minimum_fingerprint),

        "ok":
            bool(
                minimum_overlap
                    > 1.0 - 1.0e-9
                and
                minimum_fingerprint
                    > 1.0 - 1.0e-9
            ),
    }


# ---------------------------------------------------------------------------
# Complete v0.1.2.1 campaign
# ---------------------------------------------------------------------------

def run_convergence_campaign_v012(
    *,
    out_dir:
        str | Path = "audit_out_v0121/convergence",
    resolutions:
        tuple[int, ...] = (48, 64, 96),
    geometries:
        tuple[str, ...] = ("ring", "trefoil"),
    core_factor: float = 1.0,
    matching_cluster_tol:
        float = DEFAULT_MATCHING_CLUSTER_TOL,
    force_python: bool = False,
    force_build: bool = False,
) -> dict[str, Any]:

    if len(resolutions) < 2:
        raise ValueError(
            "Need at least two resolutions."
        )

    out = Path(out_dir)

    out.mkdir(
        parents=True,
        exist_ok=True,
    )

    self_check = (
        matcher_self_check_v012(
            matching_cluster_tol=
                matching_cluster_tol,
            force_python=
                force_python,
            force_build=
                force_build,
        )
    )

    write_json(
        out
        / "matcher_self_check_v0.1.2.1.json",
        self_check,
    )

    pair_rows = []
    core_rows = []
    final_pairs = []

    for geometry in geometries:
        bundles = {}

        for n in resolutions:
            bundle = solve_mode_bundle_v012(
                geometry,
                n,
                core_factor=core_factor,
                force_python=force_python,
                force_build=force_build,
            )

            bundles[n] = bundle

            core = bundle[
                "core_resolution"
            ]

            core_rows.append(
                {
                    "geometry":
                        geometry,

                    "N":
                        n,

                    "eta_a_max":
                        core["eta_a_max"],

                    "eta_a_mean":
                        core["eta_a_mean"],

                    "status":
                        core["status"],

                    "equilibrium_status":
                        bundle[
                            "equilibrium_status"
                        ],
                }
            )

            write_csv(
                out
                / (
                    f"{geometry}_"
                    f"N{n}_mode_clusters.csv"
                ),
                public_cluster_rows(
                    bundle,
                    tolerance=
                        matching_cluster_tol,
                ),
            )

        geometry_pairs = []

        for n_low, n_high in zip(
            resolutions[:-1],
            resolutions[1:],
        ):
            low = bundles[n_low]
            high = bundles[n_high]

            matches = match_clusters(
                low,
                high,
                matching_cluster_tol=
                    matching_cluster_tol,
            )

            write_csv(
                out
                / (
                    f"{geometry}_"
                    f"N{n_low}_to_N{n_high}_"
                    f"cluster_convergence.csv"
                ),
                public_match_rows(
                    matches
                ),
            )

            total = len(matches)

            trackable = sum(
                bool(
                    row[
                        "numerically_trackable"
                    ]
                )
                for row in matches
            )

            resolved_eligible_count = sum(
                _resolved_eligible(row)
                for row in matches
            )

            resolved_trackable_count = sum(
                _resolved_eligible(row)
                and bool(
                    row["numerically_trackable"]
                )
                for row in matches
            )

            physical_eligible_count = sum(
                _physical_eligible(row)
                for row in matches
            )

            physical_trackable_count = sum(
                _physical_eligible(row)
                and bool(
                    row["numerically_trackable"]
                )
                for row in matches
            )

            physical = sum(
                bool(
                    row[
                        "physical_interpretation_allowed"
                    ]
                )
                for row in matches
            )

            track_fraction_all = _safe_fraction(
                trackable,
                total,
            )

            resolved_trackable_fraction = (
                _safe_fraction(
                    resolved_trackable_count,
                    resolved_eligible_count,
                )
            )

            physical_trackable_fraction = (
                _safe_fraction(
                    physical_trackable_count,
                    physical_eligible_count,
                )
            )

            physical_fraction_all = _safe_fraction(
                physical,
                total,
            )

            pair = {
                "geometry":
                    geometry,

                "N_low":
                    n_low,

                "N_high":
                    n_high,

                "energy_rel_error":
                    _energy_relative_error(
                        low["energy"],
                        high["energy"],
                    ),

                "low_core_eta_a":
                    low[
                        "core_resolution"
                    ]["eta_a_max"],

                "high_core_eta_a":
                    high[
                        "core_resolution"
                    ]["eta_a_max"],

                "low_core_status":
                    low[
                        "core_resolution"
                    ]["status"],

                "high_core_status":
                    high[
                        "core_resolution"
                    ]["status"],

                "equilibrium_status":
                    high[
                        "equilibrium_status"
                    ],

                "matched_clusters":
                    total,

                "numerically_trackable_clusters":
                    trackable,

                "numerical_tracking_fraction_all":
                    track_fraction_all,

                "numerically_trackable_fraction":
                    track_fraction_all,

                "resolved_eligible_count":
                    resolved_eligible_count,

                "resolved_trackable_count":
                    resolved_trackable_count,

                "resolved_trackable_fraction":
                    resolved_trackable_fraction,

                "physical_eligible_count":
                    physical_eligible_count,

                "physical_trackable_count":
                    physical_trackable_count,

                "physical_trackable_fraction":
                    physical_trackable_fraction,

                "physical_clusters":
                    physical,

                "physical_fraction_all":
                    physical_fraction_all,

                "physical_fraction":
                    physical_fraction_all,

                "numerical_tracking_ready":
                    bool(
                        resolved_eligible_count
                        and
                        resolved_trackable_fraction
                            >= 0.80
                    ),

                "physical_interpretation_ready":
                    bool(
                        physical_eligible_count
                        and
                        physical_trackable_fraction
                            >= 0.80
                    ),
            }

            pair_rows.append(pair)
            geometry_pairs.append(pair)

        if geometry_pairs:
            final_pairs.append(
                geometry_pairs[-1]
            )

    write_csv(
        out / "core_resolution.csv",
        core_rows,
    )

    write_csv(
        out
        / "convergence_summary_v0.1.3.1.csv",
        pair_rows,
    )

    numerical_ready = bool(
        self_check["ok"]
        and
        final_pairs
        and
        all(
            pair[
                "numerical_tracking_ready"
            ]
            for pair in final_pairs
        )
    )

    # With the frozen trefoil included this is intentionally false until
    # v0.2.0 provides a genuine relative-equilibrium solve.
    physical_ready = bool(
        self_check["ok"]
        and
        final_pairs
        and
        all(
            pair[
                "physical_interpretation_ready"
            ]
            for pair in final_pairs
        )
    )

    summary = {
        "audit_name":
            (
                "SST chiral Kelvin "
                "v0.1.3.1 convergence campaign"
            ),

        "epistemic_status":
            (
                "near-degenerate subspace "
                "convergence hardening; "
                "trefoil remains frozen geometry"
            ),

        "omega_K_s^-1":
            OMEGA_K,

        "resolutions":
            list(resolutions),

        "core_factor":
            core_factor,

        "policy":
            {
                "true_degeneracy_tol":
                    TRUE_DEGENERACY_TOL,

                "matching_cluster_tol":
                    matching_cluster_tol,

                "match_overlap_min":
                    DEFAULT_MATCH_OVERLAP,

                "frequency_rel_tol":
                    DEFAULT_FREQ_REL_TOL,

                "circularity_tol":
                    DEFAULT_CIRCULARITY_TOL,

                "fingerprint_similarity_min":
                    DEFAULT_FINGERPRINT_SIMILARITY,

                "core_resolved_eta_max":
                    CORE_RESOLVED_MAX,

                "core_diagnostic_eta_max":
                    CORE_DIAGNOSTIC_MAX,

                "wavelength_resolved_ppw_min":
                    WAVELENGTH_RESOLVED_PPW,

                "wavelength_diagnostic_ppw_min":
                    WAVELENGTH_DIAGNOSTIC_PPW,
            },

        "matcher_self_check":
            self_check,

        "pairs":
            pair_rows,

        "numerical_tracking_ready":
            numerical_ready,

        "physical_interpretation_ready":
            physical_ready,

        "rule":
            (
                "Physical interpretation requires "
                "numerical trackability, RESOLVED "
                "core sampling, RESOLVED wavelength "
                "sampling, and an established relative "
                "equilibrium."
            ),

        "fraction_semantics": {
            "numerical_tracking_fraction_all":
                (
                    "Trackable clusters divided by all "
                    "matched clusters."
                ),

            "resolved_trackable_fraction":
                (
                    "Trackable clusters divided only by "
                    "clusters satisfying both core and "
                    "wavelength resolution at both grids."
                ),

            "physical_trackable_fraction":
                (
                    "Trackable clusters divided only by "
                    "resolved clusters with an established "
                    "relative-equilibrium interpretation."
                ),
        },
    }

    write_json(
        out
        / "convergence_summary_v0.1.3.1.json",
        summary,
    )

    return summary
