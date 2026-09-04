from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

from . import constants
from ._config import EXT_BASENAME, PACKAGE_NAME, RESULT_SCHEMA

PACKAGE_VERSION = "0.4.1"


def write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        p.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with p.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _backend(*, force_python: bool, auto_build: bool, force_build: bool, build_verbose: bool):
    info: dict[str, Any] = {"backend": "python", "build": None, "import_error": None}
    if force_python:
        from . import fallback
        return fallback, info
    if auto_build:
        from .build_ext_if_needed import build_if_needed
        info["build"] = build_if_needed(force=force_build, verbose=build_verbose)
    try:
        mod = __import__(f"{PACKAGE_NAME}.{EXT_BASENAME}", fromlist=["*"])
        info["backend"] = "cpp"
        return mod, info
    except Exception as exc:
        info["import_error"] = f"{type(exc).__name__}: {exc}"
        from . import fallback
        return fallback, info


def analyze_profile(
    profile: str = "external",
    a_core_over_rc: float = 0.0045,
    x_min: float = 1e-5,
    x_max: float = 0.1,
    samples: int = 4000,
    *,
    force_python: bool = False,
    auto_build: bool = True,
    force_build: bool = False,
    build_verbose: bool = False,
) -> dict[str, Any]:
    mod, backend = _backend(
        force_python=force_python, auto_build=auto_build,
        force_build=force_build, build_verbose=build_verbose,
    )
    raw = mod.analyze_profile(profile, constants.BETA_0, a_core_over_rc, x_min, x_max, samples)
    roots = []
    for root in raw["critical_roots"]:
        root = dict(root)
        root["r_m"] = float(root["x"]) * constants.R_C
        root["outside_declared_core"] = float(root["x"]) > a_core_over_rc
        root["radial_stability"] = (
            "hyperbolic_candidate" if root.get("K_hat") is not None and float(root["K_hat"]) < 0
            else "elliptic_or_unresolved"
        )
        roots.append(root)
    horizons = []
    for h in raw["horizon_roots"]:
        h = dict(h)
        h["r_m"] = float(h["x"]) * constants.R_C
        h["outside_declared_core"] = float(h["x"]) > a_core_over_rc
        horizons.append(h)

    external_benchmark = {
        "x_horizon": constants.FORMAL_X_HORIZON,
        "x_star": constants.FORMAL_X_STAR,
        "r_horizon_m": constants.FORMAL_X_HORIZON * constants.R_C,
        "r_star_m": constants.FORMAL_X_STAR * constants.R_C,
        "a_window_horizon_free_light_ring": [constants.FORMAL_X_HORIZON, constants.FORMAL_X_STAR],
    }
    valid_roots = [r for r in roots if r["outside_declared_core"] and r["clock_valid"]]
    classification = "NO_RADIAL_FERMAT_CRITICAL_RADIUS"
    if roots and not valid_roots:
        classification = "CRITICAL_RADIUS_INSIDE_DECLARED_CORE"
    if valid_roots:
        classification = "RADIAL_FERMAT_CRITICAL_CANDIDATE"
    if any(h["outside_declared_core"] for h in horizons):
        classification += "_WITH_EXTERNAL_CLOCK_DEGENERACY"

    return {
        "schema": RESULT_SCHEMA,
        "package_version": PACKAGE_VERSION,
        "audit_name": "SST standalone radial Fermat profile analysis",
        "status": "RESEARCH_TRACK",
        "backend": backend,
        "canonical_constants": constants.as_dict(),
        "input": {
            "profile": profile,
            "a_core_over_rc": a_core_over_rc,
            "x_min": x_min,
            "x_max": x_max,
            "samples": samples,
        },
        "external_analytic_benchmark": external_benchmark,
        "critical_roots": roots,
        "horizon_roots": horizons,
        "classification": classification,
        "global_closed_orbit_certified": False,
        "qsm_certified": False,
    }


def sweep_profiles(
    profile: str,
    a_values: list[float],
    *,
    x_min: float = 1e-5,
    x_max: float = 0.1,
    samples: int = 4000,
    force_python: bool = False,
    auto_build: bool = True,
    force_build: bool = False,
    build_verbose: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i, a in enumerate(a_values):
        result = analyze_profile(
            profile, a, x_min, x_max, samples,
            force_python=force_python,
            auto_build=auto_build if i == 0 else False,
            force_build=force_build if i == 0 else False,
            build_verbose=build_verbose,
        )
        valid = [r for r in result["critical_roots"] if r.get("outside_declared_core") and r.get("clock_valid")]
        root = valid[0] if valid else (result["critical_roots"][0] if result["critical_roots"] else {})
        rows.append({
            "profile": profile,
            "a_core_over_rc": a,
            "backend": result["backend"]["backend"],
            "classification": result["classification"],
            "critical_count": len(result["critical_roots"]),
            "first_x_star": root.get("x"),
            "first_r_star_m": root.get("r_m"),
            "first_K_hat": root.get("K_hat"),
            "outside_declared_core": root.get("outside_declared_core"),
            "horizon_count": len(result["horizon_roots"]),
        })
    return rows


def backend_biot_savart(
    centerline,
    probes,
    *,
    epsilon: float,
    kernel_model: str = "rosenhead_midpoint",
    force_python: bool = False,
    auto_build: bool = True,
):
    mod, backend = _backend(
        force_python=force_python, auto_build=auto_build, force_build=False, build_verbose=False
    )
    coefficient = constants.BETA_0 / 2.0
    return (
        mod.biot_savart_batch(centerline, probes, coefficient, epsilon, kernel_model),
        backend,
    )


def backend_biot_savart_with_jacobian(
    centerline,
    probes,
    *,
    epsilon: float,
    kernel_model: str = "rosenhead_midpoint",
    force_python: bool = False,
    auto_build: bool = True,
):
    mod, backend = _backend(
        force_python=force_python, auto_build=auto_build, force_build=False, build_verbose=False
    )
    coefficient = constants.BETA_0 / 2.0
    beta, jacobian = mod.biot_savart_batch_with_jacobian(
        centerline, probes, coefficient, epsilon, kernel_model
    )
    return beta, jacobian, backend
