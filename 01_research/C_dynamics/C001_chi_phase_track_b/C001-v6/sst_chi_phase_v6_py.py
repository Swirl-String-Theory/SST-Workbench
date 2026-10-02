r"""Pure-Python backend for SST chi-phase v6 root selector.

v6 focuses on the smooth matched polynomial profile

    f_a(x) = x [ a + (3 - 2a) x^2 + (a - 2) x^4 ]

which satisfies f(0)=0, f(1)=1, f'(1)=-1.  It solves the non-tautological
condition c_chi/v_ref = 1, where

    (c_chi/v_ref)^2 = 4 \int_0^1 f_a(x)^2 x^3 dx

for uniform density in the core cross-section.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import math
from typing import Callable, Dict, Iterable, List, Tuple

PHI = (1.0 + math.sqrt(5.0)) / 2.0
A0_STAR_ANALYTIC = (-13.0 + math.sqrt(385.0)) / 4.0


@dataclass
class PointResult:
    label: str
    a0: float
    c2_over_v2_analytic: float
    c_over_v_analytic: float
    c2_over_v2_numeric: float
    c_over_v_numeric: float
    c_minus_1: float
    a0_minus_phi: float
    grad_energy: float
    curvature_energy: float
    shape_energy: float

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def smooth_matched_poly(x: float, a0: float) -> float:
    x2 = x * x
    return x * (a0 + (3.0 - 2.0 * a0) * x2 + (a0 - 2.0) * x2 * x2)


def smooth_matched_poly_prime(x: float, a0: float) -> float:
    # f = a x + (3-2a)x^3 + (a-2)x^5
    return a0 + 3.0 * (3.0 - 2.0 * a0) * x * x + 5.0 * (a0 - 2.0) * x**4


def smooth_matched_poly_second(x: float, a0: float) -> float:
    return 6.0 * (3.0 - 2.0 * a0) * x + 20.0 * (a0 - 2.0) * x**3


def c2_over_v2_analytic(a0: float) -> float:
    return (2.0 * a0 * a0 + 13.0 * a0 + 78.0) / 105.0


def c_over_v_analytic(a0: float) -> float:
    return math.sqrt(c2_over_v2_analytic(a0))


def root_residual(a0: float) -> float:
    return c2_over_v2_analytic(a0) - 1.0


def analytic_root() -> float:
    return A0_STAR_ANALYTIC


def bisection_root(lo: float = 0.0, hi: float = 3.0, tol: float = 1e-14, max_iter: int = 200) -> float:
    flo = root_residual(lo)
    fhi = root_residual(hi)
    if flo == 0.0:
        return lo
    if fhi == 0.0:
        return hi
    if flo * fhi > 0.0:
        raise ValueError(f"Root not bracketed: f({lo})={flo}, f({hi})={fhi}")
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        fm = root_residual(mid)
        if abs(fm) < tol or 0.5 * (hi - lo) < tol:
            return mid
        if flo * fm <= 0.0:
            hi = mid
            fhi = fm
        else:
            lo = mid
            flo = fm
    return 0.5 * (lo + hi)


def midpoint_integral(func: Callable[[float], float], n: int = 400000) -> float:
    # Robust midpoint rule; enough for smoke tests, avoids numpy dependency in backend.
    h = 1.0 / float(n)
    total = 0.0
    for i in range(n):
        x = (i + 0.5) * h
        total += func(x)
    return total * h


def c2_over_v2_numeric(a0: float, n: int = 400000) -> float:
    # denominator \int_0^1 x^3 dx = 1/4 for uniform density.
    num = midpoint_integral(lambda x: smooth_matched_poly(x, a0) ** 2 * x**3, n=n)
    return 4.0 * num


def grad_energy_analytic(a0: float) -> float:
    # \int_0^1 f'(x)^2 x dx
    return (2.0 * a0 * a0 - 7.0 * a0 + 12.0) / 12.0


def curvature_energy_analytic(a0: float) -> float:
    # \int_0^1 f''(x)^2 x dx
    return 6.0 * a0 * a0 - 28.0 * a0 + 41.0


def shape_energy_analytic(a0: float) -> float:
    # \int_0^1 (f(x)-x)^2 x dx ; zero-ish would prefer solid-body-like shape.
    return (2.0 * a0 * a0 - 2.0 * a0 + 1.0) / 120.0


def energy_minima() -> Dict[str, float]:
    return {
        "grad_energy_min_a0": 7.0 / 4.0,
        "curvature_energy_min_a0": 7.0 / 3.0,
        "shape_energy_min_a0": 0.5,
    }


def point_result(label: str, a0: float, n: int = 400000) -> PointResult:
    c2_a = c2_over_v2_analytic(a0)
    c2_n = c2_over_v2_numeric(a0, n=n)
    c_a = math.sqrt(c2_a)
    c_n = math.sqrt(c2_n)
    return PointResult(
        label=label,
        a0=a0,
        c2_over_v2_analytic=c2_a,
        c_over_v_analytic=c_a,
        c2_over_v2_numeric=c2_n,
        c_over_v_numeric=c_n,
        c_minus_1=c_a - 1.0,
        a0_minus_phi=a0 - PHI,
        grad_energy=grad_energy_analytic(a0),
        curvature_energy=curvature_energy_analytic(a0),
        shape_energy=shape_energy_analytic(a0),
    )


def sweep_a0(a_min: float = 0.0, a_max: float = 3.0, count: int = 301) -> List[Dict[str, float]]:
    if count < 2:
        raise ValueError("count must be >= 2")
    rows = []
    for i in range(count):
        a0 = a_min + (a_max - a_min) * i / (count - 1)
        rows.append({
            "a0": a0,
            "c2_over_v2": c2_over_v2_analytic(a0),
            "c_over_v": c_over_v_analytic(a0),
            "residual_c2_minus_1": root_residual(a0),
            "distance_to_phi": a0 - PHI,
            "distance_to_a0_star": a0 - A0_STAR_ANALYTIC,
            "grad_energy": grad_energy_analytic(a0),
            "curvature_energy": curvature_energy_analytic(a0),
            "shape_energy": shape_energy_analytic(a0),
        })
    return rows


def profile_curve(a0: float, n: int = 1000) -> Tuple[List[float], List[float]]:
    xs = [i / (n - 1) for i in range(n)]
    ys = [smooth_matched_poly(x, a0) for x in xs]
    return xs, ys


def build_report_points(n: int = 400000) -> List[PointResult]:
    root_n = bisection_root()
    mins = energy_minima()
    return [
        point_result("analytic_root", A0_STAR_ANALYTIC, n=n),
        point_result("bisection_root", root_n, n=n),
        point_result("golden_ratio_phi", PHI, n=n),
        point_result("v5_a0_1p5", 1.5, n=n),
        point_result("v5_a0_2p0", 2.0, n=n),
        point_result("grad_energy_min", mins["grad_energy_min_a0"], n=n),
        point_result("curvature_energy_min", mins["curvature_energy_min_a0"], n=n),
        point_result("shape_energy_min", mins["shape_energy_min_a0"], n=n),
    ]
