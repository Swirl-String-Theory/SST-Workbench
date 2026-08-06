from __future__ import annotations
from pathlib import Path
from typing import Iterable
import json
import numpy as np

from .core import BackendOptions, resolve_backend
from .build_ext_if_needed import extension_path, source_hash
from . import fallback


def _error(native: np.ndarray, python: np.ndarray) -> dict:
    delta = np.asarray(native) - np.asarray(python)
    abs_max = float(np.max(np.abs(delta))) if delta.size else 0.0
    l2 = float(np.linalg.norm(delta.ravel()))
    ref = float(np.linalg.norm(np.asarray(python).ravel()))
    return {
        "abs_max": abs_max,
        "relative_l2": l2 / max(ref, 1e-300),
        "reference_l2": ref,
    }


def run_native_parity_audit(
    curves: list[np.ndarray],
    sign_matrix: np.ndarray,
    epsilons: list[float],
    options: BackendOptions,
    abs_tolerance: float = 2e-12,
    relative_tolerance: float = 2e-12,
    local_skip_velocity: int = 3,
    local_skip_energy: int = 2,
) -> dict:
    native_options = BackendOptions(
        require_native=True,
        force_python=False,
        skip_build=options.skip_build,
        force_build=options.force_build,
        build_verbose=options.build_verbose,
    )
    native, backend_name = resolve_backend(native_options)
    report = {
        "backend_status": {
            "backend": backend_name,
            "native_required": True,
            "force_python": False,
            "extension_path": str(extension_path()),
            "extension_exists": extension_path().exists(),
            "source_hash": source_hash(),
            "build_info": dict(native.build_info()),
        },
        "abs_tolerance": abs_tolerance,
        "relative_tolerance": relative_tolerance,
        "velocity": [],
    }
    for epsilon in epsilons:
        cpp_velocity = [np.asarray(x) for x in native.link_velocity_batch(
            curves, sign_matrix, float(epsilon), int(local_skip_velocity)
        )]
        py_velocity = fallback.link_velocity_batch(
            curves, sign_matrix, float(epsilon), int(local_skip_velocity)
        )
        component_errors = [_error(a, b) for a, b in zip(cpp_velocity, py_velocity)]
        report["velocity"].append({"epsilon_D": epsilon, "components": component_errors})
    cpp_linking = np.asarray(native.gauss_linking_matrix(curves))
    py_linking = fallback.gauss_linking_matrix(curves)
    report["gauss_linking"] = _error(cpp_linking, py_linking)
    cpp_energy = np.asarray(native.neumann_coupling_matrices(
        curves, np.asarray(epsilons, dtype=float), int(local_skip_energy)
    ))
    py_energy = fallback.neumann_coupling_matrices(
        curves, np.asarray(epsilons, dtype=float), int(local_skip_energy)
    )
    report["neumann_coupling"] = _error(cpp_energy, py_energy)
    all_errors = [report["gauss_linking"], report["neumann_coupling"]]
    all_errors.extend(x for row in report["velocity"] for x in row["components"])
    report["ok"] = all(
        x["abs_max"] <= abs_tolerance or x["relative_l2"] <= relative_tolerance
        for x in all_errors
    )
    return report


def write_audit(path: str | Path, report: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
