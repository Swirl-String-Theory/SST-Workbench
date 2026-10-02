#!/usr/bin/env python3
"""Analytic and numerical circle values for the signed soft-core kernel."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.integrate import quad
from scipy.special import ellipk, ellipe


@dataclass(frozen=True)
class CircleResult:
    radius: float
    regulator: float
    subtraction_range: float
    raw_analytic: float
    raw_quadrature: float
    renormalized_analytic: float
    relative_error: float

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def raw_circle(radius: float, regulator: float) -> float:
    b = float(radius)
    a = float(regulator)
    if b <= 0.0 or a <= 0.0:
        raise ValueError("radius and regulator must be positive")
    A = a * a + 4.0 * b * b
    m = 4.0 * b * b / A
    return (
        2.0
        * math.pi
        / math.sqrt(A)
        * ((a * a + 2.0 * b * b) * ellipk(m) - A * ellipe(m))
    )


def raw_circle_quadrature(radius: float, regulator: float) -> float:
    b = float(radius)
    a = float(regulator)

    def integrand(delta: float) -> float:
        return (
            math.cos(delta)
            / math.sqrt(a * a + 4.0 * b * b * math.sin(delta / 2.0) ** 2)
        )

    value, _ = quad(integrand, 0.0, 2.0 * math.pi, epsabs=1e-12, epsrel=1e-12)
    return math.pi * b * b * value


def local_subtraction(
    radius: float, regulator: float, subtraction_range: float | None = None
) -> float:
    b = float(radius)
    a = float(regulator)
    L = 2.0 * math.pi * b
    ell = L / 2.0 if subtraction_range is None else float(subtraction_range)
    if not (0.0 < ell <= L / 2.0):
        raise ValueError("subtraction_range must lie in (0,L/2]")
    return L * math.asinh(ell / a)


def renormalized_circle(
    radius: float, regulator: float, subtraction_range: float | None = None
) -> float:
    return raw_circle(radius, regulator) - local_subtraction(
        radius, regulator, subtraction_range
    )


def validate(
    radius: float = 1.36,
    regulator: float = 1.36,
    subtraction_range: float | None = None,
) -> CircleResult:
    L = 2.0 * math.pi * radius
    ell = L / 2.0 if subtraction_range is None else subtraction_range
    analytic = raw_circle(radius, regulator)
    numerical = raw_circle_quadrature(radius, regulator)
    rel = abs(analytic - numerical) / max(abs(analytic), 1e-15)
    return CircleResult(
        radius=radius,
        regulator=regulator,
        subtraction_range=ell,
        raw_analytic=analytic,
        raw_quadrature=numerical,
        renormalized_analytic=renormalized_circle(radius, regulator, ell),
        relative_error=rel,
    )


if __name__ == "__main__":
    import json

    print(json.dumps(validate().as_dict(), indent=2))
