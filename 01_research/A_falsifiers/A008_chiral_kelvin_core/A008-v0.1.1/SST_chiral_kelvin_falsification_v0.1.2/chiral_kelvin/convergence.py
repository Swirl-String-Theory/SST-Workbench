from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from . import _config
from .core import (
    build_normal_operator,
    filament_energy,
    gamma0,
    make_ring,
    make_torus_trefoil,
    write_csv,
    write_json,
)

# ============================================================================
# v0.1.2 numerical policy
# ============================================================================

OMEGA_K = (
    _config.V_SWIRL
    / (2.0 * _config.R_C)
)

# Only genuine eigenvalue degeneracy.
TRUE_DEGENERACY_TOL = 1.0e-8

# Broader identity cluster for convergence tracking.
MATCHING_CLUSTER_TOL = 5.0e-3

DEFAULT_MATCH_OVERLAP = 0.80
DEFAULT_FREQ_REL_TOL = 0.15
DEFAULT_CIRCULARITY_TOL = 0.15
DEFAULT_FINGERPRINT_SIMILARITY = 0.85

ZERO_HAT_TOL = 1.0e-10
OSCILLATORY_RATIO = 1.0e-6
REAL_DOMINANT_RATIO = 1.0e-6

CORE_RESOLVED_MAX = 0.5
CORE_DIAGNOSTIC_MAX = 2.0

# ============================================================================
# Geometry
# ============================================================================

def make_geometry(
    geometry: str,
    n: int,
) -> np.ndarray:

    if geometry == "ring":
        return make_ring(n=n)

    if geometry == "trefoil":
        return make_torus_trefoil(n=n)

    raise ValueError(
        f"Unknown geometry: {geometry}"
    )

def segment_lengths(
    points: np.ndarray,
) -> np.ndarray:

    x = np.asarray(
        points,
        dtype=float,
    )

    return np.linalg.norm(
        np.roll(x, -1, axis=0) - x,
        axis=1,
    )

def normalized_arclength(
    points: np.ndarray,
) -> np.ndarray:

    seg = segment_lengths(points)

    total = float(
        np.sum(seg)
    )

    if total <= 0:
        raise ValueError(
            "Degenerate centerline."
        )

    cumulative = np.concatenate(
        (
            [0.0],
            np.cumsum(seg[:-1]),
        )
    )

    return cumulative / total

def node_arclength_weights(
    points: np.ndarray,
) -> np.ndarray:

    seg = segment_lengths(points)

    weights = 0.5 * (
        seg
        + np.roll(seg, 1)
    )

    total = float(
        np.sum(weights)
    )

    if total <= 0:
        raise ValueError(
            "Degenerate weights."
        )

    return weights / total

# ============================================================================
# Core resolution
# ============================================================================

def core_resolution(
    points: np.ndarray,
    core_a: float,
) -> dict[str, Any]:

    if core_a <= 0:
        raise ValueError(
            "core_a must be positive."
        )

    seg = segment_lengths(points)

    eta_max = float(
        np.max(seg)
        / core_a
    )

    eta_mean = float(
        np.mean(seg)
        / core_a
    )

    if eta_max <= CORE_RESOLVED_MAX:
        status = "RESOLVED"

    elif eta_max <= CORE_DIAGNOSTIC_MAX:
        status = "DIAGNOSTIC"

    else:
        status = "UNDERRESOLVED"

    return {
        "eta_a_max":
            eta_max,

        "eta_a_mean":
            eta_mean,

        "max_segment_m":
            float(np.max(seg)),

        "mean_segment_m":
            float(np.mean(seg)),

        "core_a_m":
            float(core_a),

        "status":
            status,

        "resolved":
            status == "RESOLVED",
    }

# ============================================================================
# Periodic interpolation
# ============================================================================

def periodic_interp_complex(
    s_old: np.ndarray,
    values_old: np.ndarray,
    s_new: np.ndarray,
) -> np.ndarray:

    s_old = np.asarray(
        s_old,
        dtype=float,
    )

    s_new = np.asarray(
        s_new,
        dtype=float,
    )

    values = np.asarray(
        values_old,
        dtype=complex,
    )

    scalar = (
        values.ndim == 1
    )

    if scalar:
        values = values[:, None]

    s_ext = np.concatenate(
        (
            s_old,
            [1.0],
        )
    )

    values_ext = np.concatenate(
        (
            values,
            values[:1],
        ),
        axis=0,
    )

    out = np.empty(
        (
            len(s_new),
            values.shape[1],
        ),
        dtype=complex,
    )

    for column in range(
        values.shape[1]
    ):

        out[:, column] = (
            np.interp(
                s_new,
                s_ext,
                np.real(
                    values_ext[:, column]
                ),
            )
            +
            1j
            *
            np.interp(
                s_new,
                s_ext,
                np.imag(
                    values_ext[:, column]
                ),
            )
        )

    if scalar:
        return out[:, 0]

    return out

# ============================================================================
# Dimensionless diagnostics
# ============================================================================

def dimensionless_frequency(
    omega: float,
) -> float:

    return float(
        omega / OMEGA_K
    )

def dimensionless_growth(
    sigma: float,
) -> float:

    return float(
        sigma / OMEGA_K
    )

def classify_mode(
    sigma: float,
    omega: float,
) -> str:

    sh = abs(
        dimensionless_growth(sigma)
    )

    wh = abs(
        dimensionless_frequency(omega)
    )

    if (
        sh < ZERO_HAT_TOL
        and
        wh < ZERO_HAT_TOL
    ):
        return "near_zero"

    if wh > 0:

        if (
            sh
            / max(
                wh,
                1e-300,
            )
            < OSCILLATORY_RATIO
        ):
            return "oscillatory"

    if sh > 0:

        if (
            wh
            / max(
                sh,
                1e-300,
            )
            < REAL_DOMINANT_RATIO
        ):
            return "real_dominant"

    return "mixed"

def branch_sign(
    sigma: float,
    omega: float,
) -> int:

    wh = dimensionless_frequency(
        omega
    )

    sh = dimensionless_growth(
        sigma
    )

    if abs(wh) >= ZERO_HAT_TOL:
        return int(
            np.sign(wh)
        )

    if abs(sh) >= ZERO_HAT_TOL:
        return int(
            np.sign(sh)
        )

    return 0

# ============================================================================
# Circularity
# ============================================================================

def circularity_value(
    vector: np.ndarray,
) -> float:

    z = np.asarray(
        vector,
        dtype=complex,
    )

    u = z[0::2]
    v = z[1::2]

    denominator = float(
        np.sum(
            np.abs(u) ** 2
            +
            np.abs(v) ** 2
        )
    )

    if denominator == 0:
        return 0.0

    return float(
        2.0
        * np.imag(
            np.vdot(u, v)
        )
        / denominator
    )

def circularity_apply(
    vectors: np.ndarray,
) -> np.ndarray:

    z = np.asarray(
        vectors,
        dtype=complex,
    )

    one_vector = (
        z.ndim == 1
    )

    if one_vector:
        z = z[:, None]

    out = np.zeros_like(z)

    out[0::2] = (
        -1j * z[1::2]
    )

    out[1::2] = (
        +1j * z[0::2]
    )

    if one_vector:
        return out[:, 0]

    return out

def subspace_circularities(
    basis_vectors: np.ndarray,
) -> np.ndarray:

    V = np.asarray(
        basis_vectors,
        dtype=complex,
    )

    Q, _ = np.linalg.qr(V)

    H_sub = (
        Q.conj().T
        @ circularity_apply(Q)
    )

    H_sub = 0.5 * (
        H_sub
        + H_sub.conj().T
    )

    values = np.real(
        np.linalg.eigvalsh(
            H_sub
        )
    )

    return np.sort(
        np.clip(
            values,
            -1.0,
            1.0,
        )
    )

# ============================================================================
# Reconstruct physical 3-D perturbation
# ============================================================================

def coefficient_to_3d(
    coefficient_vector: np.ndarray,
    e1: np.ndarray,
    e2: np.ndarray,
) -> np.ndarray:

    z = np.asarray(
        coefficient_vector,
        dtype=complex,
    )

    u = z[0::2]
    v = z[1::2]

    return (
        u[:, None] * e1
        +
        v[:, None] * e2
    )

# ============================================================================
# Fourier fingerprint
# ============================================================================

def arclength_fourier_fingerprint(
    q3d: np.ndarray,
    points: np.ndarray,
    *,
    max_m: int | None = None,
) -> np.ndarray:

    q3d = np.asarray(
        q3d,
        dtype=complex,
    )

    n = len(q3d)

    s = normalized_arclength(
        points
    )

    weights = node_arclength_weights(
        points
    )

    if max_m is None:

        max_m = max(
            1,
            min(
                24,
                n // 2 - 1,
            ),
        )

    powers = []

    for m in range(
        max_m + 1
    ):

        phase_plus = np.exp(
            -2j
            * np.pi
            * m
            * s
        )

        amp_plus = np.sum(
            (
                weights
                * phase_plus
            )[:, None]
            * q3d,
            axis=0,
        )

        power = float(
            np.vdot(
                amp_plus,
                amp_plus,
            ).real
        )

        if m > 0:

            phase_minus = np.exp(
                +2j
                * np.pi
                * m
                * s
            )

            amp_minus = np.sum(
                (
                    weights
                    * phase_minus
                )[:, None]
                * q3d,
                axis=0,
            )

            power += float(
                np.vdot(
                    amp_minus,
                    amp_minus,
                ).real
            )

        powers.append(power)

    fingerprint = np.asarray(
        powers,
        dtype=float,
    )

    total = float(
        np.sum(fingerprint)
    )

    if total > 0:
        fingerprint /= total

    return fingerprint

def fingerprint_similarity(
    a: np.ndarray,
    b: np.ndarray,
) -> float:

    a = np.asarray(
        a,
        dtype=float,
    )

    b = np.asarray(
        b,
        dtype=float,
    )

    n = min(
        len(a),
        len(b),
    )

    if n == 0:
        return 0.0

    a = a[:n]
    b = b[:n]

    denominator = float(
        np.linalg.norm(a)
        * np.linalg.norm(b)
    )

    if denominator == 0:
        return 0.0

    return float(
        np.clip(
            np.dot(a, b)
            / denominator,
            0.0,
            1.0,
        )
    )

# ============================================================================
# Eigenvalue conditioning
# ============================================================================

def eigen_condition_numbers(
    operator: np.ndarray,
    eigenvalues: np.ndarray,
    right_vectors: np.ndarray,
) -> np.ndarray:

    A = np.asarray(
        operator,
        dtype=float,
    )

    left_values, left_vectors = (
        np.linalg.eig(
            A.T
        )
    )

    used = set()

    output = np.empty(
        len(eigenvalues),
        dtype=float,
    )

    for i, lam in enumerate(
        eigenvalues
    ):

        target = np.conjugate(lam)

        order = np.argsort(
            np.abs(
                left_values
                - target
            )
        )

        selected = None

        for candidate in order:

            candidate = int(
                candidate
            )

            if candidate not in used:

                selected = candidate
                break

        if selected is None:
            selected = int(
                order[0]
            )

        used.add(selected)

        x = np.asarray(
            right_vectors[:, i],
            dtype=complex,
        )

        y = np.asarray(
            left_vectors[:, selected],
            dtype=complex,
        )

        numerator = float(
            np.linalg.norm(x)
            * np.linalg.norm(y)
        )

        denominator = float(
            abs(
                np.vdot(y, x)
            )
        )

        if denominator == 0:
            output[i] = float("inf")

        else:
            output[i] = (
                numerator
                / denominator
            )

    return output

# ============================================================================
# Solve a resolution
# ============================================================================

def solve_mode_bundle(
    geometry: str,
    n: int,
    *,
    core_factor: float = 1.0,
    force_python: bool = False,
    force_build: bool = False,
) -> dict[str, Any]:

    points = make_geometry(
        geometry,
        n,
    )

    core_a = (
        core_factor
        * _config.R_C
    )

    L, e1, e2 = (
        build_normal_operator(
            points,
            gamma=gamma0(),
            core_a=core_a,
            force_python=force_python,
            force_build=force_build,
        )
    )

    eigenvalues, eigenvectors = (
        np.linalg.eig(L)
    )

    condition_numbers = (
        eigen_condition_numbers(
            L,
            eigenvalues,
            eigenvectors,
        )
    )

    modes = []

    for index, lam in enumerate(
        eigenvalues
    ):

        vector = (
            eigenvectors[:, index]
        )

        sigma = float(
            np.real(lam)
        )

        omega = float(
            -np.imag(lam)
        )

        q3d = coefficient_to_3d(
            vector,
            e1,
            e2,
        )

        fingerprint = (
            arclength_fourier_fingerprint(
                q3d,
                points,
            )
        )

        dominant_m = int(
            np.argmax(
                fingerprint
            )
        )

        modes.append(
            {
                "index":
                    int(index),

                "lambda":
                    complex(lam),

                "sigma":
                    sigma,

                "omega":
                    omega,

                "sigma_hat":
                    dimensionless_growth(
                        sigma
                    ),

                "omega_hat":
                    dimensionless_frequency(
                        omega
                    ),

                "classification":
                    classify_mode(
                        sigma,
                        omega,
                    ),

                "branch_sign":
                    branch_sign(
                        sigma,
                        omega,
                    ),

                "circularity":
                    circularity_value(
                        vector
                    ),

                "fingerprint":
                    fingerprint,

                "dominant_m":
                    dominant_m,

                "condition_number":
                    float(
                        condition_numbers[
                            index
                        ]
                    ),

                "vector":
                    vector,

                "q3d":
                    q3d,
            }
        )

    energy = filament_energy(
        points,
        gamma=gamma0(),
        core_a=core_a,
        force_python=force_python,
        force_build=force_build,
    )

    return {
        "geometry":
            geometry,

        "N":
            n,

        "core_factor":
            core_factor,

        "core_a":
            core_a,

        "points":
            points,

        "operator":
            L,

        "e1":
            e1,

        "e2":
            e2,

        "modes":
            modes,

        "energy":
            float(energy),

        "core_resolution":
            core_resolution(
                points,
                core_a,
            ),
    }

# ============================================================================
# Near-degenerate clustering
# ============================================================================

def relative_complex_distance(
    a: complex,
    b: complex,
) -> float:

    scale = max(
        abs(a),
        abs(b),
        1e-12,
    )

    return float(
        abs(a - b)
        / scale
    )

def cluster_modes(
    bundle: dict[str, Any],
    *,
    tolerance: float,
) -> list[dict[str, Any]]:

    modes = bundle["modes"]

    unused = set(
        range(len(modes))
    )

    groups = []

    while unused:

        seed_index = min(
            unused
        )

        seed = modes[
            seed_index
        ]

        members_idx = {
            seed_index
        }

        changed = True

        while changed:

            changed = False

            candidates = list(
                unused
                - members_idx
            )

            for candidate_index in candidates:

                candidate = modes[
                    candidate_index
                ]

                if (
                    candidate[
                        "branch_sign"
                    ]
                    !=
                    seed[
                        "branch_sign"
                    ]
                ):
                    continue

                candidate_hat = (
                    candidate["lambda"]
                    / OMEGA_K
                )

                for member_index in members_idx:

                    member_hat = (
                        modes[
                            member_index
                        ]["lambda"]
                        / OMEGA_K
                    )

                    if (
                        relative_complex_distance(
                            candidate_hat,
                            member_hat,
                        )
                        <= tolerance
                    ):
                        members_idx.add(
                            candidate_index
                        )

                        changed = True
                        break

        for index in members_idx:
            unused.discard(index)

        members = [
            modes[index]
            for index
            in sorted(members_idx)
        ]

        basis = np.column_stack(
            [
                mode["vector"]
                for mode in members
            ]
        )

        Q, _ = np.linalg.qr(
            basis
        )

        lambda_mean = complex(
            np.mean(
                [
                    mode["lambda"]
                    for mode in members
                ]
            )
        )

        sigma_mean = float(
            np.real(lambda_mean)
        )

        omega_mean = float(
            -np.imag(lambda_mean)
        )

        # Only call it true degeneracy when all
        # eigenvalues satisfy the strict threshold.
        true_degenerate = all(

            relative_complex_distance(
                members[0]["lambda"]
                / OMEGA_K,

                member["lambda"]
                / OMEGA_K,
            )
            <= TRUE_DEGENERACY_TOL

            for member in members[1:]
        )

        if true_degenerate:

            circularities = (
                subspace_circularities(Q)
            )

        else:

            circularities = np.sort(
                np.asarray(
                    [
                        mode["circularity"]
                        for mode in members
                    ]
                )
            )

        fps = np.vstack(
            [
                mode["fingerprint"]
                for mode in members
            ]
        )

        fingerprint = np.mean(
            fps,
            axis=0,
        )

        fp_sum = float(
            np.sum(fingerprint)
        )

        if fp_sum > 0:
            fingerprint /= fp_sum

        conditions = np.asarray(
            [
                mode[
                    "condition_number"
                ]
                for mode in members
            ]
        )

        finite = conditions[
            np.isfinite(conditions)
        ]

        groups.append(
            {
                "group_id":
                    len(groups),

                "member_indices":
                    [
                        mode["index"]
                        for mode in members
                    ],

                "dimension":
                    len(members),

                "lambda_mean":
                    lambda_mean,

                "sigma_mean":
                    sigma_mean,

                "omega_mean":
                    omega_mean,

                "sigma_hat":
                    dimensionless_growth(
                        sigma_mean
                    ),

                "omega_hat":
                    dimensionless_frequency(
                        omega_mean
                    ),

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

                "condition_number_max":
                    (
                        float(
                            np.max(finite)
                        )
                        if len(finite)
                        else float("inf")
                    ),

                "condition_number_median":
                    (
                        float(
                            np.median(finite)
                        )
                        if len(finite)
                        else float("inf")
                    ),

                "strict_true_degeneracy":
                    true_degenerate,

                "basis":
                    Q,
            }
        )

    return groups

def group_degenerate_modes(
    bundle: dict[str, Any],
):
    return cluster_modes(
        bundle,
        tolerance=
            TRUE_DEGENERACY_TOL,
    )

def group_matching_clusters(
    bundle: dict[str, Any],
):
    return cluster_modes(
        bundle,
        tolerance=
            MATCHING_CLUSTER_TOL,
    )

# ============================================================================
# Principal-angle subspace overlap
# ============================================================================

def group_basis_3d(
    group: dict[str, Any],
    bundle: dict[str, Any],
):

    Q = group["basis"]

    return [
        coefficient_to_3d(
            Q[:, column],
            bundle["e1"],
            bundle["e2"],
        )
        for column
        in range(Q.shape[1])
    ]

def weighted_flat_matrix(
    fields,
    points,
):

    weights = (
        node_arclength_weights(
            points
        )
    )

    sqrt_w = np.sqrt(
        weights
    )

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

def subspace_overlap(
    low_group,
    low_bundle,
    high_group,
    high_bundle,
):

    low_fields = group_basis_3d(
        low_group,
        low_bundle,
    )

    high_fields = group_basis_3d(
        high_group,
        high_bundle,
    )

    s_low = normalized_arclength(
        low_bundle["points"]
    )

    s_high = normalized_arclength(
        high_bundle["points"]
    )

    low_interp = [
        periodic_interp_complex(
            s_low,
            field,
            s_high,
        )
        for field in low_fields
    ]

    A = weighted_flat_matrix(
        low_interp,
        high_bundle["points"],
    )

    B = weighted_flat_matrix(
        high_fields,
        high_bundle["points"],
    )

    QA, _ = np.linalg.qr(A)
    QB, _ = np.linalg.qr(B)

    singular_values = np.linalg.svd(
        QA.conj().T @ QB,
        compute_uv=False,
    )

    singular_values = np.clip(
        np.real(singular_values),
        0,
        1,
    )

    dimension_penalty = (
        min(
            A.shape[1],
            B.shape[1],
        )
        /
        max(
            A.shape[1],
            B.shape[1],
        )
    )

    return {
        "mean_overlap":
            float(
                np.mean(
                    singular_values
                )
                * dimension_penalty
            ),

        "minimum_overlap":
            float(
                np.min(
                    singular_values
                )
                * dimension_penalty
            ),
    }

# ============================================================================
# Matching
# ============================================================================

def relative_frequency_error(
    a: float,
    b: float,
) -> float:

    scale = max(
        abs(a),
        abs(b),
        1e-300,
    )

    return float(
        abs(
            abs(a)
            - abs(b)
        )
        / scale
    )

def circularity_error(
    a,
    b,
) -> float:

    a = np.sort(
        np.asarray(a)
    )

    b = np.sort(
        np.asarray(b)
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

def match_groups(
    low_bundle,
    high_bundle,
):

    low_groups = (
        group_matching_clusters(
            low_bundle
        )
    )

    high_groups = (
        group_matching_clusters(
            high_bundle
        )
    )

    candidates = []

    for low in low_groups:

        for high in high_groups:

            if (
                low["branch_sign"]
                != high["branch_sign"]
            ):
                continue

            overlap = subspace_overlap(
                low,
                low_bundle,
                high,
                high_bundle,
            )

            frequency_error = (
                relative_frequency_error(
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
                0.60
                * overlap["mean_overlap"]
                +
                0.25
                * fp_similarity
                +
                0.15
                * max(
                    0,
                    1
                    - min(
                        frequency_error,
                        1,
                    ),
                )
            )

            candidates.append(
                (
                    score,
                    low,
                    high,
                    overlap,
                    frequency_error,
                    fp_similarity,
                )
            )

    candidates.sort(
        key=lambda item:
            item[0],
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
        frequency_error,
        fp_similarity,
    ) in candidates:

        if (
            low["group_id"]
            in used_low
        ):
            continue

        if (
            high["group_id"]
            in used_high
        ):
            continue

        used_low.add(
            low["group_id"]
        )

        used_high.add(
            high["group_id"]
        )

        c_error = circularity_error(
            low["circularity_eigs"],
            high["circularity_eigs"],
        )

        same_dimension = (
            low["dimension"]
            ==
            high["dimension"]
        )

        numerically_trackable = bool(
            same_dimension
            and
            overlap["mean_overlap"]
            >= DEFAULT_MATCH_OVERLAP
            and
            frequency_error
            <= DEFAULT_FREQ_REL_TOL
            and
            c_error
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

        physical_allowed = bool(
            numerically_trackable
            and
            low_core == "RESOLVED"
            and
            high_core == "RESOLVED"
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

                "low_omega_hat":
                    low["omega_hat"],

                "high_omega_hat":
                    high["omega_hat"],

                "frequency_rel_error":
                    frequency_error,

                "overlap":
                    overlap[
                        "mean_overlap"
                    ],

                "minimum_overlap":
                    overlap[
                        "minimum_overlap"
                    ],

                "fingerprint_similarity":
                    fp_similarity,

                "low_dominant_m":
                    low["dominant_m"],

                "high_dominant_m":
                    high["dominant_m"],

                "low_circularity_eigs":
                    low[
                        "circularity_eigs"
                    ],

                "high_circularity_eigs":
                    high[
                        "circularity_eigs"
                    ],

                "circularity_error":
                    c_error,

                "low_condition_number_max":
                    low[
                        "condition_number_max"
                    ],

                "high_condition_number_max":
                    high[
                        "condition_number_max"
                    ],

                "low_class":
                    low["classification"],

                "high_class":
                    high["classification"],

                "low_core_status":
                    low_core,

                "high_core_status":
                    high_core,

                "score":
                    score,

                "numerically_trackable":
                    numerically_trackable,

                "physical_interpretation_allowed":
                    physical_allowed,
            }
        )

    return matches

# ============================================================================
# Output helpers
# ============================================================================

def fmt_array(
    values,
):

    return ";".join(
        f"{float(v):.12g}"
        for v in values
    )

def public_cluster_rows(
    bundle,
):

    rows = []

    for group in (
        group_matching_clusters(
            bundle
        )
    ):

        rows.append(
            {
                "cluster_id":
                    group["group_id"],

                "dimension":
                    group["dimension"],

                "members":
                    ";".join(
                        str(x)
                        for x
                        in group[
                            "member_indices"
                        ]
                    ),

                "classification":
                    group[
                        "classification"
                    ],

                "omega_hat":
                    group[
                        "omega_hat"
                    ],

                "sigma_hat":
                    group[
                        "sigma_hat"
                    ],

                "dominant_m":
                    group[
                        "dominant_m"
                    ],

                "circularity_eigs":
                    fmt_array(
                        group[
                            "circularity_eigs"
                        ]
                    ),

                "condition_number_median":
                    group[
                        "condition_number_median"
                    ],

                "condition_number_max":
                    group[
                        "condition_number_max"
                    ],

                "strict_true_degeneracy":
                    group[
                        "strict_true_degeneracy"
                    ],

                "core_eta_a_max":
                    bundle[
                        "core_resolution"
                    ][
                        "eta_a_max"
                    ],

                "core_status":
                    bundle[
                        "core_resolution"
                    ][
                        "status"
                    ],
            }
        )

    return rows

def public_match_rows(
    matches,
):

    rows = []

    for match in matches:

        rows.append(
            {
                key:
                    (
                        fmt_array(value)
                        if isinstance(
                            value,
                            np.ndarray,
                        )
                        else value
                    )

                for key, value
                in match.items()
            }
        )

    return rows

def energy_relative_error(
    low,
    high,
):

    return float(
        abs(high - low)
        /
        max(
            abs(low),
            abs(high),
            1e-300,
        )
    )

# ============================================================================
# Matcher self-check
# ============================================================================

def matcher_self_check(
    *,
    force_python=False,
    force_build=False,
):

    first = solve_mode_bundle(
        "ring",
        16,
        force_python=
            force_python,
        force_build=
            force_build,
    )

    second = solve_mode_bundle(
        "ring",
        16,
        force_python=
            force_python,
    )

    matches = match_groups(
        first,
        second,
    )

    if not matches:

        return {
            "ok": False,
            "reason":
                "No self matches.",
        }

    min_overlap = min(
        match["overlap"]
        for match in matches
    )

    min_fingerprint = min(
        match[
            "fingerprint_similarity"
        ]
        for match in matches
    )

    ok = (
        min_overlap
        > 1 - 1e-9
        and
        min_fingerprint
        > 1 - 1e-9
    )

    return {
        "minimum_self_overlap":
            float(min_overlap),

        "minimum_fingerprint_similarity":
            float(min_fingerprint),

        "ok":
            bool(ok),
    }

# ============================================================================
# Campaign
# ============================================================================

def run_convergence_campaign(
    *,
    out_dir="audit_out_v012",
    resolutions=(48, 64, 96),
    geometries=("ring", "trefoil"),
    core_factor=1.0,
    force_python=False,
    force_build=False,
):

    out = Path(out_dir)

    out.mkdir(
        parents=True,
        exist_ok=True,
    )

    self_check = (
        matcher_self_check(
            force_python=
                force_python,
            force_build=
                force_build,
        )
    )

    write_json(
        out
        / "matcher_self_check_v0.1.2.json",
        self_check,
    )

    summaries = []
    core_rows = []

    final_pairs = []

    for geometry in geometries:

        bundles = {}

        for n in resolutions:

            bundle = (
                solve_mode_bundle(
                    geometry,
                    n,
                    core_factor=
                        core_factor,
                    force_python=
                        force_python,
                    force_build=
                        force_build,
                )
            )

            bundles[n] = bundle

            resolution = (
                bundle[
                    "core_resolution"
                ]
            )

            core_rows.append(
                {
                    "geometry":
                        geometry,

                    "N":
                        n,

                    "eta_a_max":
                        resolution[
                            "eta_a_max"
                        ],

                    "eta_a_mean":
                        resolution[
                            "eta_a_mean"
                        ],

                    "status":
                        resolution[
                            "status"
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
                    bundle
                ),
            )

        geometry_pairs = []

        for (
            n_low,
            n_high,
        ) in zip(
            resolutions[:-1],
            resolutions[1:],
        ):

            low = bundles[
                n_low
            ]

            high = bundles[
                n_high
            ]

            matches = match_groups(
                low,
                high,
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

            trackable = sum(
                bool(
                    match[
                        "numerically_trackable"
                    ]
                )
                for match in matches
            )

            physical = sum(
                bool(
                    match[
                        "physical_interpretation_allowed"
                    ]
                )
                for match in matches
            )

            total = len(matches)

            track_fraction = (
                trackable / total
                if total
                else 0.0
            )

            physical_fraction = (
                physical / total
                if total
                else 0.0
            )

            pair = {
                "geometry":
                    geometry,

                "N_low":
                    n_low,

                "N_high":
                    n_high,

                "energy_rel_error":
                    energy_relative_error(
                        low["energy"],
                        high["energy"],
                    ),

                "low_core_eta_a":
                    low[
                        "core_resolution"
                    ][
                        "eta_a_max"
                    ],

                "high_core_eta_a":
                    high[
                        "core_resolution"
                    ][
                        "eta_a_max"
                    ],

                "low_core_status":
                    low[
                        "core_resolution"
                    ][
                        "status"
                    ],

                "high_core_status":
                    high[
                        "core_resolution"
                    ][
                        "status"
                    ],

                "matched_clusters":
                    total,

                "numerically_trackable_clusters":
                    trackable,

                "numerically_trackable_fraction":
                    track_fraction,

                "physical_clusters":
                    physical,

                "physical_fraction":
                    physical_fraction,

                "numerical_tracking_ready":
                    (
                        total > 0
                        and
                        track_fraction >= 0.80
                    ),

                "physical_interpretation_ready":
                    (
                        total > 0
                        and
                        physical_fraction >= 0.80
                    ),
            }

            summaries.append(pair)
            geometry_pairs.append(
                pair
            )

        if geometry_pairs:
            final_pairs.append(
                geometry_pairs[-1]
            )

    write_csv(
        out
        / "core_resolution.csv",
        core_rows,
    )

    write_csv(
        out
        / "convergence_summary_v0.1.2.csv",
        summaries,
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
            for pair
            in final_pairs
        )
    )

    physical_ready = bool(
        self_check["ok"]
        and
        final_pairs
        and
        all(
            pair[
                "physical_interpretation_ready"
            ]
            for pair
            in final_pairs
        )
    )

    result = {
        "audit_name":
            (
                "SST chiral Kelvin "
                "v0.1.2 convergence campaign"
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

        "policy":
            {
                "true_degeneracy_tol":
                    TRUE_DEGENERACY_TOL,

                "matching_cluster_tol":
                    MATCHING_CLUSTER_TOL,

                "core_resolved_eta_max":
                    CORE_RESOLVED_MAX,

                "core_diagnostic_eta_max":
                    CORE_DIAGNOSTIC_MAX,
            },

        "matcher_self_check":
            self_check,

        "pairs":
            summaries,

        "numerical_tracking_ready":
            numerical_ready,

        "physical_interpretation_ready":
            physical_ready,

        "rule":
            (
                "Physical interpretation requires "
                "numerical trackability AND "
                "RESOLVED core sampling."
            ),
    }

    write_json(
        out
        / "convergence_summary_v0.1.2.json",
        result,
    )

    return result
