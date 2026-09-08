from __future__ import annotations

import math

import numpy as np


def periodic_derivative_q(values: np.ndarray) -> np.ndarray:
    """
    Centered periodic derivative with respect to q in [0,1).

    q_j = j/N
    dq = 1/N
    """

    x = np.asarray(values, dtype=float)

    if x.ndim != 2 or x.shape[1] != 3:
        raise ValueError("Expected shape (N, 3).")

    n = len(x)

    if n < 4:
        raise ValueError("Need at least four points.")

    dq = 1.0 / float(n)

    return (
        np.roll(x, -1, axis=0)
        - np.roll(x, +1, axis=0)
    ) / (2.0 * dq)


def biot_savart_velocity(
    points: np.ndarray,
    gamma: float,
    core_a: float,
) -> np.ndarray:
    r"""
    Regularized finite-core Biot-Savart velocity.

    V(q) =
        Gamma/(4 pi)
        integral
            X'(q') x [X(q)-X(q')]
            -------------------------------- dq'
            (|X(q)-X(q')|^2 + a^2)^(3/2)

    Uniform periodic q discretization.
    """

    x = np.asarray(points, dtype=float)

    n = len(x)
    dq = 1.0 / float(n)

    tangent_q = periodic_derivative_q(x)

    out = np.zeros_like(x)

    prefactor = gamma / (4.0 * math.pi)

    for i in range(n):

        r = x[i] - x

        d = np.sum(r * r, axis=1) + core_a * core_a

        numerator = np.cross(tangent_q, r)

        kernel = numerator / d[:, None] ** 1.5

        out[i] = (
            prefactor
            * np.sum(kernel, axis=0)
            * dq
        )

    return out


def jacobian_action(
    points: np.ndarray,
    perturbation: np.ndarray,
    gamma: float,
    core_a: float,
) -> np.ndarray:
    r"""
    Analytic Frechet derivative of the same regularized
    Biot-Savart operator.

    Let

        R     = X(q) - X(q')
        dR    = xi(q) - xi(q')
        D     = |R|^2 + a^2

    Then

    delta V =
        Gamma/(4 pi) integral [

            xi'(q') x R / D^(3/2)

          + X'(q') x dR / D^(3/2)

          - 3 (R.dR)
              [X'(q') x R]
              / D^(5/2)

        ] dq'.
    """

    x = np.asarray(points, dtype=float)
    xi = np.asarray(perturbation, dtype=float)

    if x.shape != xi.shape:
        raise ValueError("points and perturbation must have same shape.")

    n = len(x)
    dq = 1.0 / float(n)

    dx = periodic_derivative_q(x)
    dxi = periodic_derivative_q(xi)

    out = np.zeros_like(x)

    prefactor = gamma / (4.0 * math.pi)

    for i in range(n):

        r = x[i] - x
        dr = xi[i] - xi

        d = np.sum(r * r, axis=1) + core_a * core_a

        term_1 = (
            np.cross(dxi, r)
            / d[:, None] ** 1.5
        )

        term_2 = (
            np.cross(dx, dr)
            / d[:, None] ** 1.5
        )

        dot_r_dr = np.sum(r * dr, axis=1)

        base_cross = np.cross(dx, r)

        term_3 = (
            -3.0
            * dot_r_dr[:, None]
            * base_cross
            / d[:, None] ** 2.5
        )

        out[i] = (
            prefactor
            * np.sum(
                term_1 + term_2 + term_3,
                axis=0,
            )
            * dq
        )

    return out


def filament_energy(
    points: np.ndarray,
    gamma: float,
    core_a: float,
    rho_f: float,
) -> float:
    r"""
    Regularized filament kinetic-energy proxy.

    E =
        rho_f Gamma^2 /(8 pi)
        double integral

          X'(q).X'(q')
        -------------------- dq dq'
        sqrt(|X-X'|^2+a^2)

    The exact finite-core energy depends on the chosen core model.
    This expression is used as the symmetry/null baseline.

    Important consequence:

        E(Gamma) = E(-Gamma)

    and exact mirror geometries have identical E.
    """

    x = np.asarray(points, dtype=float)

    n = len(x)
    dq = 1.0 / float(n)

    dx = periodic_derivative_q(x)

    total = 0.0

    for i in range(n):

        r = x[i] - x

        denominator = np.sqrt(
            np.sum(r * r, axis=1)
            + core_a * core_a
        )

        dot_products = dx @ dx[i]

        total += np.sum(
            dot_products / denominator
        )

    return float(
        rho_f
        * gamma * gamma
        * total
        * dq * dq
        / (8.0 * math.pi)
    )


def mode_circularity(
    u: np.ndarray,
    v: np.ndarray,
) -> float:
    r"""
    Dimensionless Kelvin-mode circularity

                    2 Im sum(u* v)
        C = --------------------------------
            sum(|u|^2 + |v|^2)

    with

        -1 <= C <= +1.

    C =  0 : linearly polarized / achiral transverse motion
    C = +1 : one circular polarization
    C = -1 : opposite circular polarization
    """

    u = np.asarray(u, dtype=complex)
    v = np.asarray(v, dtype=complex)

    denominator = np.sum(
        np.abs(u) ** 2
        + np.abs(v) ** 2
    )

    if denominator == 0.0:
        return 0.0

    numerator = (
        2.0
        * np.imag(
            np.vdot(u, v)
        )
    )

    value = float(
        numerator / denominator
    )

    # Numerical protection only.
    if value > 1.0 and value < 1.0 + 1e-12:
        value = 1.0

    if value < -1.0 and value > -1.0 - 1e-12:
        value = -1.0

    return value
