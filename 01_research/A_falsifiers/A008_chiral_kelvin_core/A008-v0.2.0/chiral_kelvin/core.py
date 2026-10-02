from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from . import _config
from . import fallback


_NATIVE_CACHE = None
_NATIVE_ATTEMPTED = False


# ============================================================================
# I/O
# ============================================================================


def write_json(
    path: str | Path,
    data: Any,
) -> None:
    path = Path(path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        json.dumps(
            data,
            indent=2,
        ),
        encoding="utf-8",
    )


def write_csv(
    path: str | Path,
    rows: list[dict[str, Any]],
) -> None:
    path = Path(path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not rows:
        path.write_text(
            "",
            encoding="utf-8",
        )
        return

    fieldnames = list(
        rows[0].keys()
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as fh:

        writer = csv.DictWriter(
            fh,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


# ============================================================================
# Backend
# ============================================================================


def _load_cpp_backend(
    *,
    force_build: bool = False,
    build_verbose: bool = False,
):
    global _NATIVE_CACHE
    global _NATIVE_ATTEMPTED

    if (
        _NATIVE_ATTEMPTED
        and not force_build
    ):
        return _NATIVE_CACHE

    _NATIVE_ATTEMPTED = True

    try:
        from .build_ext_if_needed import (
            build_if_needed,
        )

        build_if_needed(
            force=force_build,
            verbose=build_verbose,
        )

        module = __import__(
            f"{_config.PACKAGE_NAME}."
            f"{_config.EXT_BASENAME}",
            fromlist=["*"],
        )

        _NATIVE_CACHE = module

        return module

    except Exception as exc:

        if build_verbose:
            print(
                f"{_config.LOG_PREFIX} "
                f"native unavailable: {exc}",
                file=sys.stderr,
            )

        _NATIVE_CACHE = None

        return None


# ============================================================================
# SST constants
# ============================================================================


def gamma0() -> float:
    return float(
        _config.GAMMA_0
    )


# ============================================================================
# Geometries
# ============================================================================


def make_ring(
    n: int = 32,
    radius: float | None = None,
) -> np.ndarray:
    """
    Circular validation geometry.

    A ring is the first normal-mode benchmark.
    """

    if radius is None:
        radius = (
            _config.DEFAULT_RING_RADIUS
        )

    theta = (
        2.0
        * np.pi
        * np.arange(n)
        / float(n)
    )

    return np.column_stack(
        (
            radius * np.cos(theta),
            radius * np.sin(theta),
            np.zeros(n),
        )
    )


def make_torus_trefoil(
    n: int = 32,
    major_radius: float | None = None,
    minor_radius: float | None = None,
    p: int = 2,
    q: int = 3,
) -> np.ndarray:
    """
    Exploratory torus-knot T(p,q).

    IMPORTANT:
    this is NOT an ideal-knot / SST-canonical
    equilibrium geometry.

    It is only a four-state symmetry and
    frozen-Jacobian test geometry for v0.1.0.
    """

    if major_radius is None:
        major_radius = (
            _config
            .DEFAULT_TREFOIL_MAJOR_RADIUS
        )

    if minor_radius is None:
        minor_radius = (
            _config
            .DEFAULT_TREFOIL_MINOR_RADIUS
        )

    t = (
        2.0
        * np.pi
        * np.arange(n)
        / float(n)
    )

    radial = (
        major_radius
        + minor_radius
        * np.cos(q * t)
    )

    x = (
        radial
        * np.cos(p * t)
    )

    y = (
        radial
        * np.sin(p * t)
    )

    z = (
        minor_radius
        * np.sin(q * t)
    )

    return np.column_stack(
        (x, y, z)
    )


def mirror_x(
    points: np.ndarray,
) -> np.ndarray:
    """
    Exact Euclidean mirror Q=diag(-1,1,1).
    """

    out = np.asarray(
        points,
        dtype=float,
    ).copy()

    out[:, 0] *= -1.0

    return out


# ============================================================================
# Kernels
# ============================================================================


def biot_savart_velocity(
    points: np.ndarray,
    gamma: float | None = None,
    core_a: float | None = None,
    *,
    force_python: bool = False,
    force_build: bool = False,
) -> np.ndarray:

    if gamma is None:
        gamma = gamma0()

    if core_a is None:
        core_a = (
            _config.DEFAULT_CORE_A
        )

    if not force_python:

        native = _load_cpp_backend(
            force_build=force_build,
        )

        if native is not None:

            return np.asarray(
                native.biot_savart_velocity(
                    np.asarray(
                        points,
                        dtype=float,
                    ),
                    float(gamma),
                    float(core_a),
                ),
                dtype=float,
            )

    return fallback.biot_savart_velocity(
        points,
        float(gamma),
        float(core_a),
    )


def jacobian_action(
    points: np.ndarray,
    perturbation: np.ndarray,
    gamma: float | None = None,
    core_a: float | None = None,
    *,
    force_python: bool = False,
    force_build: bool = False,
) -> np.ndarray:

    if gamma is None:
        gamma = gamma0()

    if core_a is None:
        core_a = (
            _config.DEFAULT_CORE_A
        )

    if not force_python:

        native = _load_cpp_backend(
            force_build=force_build,
        )

        if native is not None:

            return np.asarray(
                native.jacobian_action(
                    np.asarray(
                        points,
                        dtype=float,
                    ),
                    np.asarray(
                        perturbation,
                        dtype=float,
                    ),
                    float(gamma),
                    float(core_a),
                ),
                dtype=float,
            )

    return fallback.jacobian_action(
        points,
        perturbation,
        float(gamma),
        float(core_a),
    )


def filament_energy(
    points: np.ndarray,
    gamma: float | None = None,
    core_a: float | None = None,
    rho_f: float | None = None,
    *,
    force_python: bool = False,
    force_build: bool = False,
) -> float:

    if gamma is None:
        gamma = gamma0()

    if core_a is None:
        core_a = (
            _config.DEFAULT_CORE_A
        )

    if rho_f is None:
        rho_f = _config.RHO_F

    if not force_python:

        native = _load_cpp_backend(
            force_build=force_build,
        )

        if native is not None:

            return float(
                native.filament_energy(
                    np.asarray(
                        points,
                        dtype=float,
                    ),
                    float(gamma),
                    float(core_a),
                    float(rho_f),
                )
            )

    return fallback.filament_energy(
        points,
        float(gamma),
        float(core_a),
        float(rho_f),
    )


# ============================================================================
# Local transverse frames
# ============================================================================


def unit_tangents(
    points: np.ndarray,
) -> np.ndarray:

    dx = (
        fallback
        .periodic_derivative_q(
            np.asarray(
                points,
                dtype=float,
            )
        )
    )

    norm = np.linalg.norm(
        dx,
        axis=1,
    )

    if np.any(norm == 0.0):
        raise ValueError(
            "Degenerate tangent encountered."
        )

    return (
        dx
        / norm[:, None]
    )


def transverse_frames(
    points: np.ndarray,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """
    Construct an oriented local orthonormal frame

        e1 x e2 = tangent.

    The frame need not be Frenet.

    Since mode circularity is invariant under
    local SO(2) rotations of the transverse
    basis, this is sufficient for the v0.1.0
    frozen-geometry eigensystem.
    """

    tangent = unit_tangents(
        points
    )

    n = len(tangent)

    e1 = np.zeros_like(
        tangent
    )

    e2 = np.zeros_like(
        tangent
    )

    axes = np.eye(3)

    for i in range(n):

        t = tangent[i]

        # Select the global axis least aligned
        # with the local tangent.
        dots = np.abs(
            axes @ t
        )

        ref = axes[
            int(
                np.argmin(dots)
            )
        ]

        a = np.cross(
            ref,
            t,
        )

        a_norm = np.linalg.norm(a)

        if a_norm == 0.0:
            raise RuntimeError(
                "Failed to construct "
                "normal frame."
            )

        a /= a_norm

        b = np.cross(
            t,
            a,
        )

        b /= np.linalg.norm(b)

        e1[i] = a
        e2[i] = b

    return (
        tangent,
        e1,
        e2,
    )


# ============================================================================
# Normal projected Jacobian
# ============================================================================


def build_normal_operator(
    points: np.ndarray,
    gamma: float | None = None,
    core_a: float | None = None,
    *,
    force_python: bool = False,
    force_build: bool = False,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:

    x = np.asarray(
        points,
        dtype=float,
    )

    n = len(x)

    _, e1, e2 = (
        transverse_frames(x)
    )

    operator = np.zeros(
        (2 * n, 2 * n),
        dtype=float,
    )

    for j in range(n):

        for pol in range(2):

            xi = np.zeros_like(x)

            if pol == 0:
                xi[j] = e1[j]
            else:
                xi[j] = e2[j]

            response = jacobian_action(
                x,
                xi,
                gamma=gamma,
                core_a=core_a,
                force_python=force_python,
                force_build=force_build,
            )

            column = (
                2 * j
                + pol
            )

            for i in range(n):

                operator[
                    2 * i,
                    column,
                ] = np.dot(
                    response[i],
                    e1[i],
                )

                operator[
                    2 * i + 1,
                    column,
                ] = np.dot(
                    response[i],
                    e2[i],
                )

    return (
        operator,
        e1,
        e2,
    )


# ============================================================================
# Spectrum + chirality
# ============================================================================


def eigensystem(
    operator: np.ndarray,
) -> tuple[
    np.ndarray,
    np.ndarray,
]:

    eigenvalues, eigenvectors = (
        np.linalg.eig(
            np.asarray(
                operator,
                dtype=float,
            )
        )
    )

    return (
        eigenvalues,
        eigenvectors,
    )


def mode_table(
    operator: np.ndarray,
) -> list[dict[str, float | int]]:

    eigenvalues, eigenvectors = (
        eigensystem(operator)
    )

    rows = []

    for i, lam in enumerate(
        eigenvalues
    ):

        vector = (
            eigenvectors[:, i]
        )

        u = vector[0::2]
        v = vector[1::2]

        circularity = (
            fallback.mode_circularity(
                u,
                v,
            )
        )

        sigma = float(
            np.real(lam)
        )

        # Convention:
        #
        # lambda = sigma - i omega
        #
        omega = float(
            -np.imag(lam)
        )

        rows.append(
            {
                "mode": int(i),
                "sigma_s^-1": sigma,
                "omega_rad_s": omega,
                "abs_omega_rad_s": abs(omega),
                "circularity": circularity,
                "omega_times_C_s^-1":
                    omega * circularity,
            }
        )

    rows.sort(
        key=lambda row: (
            row["abs_omega_rad_s"],
            abs(row["sigma_s^-1"]),
        )
    )

    return rows


# ============================================================================
# General comparison helpers
# ============================================================================


def spectrum_set_residual(
    spectrum_a: np.ndarray,
    spectrum_b: np.ndarray,
) -> float:
    """
    Permutation-independent nearest-spectrum
    residual.

    Used only as a falsification diagnostic.
    """

    a = np.asarray(
        spectrum_a,
        dtype=complex,
    )

    b = np.asarray(
        spectrum_b,
        dtype=complex,
    )

    if len(a) != len(b):
        return float("inf")

    scale = max(
        float(
            np.max(
                np.abs(a)
            )
        ),
        float(
            np.max(
                np.abs(b)
            )
        ),
        1.0e-300,
    )

    worst = 0.0

    for value in a:

        nearest = float(
            np.min(
                np.abs(
                    value - b
                )
            )
        )

        worst = max(
            worst,
            nearest / scale,
        )

    return worst


# ============================================================================
# Falsification gates
# ============================================================================


def finite_difference_jacobian_check(
    points: np.ndarray,
    gamma: float | None = None,
    core_a: float | None = None,
    *,
    epsilon: float = 1.0e-6,
    seed: int = 12345,
    force_python: bool = False,
) -> dict[str, Any]:

    x = np.asarray(
        points,
        dtype=float,
    )

    if gamma is None:
        gamma = gamma0()

    if core_a is None:
        core_a = (
            _config.DEFAULT_CORE_A
        )

    rng = np.random.default_rng(
        seed
    )

    xi = rng.normal(
        size=x.shape
    )

    # Give perturbation the same characteristic
    # dimensional scale as the geometry.
    x_scale = max(
        np.linalg.norm(x),
        1.0e-300,
    )

    xi_scale = max(
        np.linalg.norm(xi),
        1.0e-300,
    )

    xi *= (
        x_scale
        / xi_scale
    )

    analytic = jacobian_action(
        x,
        xi,
        gamma=gamma,
        core_a=core_a,
        force_python=force_python,
    )

    plus = biot_savart_velocity(
        x + epsilon * xi,
        gamma=gamma,
        core_a=core_a,
        force_python=force_python,
    )

    minus = biot_savart_velocity(
        x - epsilon * xi,
        gamma=gamma,
        core_a=core_a,
        force_python=force_python,
    )

    finite_difference = (
        plus - minus
    ) / (
        2.0 * epsilon
    )

    denominator = max(
        np.linalg.norm(
            finite_difference
        ),
        1.0e-300,
    )

    relative_error = float(
        np.linalg.norm(
            analytic
            - finite_difference
        )
        / denominator
    )

    return {
        "epsilon": epsilon,
        "relative_error":
            relative_error,
        "threshold": 5.0e-5,
        "ok":
            relative_error < 5.0e-5,
    }


def circulation_reversal_check(
    points: np.ndarray,
    gamma: float | None = None,
    core_a: float | None = None,
    *,
    force_python: bool = False,
) -> dict[str, Any]:

    if gamma is None:
        gamma = gamma0()

    if core_a is None:
        core_a = (
            _config.DEFAULT_CORE_A
        )

    plus = biot_savart_velocity(
        points,
        +gamma,
        core_a,
        force_python=force_python,
    )

    minus = biot_savart_velocity(
        points,
        -gamma,
        core_a,
        force_python=force_python,
    )

    denominator = max(
        np.linalg.norm(plus),
        1.0e-300,
    )

    residual = float(
        np.linalg.norm(
            plus + minus
        )
        / denominator
    )

    return {
        "relative_error":
            residual,
        "threshold": 1.0e-12,
        "ok":
            residual < 1.0e-12,
    }


def four_state_energy_check(
    points: np.ndarray,
    gamma: float | None = None,
    core_a: float | None = None,
    *,
    force_python: bool = False,
) -> dict[str, Any]:

    if gamma is None:
        gamma = gamma0()

    if core_a is None:
        core_a = (
            _config.DEFAULT_CORE_A
        )

    right = np.asarray(
        points,
        dtype=float,
    )

    left = mirror_x(
        right
    )

    values = {
        "E_h+_s+":
            filament_energy(
                right,
                +gamma,
                core_a,
                force_python=force_python,
            ),

        "E_h+_s-":
            filament_energy(
                right,
                -gamma,
                core_a,
                force_python=force_python,
            ),

        "E_h-_s+":
            filament_energy(
                left,
                +gamma,
                core_a,
                force_python=force_python,
            ),

        "E_h-_s-":
            filament_energy(
                left,
                -gamma,
                core_a,
                force_python=force_python,
            ),
    }

    array = np.asarray(
        list(values.values()),
        dtype=float,
    )

    scale = max(
        float(
            np.max(
                np.abs(array)
            )
        ),
        1.0e-300,
    )

    spread = float(
        (
            np.max(array)
            - np.min(array)
        )
        / scale
    )

    # Z2 x Z2 decomposition
    O_pp = values["E_h+_s+"]
    O_pm = values["E_h+_s-"]
    O_mp = values["E_h-_s+"]
    O_mm = values["E_h-_s-"]

    O_00 = (
        O_pp + O_pm
        + O_mp + O_mm
    ) / 4.0

    O_h = (
        O_pp + O_pm
        - O_mp - O_mm
    ) / 4.0

    O_s = (
        O_pp - O_pm
        + O_mp - O_mm
    ) / 4.0

    O_hs = (
        O_pp - O_pm
        - O_mp + O_mm
    ) / 4.0

    return {
        **values,
        "relative_spread":
            spread,
        "E_00": O_00,
        "E_h": O_h,
        "E_s": O_s,
        "E_hs": O_hs,
        "threshold": 1.0e-12,
        "ok":
            spread < 1.0e-12,
    }


def spectral_symmetry_checks(
    points: np.ndarray,
    gamma: float | None = None,
    core_a: float | None = None,
    *,
    force_python: bool = False,
) -> dict[str, Any]:
    """
    Test:

        L(h,-s) = -L(h,s)

    spectrally, and parity covariance:

        spec L(-h,-s)
        =
        spec L(h,s)

    for the exact mirror geometry.
    """

    if gamma is None:
        gamma = gamma0()

    if core_a is None:
        core_a = (
            _config.DEFAULT_CORE_A
        )

    right = np.asarray(
        points,
        dtype=float,
    )

    left = mirror_x(
        right
    )

    L_pp, _, _ = (
        build_normal_operator(
            right,
            +gamma,
            core_a,
            force_python=force_python,
        )
    )

    L_pm, _, _ = (
        build_normal_operator(
            right,
            -gamma,
            core_a,
            force_python=force_python,
        )
    )

    # Physical parity partner:
    #
    # h -> -h
    # Gamma -> -Gamma
    #
    L_mm, _, _ = (
        build_normal_operator(
            left,
            -gamma,
            core_a,
            force_python=force_python,
        )
    )

    eig_pp = np.linalg.eigvals(
        L_pp
    )

    eig_pm = np.linalg.eigvals(
        L_pm
    )

    eig_mm = np.linalg.eigvals(
        L_mm
    )

    time_reversal_residual = (
        spectrum_set_residual(
            eig_pm,
            -eig_pp,
        )
    )

    parity_residual = (
        spectrum_set_residual(
            eig_mm,
            eig_pp,
        )
    )

    return {
        "circulation_spectrum_residual":
            time_reversal_residual,

        "parity_spectrum_residual":
            parity_residual,

        "threshold":
            1.0e-8,

        "ok":
            (
                time_reversal_residual
                < 1.0e-8
                and
                parity_residual
                < 1.0e-8
            ),
    }


def python_native_parity(
    points: np.ndarray,
    gamma: float | None = None,
    core_a: float | None = None,
    *,
    force_build: bool = False,
) -> dict[str, Any]:

    if gamma is None:
        gamma = gamma0()

    if core_a is None:
        core_a = (
            _config.DEFAULT_CORE_A
        )

    native = _load_cpp_backend(
        force_build=force_build,
        build_verbose=False,
    )

    if native is None:
        return {
            "available": False,
            "ok": True,
        }

    x = np.asarray(
        points,
        dtype=float,
    )

    velocity_cpp = np.asarray(
        native.biot_savart_velocity(
            x,
            gamma,
            core_a,
        ),
        dtype=float,
    )

    velocity_py = (
        fallback
        .biot_savart_velocity(
            x,
            gamma,
            core_a,
        )
    )

    velocity_scale = max(
        np.linalg.norm(
            velocity_py
        ),
        1.0e-300,
    )

    velocity_error = float(
        np.linalg.norm(
            velocity_cpp
            - velocity_py
        )
        / velocity_scale
    )

    energy_cpp = float(
        native.filament_energy(
            x,
            gamma,
            core_a,
            _config.RHO_F,
        )
    )

    energy_py = (
        fallback
        .filament_energy(
            x,
            gamma,
            core_a,
            _config.RHO_F,
        )
    )

    energy_error = float(
        abs(
            energy_cpp
            - energy_py
        )
        / max(
            abs(energy_py),
            1.0e-300,
        )
    )

    return {
        "available": True,
        "velocity_relative_error":
            velocity_error,
        "energy_relative_error":
            energy_error,
        "threshold":
            1.0e-11,
        "ok":
            (
                velocity_error
                < 1.0e-11
                and
                energy_error
                < 1.0e-11
            ),
    }


# ============================================================================
# Complete audit
# ============================================================================


def _geometry(
    name: str,
    n: int,
) -> np.ndarray:

    if name == "ring":
        return make_ring(n=n)

    if name == "trefoil":
        return make_torus_trefoil(
            n=n,
        )

    raise ValueError(
        f"Unknown geometry: {name}"
    )


def run_audit(
    *,
    geometry: str = "trefoil",
    n: int = 32,
    core_factor: float = 1.0,
    force_python: bool = False,
    force_build: bool = False,
) -> dict[str, Any]:

    points = _geometry(
        geometry,
        n,
    )

    gamma = gamma0()

    core_a = (
        core_factor
        * _config.R_C
    )

    fd = (
        finite_difference_jacobian_check(
            points,
            gamma,
            core_a,
            force_python=force_python,
        )
    )

    circulation = (
        circulation_reversal_check(
            points,
            gamma,
            core_a,
            force_python=force_python,
        )
    )

    energy = (
        four_state_energy_check(
            points,
            gamma,
            core_a,
            force_python=force_python,
        )
    )

    spectral = (
        spectral_symmetry_checks(
            points,
            gamma,
            core_a,
            force_python=force_python,
        )
    )

    native_parity = (
        python_native_parity(
            points,
            gamma,
            core_a,
            force_build=force_build,
        )
    )

    L, _, _ = (
        build_normal_operator(
            points,
            gamma,
            core_a,
            force_python=force_python,
        )
    )

    modes = mode_table(L)

    circularity_bound_ok = all(
        abs(
            float(
                row["circularity"]
            )
        )
        <= 1.0 + 1.0e-10
        for row in modes
    )

    ok = bool(
        fd["ok"]
        and circulation["ok"]
        and energy["ok"]
        and spectral["ok"]
        and native_parity["ok"]
        and circularity_bound_ok
    )

    return {
        "audit_name":
            "SST chiral Kelvin "
            "falsification v0.1.0",

        "epistemic_status":
            (
                "frozen-geometry diagnostic; "
                "not yet a relative-equilibrium "
                "trefoil spectrum"
            ),

        "geometry":
            geometry,

        "N":
            n,

        "core_factor":
            core_factor,

        "core_a_m":
            core_a,

        "r_c_m":
            _config.R_C,

        "v_swirl_m_s":
            _config.V_SWIRL,

        "rho_f_kg_m3":
            _config.RHO_F,

        "gamma0_m2_s":
            gamma,

        "finite_difference_jacobian":
            fd,

        "circulation_reversal":
            circulation,

        "four_state_energy":
            energy,

        "spectral_symmetry":
            spectral,

        "python_native_parity":
            native_parity,

        "circularity_bound_ok":
            circularity_bound_ok,

        "modes":
            modes,

        "ok":
            ok,
    }


def run_all_checks(
    *,
    out_dir: str | Path = "audit_out",
    force_python: bool = False,
    force_build: bool = False,
) -> dict[str, Any]:

    out = Path(out_dir)

    out.mkdir(
        parents=True,
        exist_ok=True,
    )

    cases = [
        ("ring", 24),
        ("ring", 32),
        ("trefoil", 24),
        ("trefoil", 32),
    ]

    summary_rows = []

    all_ok = True

    for geometry, n in cases:

        result = run_audit(
            geometry=geometry,
            n=n,
            force_python=force_python,
            force_build=force_build,
        )

        write_json(
            out
            / f"{geometry}_N{n}.json",
            result,
        )

        write_csv(
            out
            / f"{geometry}_N{n}_modes.csv",
            result["modes"],
        )

        row = {
            "geometry":
                geometry,

            "N":
                n,

            "fd_rel":
                result[
                    "finite_difference_jacobian"
                ][
                    "relative_error"
                ],

            "circulation_rel":
                result[
                    "circulation_reversal"
                ][
                    "relative_error"
                ],

            "energy_rel":
                result[
                    "four_state_energy"
                ][
                    "relative_spread"
                ],

            "spectral_time_reversal_rel":
                result[
                    "spectral_symmetry"
                ][
                    "circulation_spectrum_residual"
                ],

            "spectral_parity_rel":
                result[
                    "spectral_symmetry"
                ][
                    "parity_spectrum_residual"
                ],

            "ok":
                result["ok"],
        }

        summary_rows.append(
            row
        )

        all_ok = (
            all_ok
            and result["ok"]
        )

    write_csv(
        out / "summary.csv",
        summary_rows,
    )

    summary = {
        "audit_name":
            "SST chiral Kelvin "
            "full falsification battery",

        "gamma0_m2_s":
            gamma0(),

        "cases":
            summary_rows,

        "ok":
            bool(all_ok),
    }

    write_json(
        out / "audit_summary.json",
        summary,
    )

    return summary
