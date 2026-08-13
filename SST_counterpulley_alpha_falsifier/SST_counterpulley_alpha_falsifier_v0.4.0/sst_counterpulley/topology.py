"""Topology diagnostics for the counter-pulley ribbon (blind to alpha)."""
from __future__ import annotations
import numpy as np
from .backend import load_backend


def topology_observables(centerline: np.ndarray, plus: np.ndarray, minus: np.ndarray, *,
                         force_python: bool = False, skip_build: bool = True) -> dict[str, float]:
    backend, _ = load_backend(force_python=force_python, skip_build=skip_build)
    lk = float(backend.gauss_linking(plus, minus))
    wr = float(backend.writhe_midpoint(centerline))
    tw = lk - wr
    nearest = round(lk)
    return {
        "gauss_linking": lk,
        "gauss_linking_nearest_integer": int(nearest),
        "gauss_linking_integer_error": float(abs(lk - nearest)),
        "writhe": wr,
        "ribbon_twist_from_Lk_minus_Wr": float(tw),
    }
