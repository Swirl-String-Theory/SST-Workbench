from __future__ import annotations

import json
from dataclasses import dataclass
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
    transverse_frames,
    write_csv,
    write_json,
)


# ============================================================================
# v0.1.1 constants
# ============================================================================

OMEGA_K = (
    _config.V_SWIRL
    / (2.0 * _config.R_C)
)

DEFAULT_DEGENERACY_TOL = 1.0e-8

DEFAULT_MATCH_OVERLAP = 0.80
DEFAULT_FREQ_REL_TOL = 0.15
DEFAULT_CIRCULARITY_TOL = 0.15

ZERO_HAT_TOL = 1.0e-10
OSCILLATORY_RATIO = 1.0e-6
REAL_DOMINANT_RATIO = 1.0e-6


# ============================================================================
# Geometry helpers
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


def normalized_arclength(
    points: np.ndarray,
) -> np.ndarray:
    """
    Return periodic normalized arclength coordinates

        s_j in [0,1)

    for the N centerline nodes.
    """

    x = np.asarray(
        points,
        dtype=float,
    )

    segment = np.linalg.norm(
        np.roll(x, -1, axis=0) - x,
        axis=1,
    )

    total = float(
        np.sum(segment)
    )

    if total <= 0.0:
        raise ValueError(
            "Degenerate centerline length."
        )

    cumulative = np.concatenate(
        (
            np.array([0.0]),
            np.cumsum(segment[:-1]),
        )
    )

    return cumulative / total


def node_arclength_weights(
    points: np.ndarray,
) -> np.ndarray:
    """
    Trapezoid/Voronoi-like node weights for
    a closed polygonal centerline.

    We normalize them so sum(w)=1.
    """

    x = np.asarray(
        points,
        dtype=float,
    )

    forward = np.linalg.norm(
        np.roll(x, -1, axis=0) - x,
        axis=1,
    )

    backward = np.roll(
        forward,
        1,
    )

    weights = 0.5 * (
        forward + backward
    )

    total = float(
        np.sum(weights)
    )

    if total <= 0.0:
        raise ValueError(
            "Degenerate arclength weights."
        )

    return weights / total


# ============================================================================
# Periodic interpolation
# ============================================================================


def periodic_interp_complex(
    s_old: np.ndarray,
    values_old: np.ndarray,
    s_new: np.ndarray,
) -> np.ndarray:
    """
    Periodic linear interpolation of a complex
    field sampled on s in [0,1).

    values_old can have shape

        (N,)
        (N,k)
        (N,3)
    """

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

    if len(s_old) != len(values):
        raise ValueError(
            "s_old and values_old "
            "must have matching N."
        )

    s_ext = np.concatenate(
        (
            s_old,
            np.array([1.0]),
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
            * np.interp(
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
# Mode classification
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
    """
    Diagnostic only.

    Because the trefoil is still frozen geometry,
    "real_dominant" MUST NOT yet be interpreted
    as a physical instability.
    """

    sigma_hat = abs(
        dimensionless_growth(sigma)
    )

    omega_hat = abs(
        dimensionless_frequency(omega)
    )

    if (
        sigma_hat < ZERO_HAT_TOL
        and
        omega_hat < ZERO_HAT_TOL
    ):
        return "near_zero"

    if omega_hat > 0.0:

        ratio = (
            sigma_hat
            / max(
                omega_hat,
                1.0e-300,
            )
        )

        if ratio < OSCILLATORY_RATIO:
            return "oscillatory"

    if sigma_hat > 0.0:

        ratio = (
            omega_hat
            / max(
                sigma_hat,
                1.0e-300,
            )
        )

        if ratio < REAL_DOMINANT_RATIO:
            return "real_dominant"

    return "mixed"


def branch_sign(
    sigma: float,
    omega: float,
) -> int:

    omega_hat = (
        dimensionless_frequency(
            omega
        )
    )

    sigma_hat = (
        dimensionless_growth(
            sigma
        )
    )

    if abs(omega_hat) >= ZERO_HAT_TOL:
        return int(
            np.sign(omega_hat)
        )

    if abs(sigma_hat) >= ZERO_HAT_TOL:
        return int(
            np.sign(sigma_hat)
        )

    return 0


# ============================================================================
# Circularity operator
# ============================================================================


def circularity_value(
    vector: np.ndarray,
) -> float:
    r"""
    For coefficient ordering

        z = (u_0,v_0,u_1,v_1,...),

    calculate

            2 Im sum u* v
        C = -----------------
            sum(|u|²+|v|²).
    """

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

    if denominator == 0.0:
        return 0.0

    numerator = float(
        2.0
        * np.imag(
            np.vdot(u, v)
        )
    )

    return numerator / denominator


def circularity_apply(
    vectors: np.ndarray,
) -> np.ndarray:
    r"""
    Apply the Hermitian circularity operator H,

        H_j =
            [[0, -i],
             [i,  0]]

    to one vector or a matrix of column vectors.

    z^\dagger H z =
        2 Im sum_j u_j^* v_j.
    """

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
    r"""
    Circularity eigenvalues inside a degenerate
    eigenspace.

    This is superior to reporting arbitrary
    circularities of eigenvectors returned by
    np.linalg.eig, because those eigenvectors may
    rotate freely inside a degenerate subspace.
    """

    V = np.asarray(
        basis_vectors,
        dtype=complex,
    )

    if V.ndim != 2:
        raise ValueError(
            "basis_vectors must have shape "
            "(2N, k)."
        )

    Q, _ = np.linalg.qr(V)

    HQ = circularity_apply(Q)

    H_sub = (
        Q.conj().T @ HQ
    )

    H_sub = 0.5 * (
        H_sub
        + H_sub.conj().T
    )

    values = np.linalg.eigvalsh(
        H_sub
    )

    values = np.real(
        values
    )

    values = np.clip(
        values,
        -1.0,
        +1.0,
    )

    return np.sort(values)


# ============================================================================
# 3-D reconstruction
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
# Ring Fourier identity
# ============================================================================


def ring_fourier_label(
    q3d: np.ndarray,
    points: np.ndarray,
    *,
    max_m: int | None = None,
) -> tuple[int, float]:
    r"""
    Assign a signed dominant azimuthal harmonic m

        A_m = sum_j w_j q_j exp(-2 pi i m s_j)

    and return

        (m, power_fraction).

    This gives the ring a genuine mode identity
    independent of raw eigensolver index.
    """

    q3d = np.asarray(
        q3d,
        dtype=complex,
    )

    n = len(q3d)

    s = normalized_arclength(
        points
    )

    w = node_arclength_weights(
        points
    )

    if max_m is None:
        max_m = max(
            1,
            min(
                16,
                n // 2 - 1,
            ),
        )

    labels = list(
        range(
            -max_m,
            max_m + 1,
        )
    )

    powers = []

    for m in labels:

        phase = np.exp(
            -2j
            * np.pi
            * m
            * s
        )

        amplitude = np.sum(
            (
                w
                * phase
            )[:, None]
            * q3d,
            axis=0,
        )

        powers.append(
            float(
                np.vdot(
                    amplitude,
                    amplitude,
                ).real
            )
        )

    total = float(
        np.sum(powers)
    )

    best = int(
        np.argmax(powers)
    )

    label = labels[best]

    fraction = (
        powers[best] / total
        if total > 0.0
        else 0.0
    )

    return (
        int(label),
        float(fraction),
    )


# ============================================================================
# Solve one resolution
# ============================================================================


def solve_mode_bundle(
    geometry: str,
    n: int,
    *,
    core_factor: float = 1.0,
    force_python: bool = False,
    force_build: bool = False,
) -> dict[str, Any]:
    """
    Solve the frozen-geometry normal operator
    and retain both public diagnostics and
    internal eigenvectors.
    """

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

        # lambda = sigma - i omega
        omega = float(
            -np.imag(lam)
        )

        q3d = coefficient_to_3d(
            vector,
            e1,
            e2,
        )

        fourier_m = None
        fourier_fraction = None

        if geometry == "ring":

            (
                fourier_m,
                fourier_fraction,
            ) = ring_fourier_label(
                q3d,
                points,
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

                "fourier_m":
                    fourier_m,

                "fourier_fraction":
                    fourier_fraction,

                # internal
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
    }


# ============================================================================
# Degenerate groups
# ============================================================================


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


def group_degenerate_modes(
    bundle: dict[str, Any],
    *,
    tolerance: float = DEFAULT_DEGENERACY_TOL,
) -> list[dict[str, Any]]:
    """
    Cluster near-identical eigenvalues into
    degenerate subspaces.

    Conjugate +/-omega branches remain separate
    because their complex eigenvalues differ.
    """

    modes = bundle["modes"]

    unused = set(
        range(len(modes))
    )

    groups = []

    while unused:

        seed_index = min(unused)
        unused.remove(seed_index)

        seed = modes[seed_index]

        members = [seed]

        lam_seed_hat = (
            seed["lambda"]
            / OMEGA_K
        )

        compatible = []

        for candidate_index in list(
            unused
        ):

            candidate = modes[
                candidate_index
            ]

            if (
                candidate["branch_sign"]
                != seed["branch_sign"]
            ):
                continue

            lam_candidate_hat = (
                candidate["lambda"]
                / OMEGA_K
            )

            distance = (
                _relative_complex_distance(
                    lam_seed_hat,
                    lam_candidate_hat,
                )
            )

            if distance <= tolerance:
                compatible.append(
                    candidate_index
                )

        for candidate_index in compatible:

            unused.remove(
                candidate_index
            )

            members.append(
                modes[candidate_index]
            )

        basis = np.column_stack(
            [
                member["vector"]
                for member in members
            ]
        )

        Q, _ = np.linalg.qr(
            basis
        )

        circularity_eigs = (
            subspace_circularities(Q)
        )

        lambda_mean = np.mean(
            [
                member["lambda"]
                for member in members
            ]
        )

        sigma_mean = float(
            np.real(lambda_mean)
        )

        omega_mean = float(
            -np.imag(lambda_mean)
        )

        m_values = sorted(
            {
                int(member["fourier_m"])
                for member in members
                if member["fourier_m"]
                is not None
            }
        )

        groups.append(
            {
                "group_id":
                    len(groups),

                "member_indices":
                    [
                        int(member["index"])
                        for member in members
                    ],

                "dimension":
                    int(len(members)),

                "lambda_mean":
                    complex(lambda_mean),

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
                    circularity_eigs,

                "m_values":
                    m_values,

                # Orthonormal coefficient-space basis.
                "basis":
                    Q,
            }
        )

    return groups


# ============================================================================
# Subspace reconstruction and comparison
# ============================================================================


def group_basis_3d(
    group: dict[str, Any],
    bundle: dict[str, Any],
) -> list[np.ndarray]:

    Q = group["basis"]

    e1 = bundle["e1"]
    e2 = bundle["e2"]

    return [
        coefficient_to_3d(
            Q[:, column],
            e1,
            e2,
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

    sqrt_w = np.sqrt(
        weights
    )

    columns = []

    for field in fields:

        weighted = (
            np.asarray(
                field,
                dtype=complex,
            )
            * sqrt_w[:, None]
        )

        columns.append(
            weighted.reshape(-1)
        )

    return np.column_stack(
        columns
    )


def subspace_overlap(
    low_group: dict[str, Any],
    low_bundle: dict[str, Any],
    high_group: dict[str, Any],
    high_bundle: dict[str, Any],
) -> dict[str, Any]:
    r"""
    Compare subspaces using principal angles.

    Low-resolution modes are interpolated as
    global 3-D displacement fields onto the
    high-resolution normalized-arclength grid.

    Singular values of

        Q_low^\dagger Q_high

    are cosines of principal angles.
    """

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

    A = _weighted_flat_matrix(
        low_interp,
        high_bundle["points"],
    )

    B = _weighted_flat_matrix(
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
        0.0,
        1.0,
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

    mean_overlap = float(
        np.mean(singular_values)
        * dimension_penalty
    )

    minimum_overlap = float(
        np.min(singular_values)
        * dimension_penalty
    )

    return {
        "mean_overlap":
            mean_overlap,

        "minimum_overlap":
            minimum_overlap,

        "principal_cosines":
            singular_values,
    }


# ============================================================================
# Matching
# ============================================================================


def _relative_frequency_error(
    omega_a: float,
    omega_b: float,
) -> float:

    scale = max(
        abs(omega_a),
        abs(omega_b),
        1.0e-300,
    )

    return float(
        abs(
            abs(omega_a)
            - abs(omega_b)
        )
        / scale
    )


def _sigma_hat_difference(
    sigma_a: float,
    sigma_b: float,
) -> float:

    return float(
        abs(
            dimensionless_growth(
                sigma_a
            )
            -
            dimensionless_growth(
                sigma_b
            )
        )
    )


def _circularity_spectrum_error(
    c_a: np.ndarray,
    c_b: np.ndarray,
) -> float:

    a = np.sort(
        np.asarray(
            c_a,
            dtype=float,
        )
    )

    b = np.sort(
        np.asarray(
            c_b,
            dtype=float,
        )
    )

    if len(a) != len(b):
        return float("inf")

    return float(
        np.max(
            np.abs(a - b)
        )
    )


def match_groups(
    low_bundle: dict[str, Any],
    high_bundle: dict[str, Any],
    *,
    degeneracy_tol: float = DEFAULT_DEGENERACY_TOL,
) -> list[dict[str, Any]]:

    low_groups = (
        group_degenerate_modes(
            low_bundle,
            tolerance=degeneracy_tol,
        )
    )

    high_groups = (
        group_degenerate_modes(
            high_bundle,
            tolerance=degeneracy_tol,
        )
    )

    candidates = []

    for low in low_groups:

        for high in high_groups:

            # Compare equivalent signed branches.
            if (
                low["branch_sign"]
                != high["branch_sign"]
            ):
                continue

            overlap_data = (
                subspace_overlap(
                    low,
                    low_bundle,
                    high,
                    high_bundle,
                )
            )

            freq_rel = (
                _relative_frequency_error(
                    low["omega_mean"],
                    high["omega_mean"],
                )
            )

            # Small frequency penalty.
            score = (
                overlap_data[
                    "mean_overlap"
                ]
                -
                0.05
                * min(freq_rel, 2.0)
            )

            # Ring Fourier identity is an
            # additional positive discriminator.
            if (
                low_bundle["geometry"]
                == "ring"
                and
                low["m_values"]
                and
                high["m_values"]
            ):

                if set(
                    low["m_values"]
                ).intersection(
                    high["m_values"]
                ):
                    score += 0.05

            candidates.append(
                (
                    float(score),
                    low,
                    high,
                    overlap_data,
                    freq_rel,
                )
            )

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    used_low = set()
    used_high = set()

    matches = []

    for (
        score,
        low,
        high,
        overlap_data,
        freq_rel,
    ) in candidates:

        low_id = low["group_id"]
        high_id = high["group_id"]

        if low_id in used_low:
            continue

        if high_id in used_high:
            continue

        used_low.add(low_id)
        used_high.add(high_id)

        c_error = (
            _circularity_spectrum_error(
                low[
                    "circularity_eigs"
                ],
                high[
                    "circularity_eigs"
                ],
            )
        )

        sigma_hat_diff = (
            _sigma_hat_difference(
                low["sigma_mean"],
                high["sigma_mean"],
            )
        )

        same_dimension = (
            low["dimension"]
            == high["dimension"]
        )

        converged = bool(
            same_dimension
            and
            overlap_data[
                "mean_overlap"
            ]
            >= DEFAULT_MATCH_OVERLAP
            and
            freq_rel
            <= DEFAULT_FREQ_REL_TOL
            and
            c_error
            <= DEFAULT_CIRCULARITY_TOL
        )

        matches.append(
            {
                "low_group":
                    low_id,

                "high_group":
                    high_id,

                "low_dimension":
                    low["dimension"],

                "high_dimension":
                    high["dimension"],

                "low_members":
                    low["member_indices"],

                "high_members":
                    high["member_indices"],

                "low_m":
                    low["m_values"],

                "high_m":
                    high["m_values"],

                "low_omega":
                    low["omega_mean"],

                "high_omega":
                    high["omega_mean"],

                "low_omega_hat":
                    low["omega_hat"],

                "high_omega_hat":
                    high["omega_hat"],

                "low_sigma_hat":
                    low["sigma_hat"],

                "high_sigma_hat":
                    high["sigma_hat"],

                "low_class":
                    low["classification"],

                "high_class":
                    high["classification"],

                "overlap":
                    overlap_data[
                        "mean_overlap"
                    ],

                "minimum_overlap":
                    overlap_data[
                        "minimum_overlap"
                    ],

                "principal_cosines":
                    overlap_data[
                        "principal_cosines"
                    ],

                "frequency_rel_error":
                    freq_rel,

                "sigma_hat_abs_error":
                    sigma_hat_diff,

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

                "score":
                    score,

                "converged":
                    converged,

                # This is the hard epistemic gate.
                "physical_interpretation_allowed":
                    converged,
            }
        )

    return matches


# ============================================================================
# Public serialization
# ============================================================================


def _fmt_vector(
    values,
) -> str:

    values = np.asarray(
        values,
        dtype=float,
    )

    return ";".join(
        f"{value:.12g}"
        for value in values
    )


def _fmt_ints(
    values,
) -> str:

    return ";".join(
        str(int(value))
        for value in values
    )


def public_group_rows(
    bundle: dict[str, Any],
) -> list[dict[str, Any]]:

    groups = group_degenerate_modes(
        bundle
    )

    rows = []

    for group in groups:

        rows.append(
            {
                "group_id":
                    group["group_id"],

                "dimension":
                    group["dimension"],

                "members":
                    _fmt_ints(
                        group[
                            "member_indices"
                        ]
                    ),

                "classification":
                    group[
                        "classification"
                    ],

                "branch_sign":
                    group[
                        "branch_sign"
                    ],

                "omega_rad_s":
                    group[
                        "omega_mean"
                    ],

                "omega_hat":
                    group[
                        "omega_hat"
                    ],

                "sigma_s^-1":
                    group[
                        "sigma_mean"
                    ],

                "sigma_hat":
                    group[
                        "sigma_hat"
                    ],

                "fourier_m":
                    _fmt_ints(
                        group[
                            "m_values"
                        ]
                    ),

                "circularity_eigs":
                    _fmt_vector(
                        group[
                            "circularity_eigs"
                        ]
                    ),
            }
        )

    return rows


def public_match_rows(
    matches: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    rows = []

    for match in matches:

        rows.append(
            {
                "low_group":
                    match[
                        "low_group"
                    ],

                "high_group":
                    match[
                        "high_group"
                    ],

                "low_dimension":
                    match[
                        "low_dimension"
                    ],

                "high_dimension":
                    match[
                        "high_dimension"
                    ],

                "low_members":
                    _fmt_ints(
                        match[
                            "low_members"
                        ]
                    ),

                "high_members":
                    _fmt_ints(
                        match[
                            "high_members"
                        ]
                    ),

                "low_m":
                    _fmt_ints(
                        match["low_m"]
                    ),

                "high_m":
                    _fmt_ints(
                        match["high_m"]
                    ),

                "low_omega_hat":
                    match[
                        "low_omega_hat"
                    ],

                "high_omega_hat":
                    match[
                        "high_omega_hat"
                    ],

                "frequency_rel_error":
                    match[
                        "frequency_rel_error"
                    ],

                "low_sigma_hat":
                    match[
                        "low_sigma_hat"
                    ],

                "high_sigma_hat":
                    match[
                        "high_sigma_hat"
                    ],

                "sigma_hat_abs_error":
                    match[
                        "sigma_hat_abs_error"
                    ],

                "overlap":
                    match[
                        "overlap"
                    ],

                "minimum_overlap":
                    match[
                        "minimum_overlap"
                    ],

                "low_circularity_eigs":
                    _fmt_vector(
                        match[
                            "low_circularity_eigs"
                        ]
                    ),

                "high_circularity_eigs":
                    _fmt_vector(
                        match[
                            "high_circularity_eigs"
                        ]
                    ),

                "circularity_error":
                    match[
                        "circularity_error"
                    ],

                "low_class":
                    match[
                        "low_class"
                    ],

                "high_class":
                    match[
                        "high_class"
                    ],

                "converged":
                    match[
                        "converged"
                    ],

                "physical_interpretation_allowed":
                    match[
                        "physical_interpretation_allowed"
                    ],
            }
        )

    return rows


# ============================================================================
# Energy convergence
# ============================================================================


def energy_relative_error(
    energy_low: float,
    energy_high: float,
) -> float:

    scale = max(
        abs(energy_low),
        abs(energy_high),
        1.0e-300,
    )

    return float(
        abs(
            energy_high
            - energy_low
        )
        / scale
    )


# ============================================================================
# One resolution-pair comparison
# ============================================================================


def compare_resolutions(
    geometry: str,
    n_low: int,
    n_high: int,
    *,
    core_factor: float = 1.0,
    force_python: bool = False,
    force_build: bool = False,
) -> dict[str, Any]:

    low = solve_mode_bundle(
        geometry,
        n_low,
        core_factor=core_factor,
        force_python=force_python,
        force_build=force_build,
    )

    high = solve_mode_bundle(
        geometry,
        n_high,
        core_factor=core_factor,
        force_python=force_python,
        force_build=force_build,
    )

    matches = match_groups(
        low,
        high,
    )

    matched_count = len(matches)

    converged_count = sum(
        bool(
            match["converged"]
        )
        for match in matches
    )

    converged_fraction = (
        converged_count
        / matched_count
        if matched_count
        else 0.0
    )

    energy_rel = (
        energy_relative_error(
            low["energy"],
            high["energy"],
        )
    )

    return {
        "geometry":
            geometry,

        "N_low":
            n_low,

        "N_high":
            n_high,

        "core_factor":
            core_factor,

        "omega_K_s^-1":
            OMEGA_K,

        "energy_low":
            low["energy"],

        "energy_high":
            high["energy"],

        "energy_rel_error":
            energy_rel,

        "matched_groups":
            matched_count,

        "converged_groups":
            converged_count,

        "converged_fraction":
            converged_fraction,

        "matches":
            matches,

        # v0.1.1 deliberately distinguishes
        # implementation correctness from
        # physical readiness.
        "physical_interpretation_ready":
            bool(
                matched_count > 0
                and
                converged_fraction >= 0.80
                and
                energy_rel <= 0.05
            ),

        "_low_bundle":
            low,

        "_high_bundle":
            high,
    }


# ============================================================================
# Self-test of matcher
# ============================================================================


def matcher_self_check(
    *,
    force_python: bool = False,
    force_build: bool = False,
) -> dict[str, Any]:
    """
    Matching a resolution against itself must
    reproduce the same eigenspaces.
    """

    first = solve_mode_bundle(
        "ring",
        16,
        force_python=force_python,
        force_build=force_build,
    )

    second = solve_mode_bundle(
        "ring",
        16,
        force_python=force_python,
        force_build=False,
    )

    matches = match_groups(
        first,
        second,
    )

    if not matches:
        return {
            "ok": False,
            "reason":
                "No self-matches found.",
        }

    minimum = min(
        match["overlap"]
        for match in matches
    )

    circularity_bound_ok = all(
        np.all(
            np.abs(
                match[
                    "low_circularity_eigs"
                ]
            )
            <= 1.0 + 1.0e-12
        )
        for match in matches
    )

    ok = bool(
        minimum > 1.0 - 1.0e-9
        and
        circularity_bound_ok
    )

    return {
        "minimum_self_overlap":
            float(minimum),

        "circularity_bound_ok":
            bool(
                circularity_bound_ok
            ),

        "ok":
            ok,
    }


# ============================================================================
# Complete v0.1.1 campaign
# ============================================================================


def run_convergence_campaign(
    *,
    out_dir: str | Path = "audit_out/convergence",
    resolutions: tuple[int, ...] = (
        24,
        32,
        48,
        64,
    ),
    geometries: tuple[str, ...] = (
        "ring",
        "trefoil",
    ),
    core_factor: float = 1.0,
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

    self_check = matcher_self_check(
        force_python=force_python,
        force_build=force_build,
    )

    write_json(
        out / "matcher_self_check.json",
        self_check,
    )

    pair_summaries = []

    all_pairs = []

    for geometry in geometries:

        cache = {}

        for n in resolutions:

            bundle = solve_mode_bundle(
                geometry,
                n,
                core_factor=core_factor,
                force_python=force_python,
                force_build=force_build,
            )

            cache[n] = bundle

            write_csv(
                out
                / f"{geometry}_N{n}_mode_groups.csv",
                public_group_rows(
                    bundle
                ),
            )

        for (
            n_low,
            n_high,
        ) in zip(
            resolutions[:-1],
            resolutions[1:],
        ):

            low = cache[n_low]
            high = cache[n_high]

            matches = match_groups(
                low,
                high,
            )

            public_matches = (
                public_match_rows(
                    matches
                )
            )

            write_csv(
                out
                / (
                    f"{geometry}_"
                    f"N{n_low}_to_N{n_high}_"
                    f"group_convergence.csv"
                ),
                public_matches,
            )

            energy_rel = (
                energy_relative_error(
                    low["energy"],
                    high["energy"],
                )
            )

            converged_count = sum(
                bool(
                    match[
                        "converged"
                    ]
                )
                for match in matches
            )

            fraction = (
                converged_count
                / len(matches)
                if matches
                else 0.0
            )

            pair = {
                "geometry":
                    geometry,

                "N_low":
                    n_low,

                "N_high":
                    n_high,

                "energy_low":
                    low["energy"],

                "energy_high":
                    high["energy"],

                "energy_rel_error":
                    energy_rel,

                "matched_groups":
                    len(matches),

                "converged_groups":
                    converged_count,

                "converged_fraction":
                    fraction,

                "physical_interpretation_ready":
                    bool(
                        matches
                        and
                        fraction >= 0.80
                        and
                        energy_rel <= 0.05
                    ),
            }

            pair_summaries.append(
                pair
            )

            all_pairs.append(
                (
                    geometry,
                    n_low,
                    n_high,
                    pair,
                )
            )

    write_csv(
        out
        / "convergence_summary.csv",
        pair_summaries,
    )

    # Scientific readiness is judged on the
    # highest-resolution pair for each geometry.
    final_pairs = []

    for geometry in geometries:

        geometry_pairs = [
            pair
            for (
                g,
                _,
                _,
                pair,
            )
            in all_pairs
            if g == geometry
        ]

        if geometry_pairs:
            final_pairs.append(
                geometry_pairs[-1]
            )

    ready = bool(
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
                "v0.1.1 convergence campaign"
            ),

        "epistemic_status":
            (
                "mode-identity/convergence "
                "hardening; trefoil remains "
                "frozen geometry"
            ),

        "omega_K_s^-1":
            OMEGA_K,

        "resolutions":
            list(resolutions),

        "core_factor":
            core_factor,

        "matcher_self_check":
            self_check,

        "pairs":
            pair_summaries,

        "physical_interpretation_ready":
            ready,

        "rule":
            (
                "Only matched groups with "
                "physical_interpretation_allowed=true "
                "may be discussed as converged "
                "diagnostic modes."
            ),
    }

    write_json(
        out
        / "convergence_summary.json",
        summary,
    )

    return summary
