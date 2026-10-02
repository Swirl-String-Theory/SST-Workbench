#!/usr/bin/env python3
"""Local identifiability diagnostics for the Q=1,2 axial-circle model."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import differential_evolution, minimize_scalar, root
from numpy.linalg import matrix_rank, svd

from nonlocal_circle import renormalized_circle


MICHELL_MIN = 1.0 / math.sqrt(3.0)
MICHELL_MAX = math.sqrt(3.0) / 2.0


@dataclass(frozen=True)
class IdentifiabilityResult:
    baseline_C: float
    baseline_g: float
    regulator: float
    thickness_radius: float
    observables: list[float]
    jacobian: list[list[float]]
    energy_only_rank: int
    energy_length_rank: int
    singular_values: list[float]
    condition_number: float
    determinant: float
    unconstrained_target_solution: list[float]
    unconstrained_target_observables: list[float]
    constrained_best_parameters: list[float]
    constrained_best_observables: list[float]
    constrained_residual_norm: float
    note: str

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def axial_energy(radius: float, C: float, g: float, Q: int, regulator: float) -> float:
    A = 1.0 + C * Q * Q
    return 2.0 * math.pi * (radius + A / radius) + g * renormalized_circle(
        radius, regulator
    )


def minimize_axial(
    C: float,
    g: float,
    Q: int,
    regulator: float,
    thickness_radius: float,
) -> tuple[float, float]:
    result = minimize_scalar(
        lambda b: axial_energy(b, C, g, Q, regulator),
        bounds=(thickness_radius, 20.0),
        method="bounded",
        options={"xatol": 1e-13},
    )
    if not result.success:
        raise RuntimeError(result.message)
    return float(result.x), float(result.fun)


def observables(
    C: float, g: float, regulator: float = 1.36, thickness_radius: float = 1.36
) -> np.ndarray:
    b1, e1 = minimize_axial(C, g, 1, regulator, thickness_radius)
    b2, e2 = minimize_axial(C, g, 2, regulator, thickness_radius)
    return np.array([e2 / e1, b2 / b1], dtype=float)


def finite_difference_jacobian(
    C: float,
    g: float,
    regulator: float,
    thickness_radius: float,
    hC: float = 1e-5,
    hg: float = 1e-5,
) -> np.ndarray:
    dC = (
        observables(C + hC, g, regulator, thickness_radius)
        - observables(C - hC, g, regulator, thickness_radius)
    ) / (2.0 * hC)
    dg = (
        observables(C, g + hg, regulator, thickness_radius)
        - observables(C, g - hg, regulator, thickness_radius)
    ) / (2.0 * hg)
    return np.column_stack((dC, dg))


def run() -> IdentifiabilityResult:
    C0, g0 = 0.85, 0.0
    regulator = thickness = 1.36
    y0 = observables(C0, g0, regulator, thickness)
    J = finite_difference_jacobian(C0, g0, regulator, thickness)
    singular = svd(J, compute_uv=False)

    target = np.array([1.63, 1.45], dtype=float)
    unconstrained = root(
        lambda x: observables(x[0], x[1], regulator, thickness) - target,
        np.array([0.8, -0.2]),
    )
    if not unconstrained.success:
        raise RuntimeError(unconstrained.message)

    def loss(x: np.ndarray) -> float:
        residual = observables(x[0], x[1], regulator, thickness) - target
        return float(residual @ residual)

    constrained = differential_evolution(
        loss,
        bounds=[(MICHELL_MIN, MICHELL_MAX), (-10.0, 10.0)],
        seed=7,
        tol=1e-11,
        polish=True,
    )

    y_un = observables(
        unconstrained.x[0], unconstrained.x[1], regulator, thickness
    )
    y_con = observables(
        constrained.x[0], constrained.x[1], regulator, thickness
    )

    return IdentifiabilityResult(
        baseline_C=C0,
        baseline_g=g0,
        regulator=regulator,
        thickness_radius=thickness,
        observables=y0.tolist(),
        jacobian=J.tolist(),
        energy_only_rank=int(matrix_rank(J[:1, :])),
        energy_length_rank=int(matrix_rank(J)),
        singular_values=singular.tolist(),
        condition_number=float(singular[0] / singular[-1]),
        determinant=float(np.linalg.det(J)),
        unconstrained_target_solution=unconstrained.x.tolist(),
        unconstrained_target_observables=y_un.tolist(),
        constrained_best_parameters=constrained.x.tolist(),
        constrained_best_observables=y_con.tolist(),
        constrained_residual_norm=float(math.sqrt(constrained.fun)),
        note=(
            "Baseline diagnostic only. The Q=1 circle is close to the active "
            "thickness constraint and the result depends on the subtraction/"
            "line-tension convention."
        ),
    )


if __name__ == "__main__":
    print(json.dumps(run().as_dict(), indent=2))
