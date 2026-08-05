from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize_scalar

from .contact import PeriodicLiftMap
from .util import circular_distance


@dataclass
class BilliardResult:
    period: int
    seed: float
    orbit: np.ndarray
    closure_residual: float
    min_lower_period_residual: float
    unique_orbit_points: int
    minimum_orbit_spacing: float
    second_best_residual: float
    map_branch: str


def iterate_map(contact_map: PeriodicLiftMap, seed: np.ndarray | float, steps: int) -> np.ndarray:
    x = np.asarray(seed, dtype=float)
    for _ in range(steps):
        x = contact_map(x)
    return x


def scan_billiard(contact_map: PeriodicLiftMap, period: int = 9, grid: int = 4096, branch_name: str = "sigma") -> BilliardResult:
    seeds = np.arange(grid, dtype=float) / grid
    end = iterate_map(contact_map, seeds, period)
    residuals = circular_distance(end, seeds)
    order = np.argsort(residuals)
    best_idx = int(order[0])
    left = (best_idx - 2) / grid
    right = (best_idx + 2) / grid
    result = minimize_scalar(
        lambda s: float(circular_distance(iterate_map(contact_map, s, period), s)),
        bounds=(left, right),
        method="bounded",
        options={"xatol": 1e-14},
    )
    seed = float(result.x % 1.0)
    orbit = [seed]
    x = seed
    for _ in range(period):
        x = float(contact_map(x))
        orbit.append(x % 1.0)
    orbit_arr = np.asarray(orbit[:-1], dtype=float)
    closure = float(circular_distance(orbit[-1], seed))
    lower = []
    x = seed
    for k in range(1, period):
        x = float(contact_map(x))
        lower.append(float(circular_distance(x, seed)))
    sorted_orbit = np.sort(orbit_arr)
    spacings = np.diff(np.r_[sorted_orbit, sorted_orbit[0] + 1.0])
    unique = int(np.sum(spacings > 1e-6))
    second_best = float(residuals[order[min(1, len(order) - 1)]])
    return BilliardResult(
        period=period,
        seed=seed,
        orbit=orbit_arr,
        closure_residual=closure,
        min_lower_period_residual=float(min(lower)) if lower else np.inf,
        unique_orbit_points=unique,
        minimum_orbit_spacing=float(np.min(spacings)),
        second_best_residual=second_best,
        map_branch=branch_name,
    )
