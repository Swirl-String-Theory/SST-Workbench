from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _load_cpp_backend():
    try:
        from .build_ext_if_needed import build_if_needed
        build_if_needed(verbose=False)
        from . import _hornbem  # type: ignore
        return _hornbem
    except Exception:
        return None


def run_horn_bem(
    lambda_: float = 1.2,
    n_ring: int = 256,
    n_surface: int = 32,
    n_volume: int = 18,
    box_radius: float = 6.0,
    source_eps: float = 0.08,
    fd_step: float = 1e-3,
    bem: bool = True,
    bem_n_eta: int = 12,
    bem_n_phi: int = 24,
    bem_self_term: float = 0.5,
    bem_auto_self_term: bool = True,
    bem_ridge: float = 1e-10,
    force_python: bool = False,
) -> Dict[str, Any]:
    """Run one horn-torus Neumann BEM audit.

    Parameters are dimensionless. The torus has major radius R=lambda_ and minor
    radius a=1. The horn limit is lambda_ -> 1+ and should not be solved directly.
    """
    if not force_python:
        backend = _load_cpp_backend()
        if backend is not None:
            try:
                return dict(backend.run_horn_bem(
                    float(lambda_), int(n_ring), int(n_surface), int(n_volume), float(box_radius),
                    float(source_eps), float(fd_step), bool(bem), int(bem_n_eta), int(bem_n_phi),
                    float(bem_self_term), bool(bem_auto_self_term), float(bem_ridge)
                ))
            except Exception as exc:
                print(f"[sst_horn_bem] C++ backend failed, using NumPy fallback: {exc}", file=sys.stderr)

    from .fallback import run_horn_bem_numpy
    return run_horn_bem_numpy(
        lambda_=lambda_, n_ring=n_ring, n_surface=n_surface, n_volume=n_volume,
        box_radius=box_radius, source_eps=source_eps, fd_step=fd_step, bem=bem,
        bem_n_eta=bem_n_eta, bem_n_phi=bem_n_phi, bem_self_term=bem_self_term,
        bem_auto_self_term=bem_auto_self_term, bem_ridge=bem_ridge,
    )


def run_sweep(
    lambdas: Iterable[float] = (1.05, 1.1, 1.2, 1.5, 2.0),
    **kwargs: Any,
) -> List[Dict[str, Any]]:
    return [run_horn_bem(lambda_=lam, **kwargs) for lam in lambdas]


def write_json(path: str | Path, data: Any) -> None:
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=True), encoding="utf-8")


def write_csv(path: str | Path, rows: List[Dict[str, Any]]) -> None:
    import csv
    if not rows:
        Path(path).write_text("", encoding="utf-8")
        return
    keys = []
    for r in rows:
        for k in r.keys():
            if k not in keys:
                keys.append(k)
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)
