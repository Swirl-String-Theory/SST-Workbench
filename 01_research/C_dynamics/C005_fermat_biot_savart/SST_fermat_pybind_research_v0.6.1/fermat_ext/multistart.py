from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np

from .core import PACKAGE_VERSION
from .certification import scan_stationary_candidates
from .geodesic import shoot_closed_orbit
from .knot_catalog import sample_ideal_knot


@dataclass(frozen=True)
class SeedIdentity:
    station: int
    angle_index: int
    direction_sign: int
    period_multiplier: float


def _seed_from_root(root: dict[str, Any], direction_sign: int) -> dict[str, Any]:
    if direction_sign not in (-1, 1):
        raise ValueError("direction_sign must be -1 or +1")
    base = np.asarray(root["azimuthal_seed_direction"], dtype=float)
    selected = (direction_sign * base).tolist()
    return {
        **root,
        "directions": [selected],
        "direction_sign": direction_sign,
    }


def collect_seed_family(
    knot_id: str,
    *,
    epsilon: float,
    centerline_points: int,
    stations: int = 4,
    angles: int = 8,
    period_multipliers: Sequence[float] = (0.5, 1.0, 2.0, 4.0),
    rho_min: float = 0.0005,
    rho_max: float = 0.01,
    bracket_samples: int = 96,
    force_python: bool = False,
    auto_build: bool = True,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    atlas = scan_stationary_candidates(
        knot_id,
        epsilon=epsilon,
        centerline_points=centerline_points,
        stations=stations,
        angles=angles,
        rho_min=rho_min,
        rho_max=rho_max,
        bracket_samples=bracket_samples,
        force_python=force_python,
        auto_build=auto_build,
        reach_pair_points=min(1024, max(128, centerline_points // 4)),
    )
    roots = [r for r in atlas["roots"] if r["classification"] == "RESOLVED_LOCAL_MINIMUM"]
    seeds: list[dict[str, Any]] = []
    for root in roots:
        for sign in (+1, -1):
            seed = _seed_from_root(root, sign)
            for multiplier in period_multipliers:
                if multiplier <= 0 or not math.isfinite(float(multiplier)):
                    raise ValueError("period multipliers must be positive and finite")
                seeds.append({
                    "identity": {
                        "station": int(root["station"]),
                        "angle_index": int(root["angle_index"]),
                        "direction_sign": sign,
                        "period_multiplier": float(multiplier),
                    },
                    "seed": seed,
                    "initial_parameters": [0.0, 0.0, 0.0, 0.0, math.log(float(multiplier))],
                })
    return atlas, seeds


def multistart_closed_orbit_search(
    knot_id: str,
    *,
    epsilon: float = 0.0019,
    centerline_points: int = 8192,
    stations: int = 4,
    angles: int = 8,
    period_multipliers: Sequence[float] = (0.5, 1.0, 2.0, 4.0),
    coarse_step_count: int = 128,
    coarse_iterations: int = 2,
    refine_top_k: int = 8,
    refine_step_count: int = 512,
    refine_iterations: int = 12,
    force_python: bool = False,
    auto_build: bool = True,
) -> dict[str, Any]:
    atlas, family = collect_seed_family(
        knot_id,
        epsilon=epsilon,
        centerline_points=centerline_points,
        stations=stations,
        angles=angles,
        period_multipliers=period_multipliers,
        force_python=force_python,
        auto_build=auto_build,
    )
    curve = sample_ideal_knot(knot_id, centerline_points)
    coarse: list[dict[str, Any]] = []
    for i, item in enumerate(family):
        shot = shoot_closed_orbit(
            curve,
            item["seed"],
            epsilon=epsilon,
            step_count=coarse_step_count,
            max_iterations=coarse_iterations,
            force_python=force_python,
            auto_build=False,
            initial_parameters=item["initial_parameters"],
        )
        residual = shot.get("best", {}).get("normalized_residual_norm")
        coarse.append({"identity": item["identity"], "shot": shot, "score": residual})
    ranked = sorted(coarse, key=lambda r: float(r["score"]) if r["score"] is not None else math.inf)
    refined: list[dict[str, Any]] = []
    for row in ranked[:max(1, refine_top_k)]:
        params = row["shot"].get("best", {}).get("parameters")
        identity = row["identity"]
        root_matches = [
            r for r in atlas["roots"]
            if r["classification"] == "RESOLVED_LOCAL_MINIMUM"
            and int(r["station"]) == int(identity["station"])
            and int(r["angle_index"]) == int(identity["angle_index"])
        ]
        if not root_matches:
            continue
        seed = _seed_from_root(root_matches[0], int(identity["direction_sign"]))
        shot = shoot_closed_orbit(
            curve,
            seed,
            epsilon=epsilon,
            step_count=refine_step_count,
            max_iterations=refine_iterations,
            force_python=force_python,
            auto_build=False,
            initial_parameters=params,
        )
        residual = shot.get("best", {}).get("normalized_residual_norm")
        refined.append({"identity": identity, "shot": shot, "score": residual})
    refined_ranked = sorted(refined, key=lambda r: float(r["score"]) if r["score"] is not None else math.inf)
    best = refined_ranked[0] if refined_ranked else (ranked[0] if ranked else None)
    return {
        "schema": "sst.fermat.multistart-closed-orbit-search.v0.6.1",
        "package_version": PACKAGE_VERSION,
        "status": "MULTISTART_SEARCH_COMPLETED" if best is not None else "NO_RESOLVED_LOCAL_MINIMUM_SEEDS",
        "knot_id": knot_id,
        "epsilon_over_rc": epsilon,
        "centerline_points": centerline_points,
        "stations": stations,
        "angles": angles,
        "period_multipliers": [float(v) for v in period_multipliers],
        "seed_count": len(family),
        "coarse_results": coarse,
        "refined_results": refined_ranked,
        "best": best,
        "resolved_closed_orbit_found": bool(best and best["shot"].get("resolved_closed_orbit")),
        "global_closed_orbit_certified": False,
        "monodromy_certified": False,
        "qsm_certified": False,
        "guard": (
            "This is a finite multistart search over sampled local-minimum seeds, both directions, "
            "and preregistered period multipliers. Absence of a resolved shot is not a proof that no closed orbit exists."
        ),
    }


def selected_seed_convergence(
    knot_id: str,
    identity: dict[str, Any],
    *,
    epsilon: float = 0.0019,
    centerline_point_counts: Sequence[int] = (8192, 16384, 32768),
    step_counts: Sequence[int] = (256, 512, 1024),
    stations: int = 4,
    angles: int = 8,
    max_iterations: int = 12,
    position_tolerance_over_rc: float = 2e-7,
    direction_tolerance: float = 2e-7,
    parameter_relative_tolerance: float = 2e-3,
    centerline_relative_tolerance: float = 2e-3,
    force_python: bool = False,
    auto_build: bool = True,
) -> dict[str, Any]:
    n_levels = sorted(set(int(v) for v in centerline_point_counts))
    s_levels = sorted(set(int(v) for v in step_counts))
    if len(n_levels) < 3 or len(s_levels) < 3:
        raise ValueError("three centerline and three integration levels are required")
    levels: list[dict[str, Any]] = []
    warm_params: list[float] | None = [0.0, 0.0, 0.0, 0.0, math.log(float(identity["period_multiplier"]))]
    for ni, n in enumerate(n_levels):
        atlas, _ = collect_seed_family(
            knot_id,
            epsilon=epsilon,
            centerline_points=n,
            stations=stations,
            angles=angles,
            period_multipliers=(float(identity["period_multiplier"]),),
            force_python=force_python,
            auto_build=auto_build if ni == 0 else False,
        )
        roots = [
            r for r in atlas["roots"]
            if r["classification"] == "RESOLVED_LOCAL_MINIMUM"
            and int(r["station"]) == int(identity["station"])
            and int(r["angle_index"]) == int(identity["angle_index"])
        ]
        if not roots:
            levels.append({"centerline_points": n, "status": "SEED_NOT_PRESENT", "atlas": atlas})
            continue
        seed = _seed_from_root(roots[0], int(identity["direction_sign"]))
        curve = sample_ideal_knot(knot_id, n)
        shots: list[dict[str, Any]] = []
        params = warm_params
        for steps in s_levels:
            shot = shoot_closed_orbit(
                curve,
                seed,
                epsilon=epsilon,
                step_count=steps,
                max_iterations=max_iterations,
                position_tolerance_over_rc=position_tolerance_over_rc,
                direction_tolerance=direction_tolerance,
                force_python=force_python,
                auto_build=False,
                initial_parameters=params,
            )
            shots.append(shot)
            if "best" in shot:
                params = shot["best"]["parameters"]
        if shots and "best" in shots[-1]:
            warm_params = shots[-1]["best"]["parameters"]
        last_two = shots[-2:]
        integration_resolved = len(last_two) == 2 and all(s.get("resolved_closed_orbit") for s in last_two)
        if len(last_two) == 2 and all("best" in s for s in last_two):
            p0=np.asarray(last_two[0]["best"]["parameters"],float); p1=np.asarray(last_two[1]["best"]["parameters"],float)
            param_drift=float(np.linalg.norm(p1-p0)/max(np.linalg.norm(p1),1.0))
            per0=float(last_two[0]["best"]["period_over_rc"]); per1=float(last_two[1]["best"]["period_over_rc"])
            period_drift=abs(per1-per0)/max(abs(per1),1e-30)
        else:
            param_drift=period_drift=math.inf
        integration_certified=integration_resolved and max(param_drift,period_drift)<=parameter_relative_tolerance
        levels.append({
            "centerline_points": n,
            "status": "INTEGRATION_CERTIFIED" if integration_certified else "UNRESOLVED_OR_NOT_CONVERGED",
            "seed": seed,
            "shots": shots,
            "integration_certified": integration_certified,
            "last_two_parameter_relative_drift": param_drift if math.isfinite(param_drift) else None,
            "last_two_period_relative_drift": period_drift if math.isfinite(period_drift) else None,
        })
    valid=[v for v in levels if v.get("integration_certified") and v.get("shots") and "best" in v["shots"][-1]]
    all_integration=len(valid)==len(n_levels)
    if len(valid)>=2:
        a,b=valid[-2],valid[-1]
        ba=a["shots"][-1]["best"]; bb=b["shots"][-1]["best"]
        period_drift=abs(float(bb["period_over_rc"])-float(ba["period_over_rc"]))/max(abs(float(bb["period_over_rc"])),1e-30)
        xa=np.asarray(ba["initial_position_over_rc"],float); xb=np.asarray(bb["initial_position_over_rc"],float)
        start_drift=float(np.linalg.norm(xb-xa)/max(np.linalg.norm(xb),1.0))
    else:
        period_drift=start_drift=math.inf
    centerline_converged=len(valid)>=2 and max(period_drift,start_drift)<=centerline_relative_tolerance
    certified=all_integration and centerline_converged
    highest_shot=None
    if valid:
        highest_shot=dict(valid[-1]["shots"][-1])
        highest_shot["global_closed_orbit_certified"]=certified
    return {
        "schema":"sst.fermat.selected-seed-global-convergence.v0.6.1",
        "package_version":PACKAGE_VERSION,
        "status":"GLOBAL_CLOSED_ORBIT_CERTIFIED" if certified else "GLOBAL_ORBIT_UNRESOLVED_OR_NOT_CONVERGED",
        "knot_id":knot_id,
        "identity":identity,
        "epsilon_over_rc":epsilon,
        "centerline_point_counts":n_levels,
        "step_counts":s_levels,
        "levels":levels,
        "last_two_centerline_period_relative_drift":period_drift if math.isfinite(period_drift) else None,
        "last_two_centerline_start_relative_drift":start_drift if math.isfinite(start_drift) else None,
        "highest_resolution_shot":highest_shot,
        "global_closed_orbit_certified":certified,
        "monodromy_certified":False,
        "qsm_certified":False,
    }


def continue_selected_seed_in_epsilon(
    knot_id: str,
    identity: dict[str, Any],
    epsilon_values: Sequence[float],
    *,
    centerline_points: int = 8192,
    step_count: int = 512,
    stations: int = 4,
    angles: int = 8,
    max_iterations: int = 12,
    force_python: bool = False,
    auto_build: bool = True,
) -> dict[str, Any]:
    values=[float(v) for v in epsilon_values]
    if not values or any(v<=0 for v in values): raise ValueError("positive epsilon values required")
    curve=sample_ideal_knot(knot_id,centerline_points)
    params=[0.0,0.0,0.0,0.0,math.log(float(identity["period_multiplier"]))]
    levels=[]
    for i,eps in enumerate(values):
        atlas,_=collect_seed_family(knot_id,epsilon=eps,centerline_points=centerline_points,stations=stations,angles=angles,period_multipliers=(float(identity["period_multiplier"]),),force_python=force_python,auto_build=auto_build if i==0 else False)
        roots=[r for r in atlas["roots"] if r["classification"]=="RESOLVED_LOCAL_MINIMUM" and int(r["station"])==int(identity["station"]) and int(r["angle_index"])==int(identity["angle_index"])]
        if not roots:
            levels.append({"epsilon_over_rc":eps,"status":"SEED_NOT_PRESENT"}); continue
        seed=_seed_from_root(roots[0],int(identity["direction_sign"]))
        shot=shoot_closed_orbit(curve,seed,epsilon=eps,step_count=step_count,max_iterations=max_iterations,force_python=force_python,auto_build=False,initial_parameters=params)
        if "best" in shot: params=shot["best"]["parameters"]
        levels.append({"epsilon_over_rc":eps,"status":shot["status"],"shot":shot})
    return {"schema":"sst.fermat.epsilon-continuation.v0.6.1","package_version":PACKAGE_VERSION,"knot_id":knot_id,"identity":identity,"levels":levels,"any_resolved":any(v.get("shot",{}).get("resolved_closed_orbit") for v in levels),"global_closed_orbit_certified":False,"qsm_certified":False}
