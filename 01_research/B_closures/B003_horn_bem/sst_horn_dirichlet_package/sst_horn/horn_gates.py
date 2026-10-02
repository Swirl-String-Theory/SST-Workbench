from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
import importlib
import json
import math
from pathlib import Path
from typing import Iterable

from .build_ext_if_needed import build_if_needed

TWOPI = 2.0 * math.pi


@dataclass
class HornGateConfig:
    lambda_: float = 1.2
    n_ring: int = 192
    n_surface: int = 40
    n_volume: int = 22
    box_radius: float = 6.0
    eps: float = 0.08
    fd_step: float = 0.025
    force_rebuild: bool = False
    prefer_cpp: bool = True
    circulation_tol: float = 1.0e-2
    neumann_tol: float = 1.0e-2
    harmonic_tol: float = 1.0e-2
    farfield_tol: float = 2.5e-1
    target_tol: float = 5.0e-2


@dataclass
class HornDirichletResult:
    lambda_: float
    chi_K: float
    chi_cav: float
    chi_E_hollow: float
    residual_kinetic_to_2pi: float
    residual_total_to_2pi: float
    circulation: float
    circulation_error: float
    neumann_boundary_error: float
    divergence_error: float
    curl_error: float
    farfield_decay_error: float
    mesh_cells: int
    dof: int
    solver_residual: float
    energy_refinement_error: float
    solver_kind: str
    analytic_total_horn_falsifies_2pi: bool
    gate_circulation_pass: bool
    gate_neumann_pass: bool
    gate_harmonic_pass: bool
    gate_farfield_pass: bool
    gate_kinetic_2pi_pass: bool
    gate_total_2pi_pass: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _backend(prefer_cpp: bool, force_rebuild: bool):
    if prefer_cpp and build_if_needed(force=force_rebuild, verbose=True):
        try:
            return importlib.import_module("sst_horn._hornkernels")
        except Exception:
            pass
    return importlib.import_module("sst_horn._fallback")


def run_gate(config: HornGateConfig) -> HornDirichletResult:
    if config.lambda_ <= 1.0:
        raise ValueError("lambda must be > 1.0; horn limit is approached as lambda -> 1+.")
    backend = _backend(config.prefer_cpp, config.force_rebuild)
    raw = backend.compute_metrics(
        float(config.lambda_),
        int(config.n_ring),
        int(config.n_surface),
        int(config.n_volume),
        float(config.box_radius),
        float(config.eps),
        float(config.fd_step),
    )
    chi_K = float(raw["chi_K"])
    chi_cav = math.pi * math.pi * config.lambda_
    chi_E = chi_K + chi_cav
    return HornDirichletResult(
        lambda_=config.lambda_,
        chi_K=chi_K,
        chi_cav=chi_cav,
        chi_E_hollow=chi_E,
        residual_kinetic_to_2pi=(chi_K - TWOPI) / TWOPI,
        residual_total_to_2pi=(chi_E - TWOPI) / TWOPI,
        circulation=float(raw["circulation"]),
        circulation_error=float(raw["circulation_error"]),
        neumann_boundary_error=float(raw["neumann_boundary_error"]),
        divergence_error=float(raw["divergence_error"]),
        curl_error=float(raw["curl_error"]),
        farfield_decay_error=float(raw["farfield_decay_error"]),
        mesh_cells=int(raw["mesh_cells"]),
        dof=int(raw["dof"]),
        solver_residual=float(raw["solver_residual"]),
        energy_refinement_error=float(raw["energy_refinement_error"]),
        solver_kind=str(raw["solver_kind"]),
        analytic_total_horn_falsifies_2pi=True,
        gate_circulation_pass=float(raw["circulation_error"]) < config.circulation_tol,
        gate_neumann_pass=float(raw["neumann_boundary_error"]) < config.neumann_tol,
        gate_harmonic_pass=(float(raw["divergence_error"]) + float(raw["curl_error"])) < config.harmonic_tol,
        gate_farfield_pass=float(raw["farfield_decay_error"]) < config.farfield_tol,
        gate_kinetic_2pi_pass=abs((chi_K - TWOPI) / TWOPI) < config.target_tol,
        gate_total_2pi_pass=abs((chi_E - TWOPI) / TWOPI) < config.target_tol,
    )


def run_sweep(lambdas: Iterable[float], base: HornGateConfig) -> list[HornDirichletResult]:
    results = []
    for lam in lambdas:
        cfg = HornGateConfig(**{**asdict(base), "lambda_": float(lam), "force_rebuild": False})
        results.append(run_gate(cfg))
    return results


def write_json(path: str | Path, results: list[HornDirichletResult] | HornDirichletResult) -> None:
    p = Path(path)
    if isinstance(results, HornDirichletResult):
        payload = results.to_dict()
    else:
        payload = [r.to_dict() for r in results]
    p.write_text(json.dumps(payload, indent=2, sort_keys=True))


def write_csv(path: str | Path, results: list[HornDirichletResult]) -> None:
    p = Path(path)
    rows = [r.to_dict() for r in results]
    if not rows:
        p.write_text("")
        return
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
