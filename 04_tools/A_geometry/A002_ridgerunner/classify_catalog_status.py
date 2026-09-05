#!/usr/bin/env python3
"""
Classify a KnotPlot/ridgerunner outdir into catalog status levels:

  stalled-not-converged | relaxed-seed | near-ideal-candidate |
  converged-local-candidate | near-ideal | certified-ideal

Writes outdir/catalog_status.json. Never auto-assigns certified-ideal.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


REF_PATH = Path(__file__).resolve().parent / "reference_ropelengths.json"
EQUIV_PATH = Path(__file__).resolve().parent / "topology_equivalents.json"

# Candidate gate (default -rr polish)
CAND_RESIDUAL = 0.01
# Strict near-ideal
STRICT_RESIDUAL = 0.005
STRICT_EPS_R = 0.0005  # 0.05%
STRICT_MULTISTART = 0.0002  # 0.02%
STRICT_RES_CONV = 0.0002  # 0.02% Δ_600→1200
STRICT_THICKNESS = 0.0001  # 0.01% from 0.5
UNIFORM_EDGE_RATIO = 1.02
UNIFORM_EDGE_CV = 0.005  # 0.5%
TARGET_THICKNESS = 0.5
CAMPAIGN_SOURCE = "campaign-best"
ANALYTIC_CIRCLE_SOURCE = "analytic-circle"


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_references() -> dict[str, Any]:
    if not REF_PATH.is_file():
        return {}
    return json.loads(REF_PATH.read_text(encoding="utf-8"))


def load_equivalents() -> list[dict[str, Any]]:
    data = load_json(EQUIV_PATH) or {}
    groups = data.get("groups") or []
    return list(groups) if isinstance(groups, list) else []


def folder_lookup_keys(folder_name: str) -> list[str]:
    keys = [folder_name]
    for prefix in ("knot_", "torus_", "link_"):
        if folder_name.startswith(prefix):
            keys.append(folder_name[len(prefix) :].replace(".", "_"))
            keys.append(folder_name[len(prefix) :])
            break
    return keys


def resolve_external_reference(
    folder_name: str, refs: dict[str, Any]
) -> tuple[float | None, str | None]:
    """External reference only (never campaign-best / best-known numerical)."""
    keys = folder_lookup_keys(folder_name)
    for key in keys:
        if key in refs and "ropelength" in refs[key]:
            return float(refs[key]["ropelength"]), str(
                refs[key].get("source", key)
            )
        for _k, v in refs.items():
            aliases = v.get("aliases") or []
            if key in aliases and "ropelength" in v:
                return float(v["ropelength"]), str(v.get("source", _k))
    return None, None


def campaign_reference(polish_ropes: list[float]) -> tuple[float | None, str]:
    if polish_ropes:
        return min(polish_ropes), CAMPAIGN_SOURCE
    return None, "none"


def equivalent_group_for(folder_name: str) -> dict[str, Any] | None:
    for group in load_equivalents():
        members = group.get("members") or []
        if folder_name in members:
            return group
    return None


def peer_ropelengths(outdir: Path, folder_name: str) -> list[float]:
    """Ropelengths from equivalent topology folders (siblings of outdir)."""
    group = equivalent_group_for(folder_name)
    if not group:
        return []
    parent = outdir.parent
    ropes: list[float] = []
    for member in group.get("members") or []:
        if member == folder_name:
            continue
        peer = parent / member
        if not peer.is_dir():
            continue
        for _path, data in find_polish_metrics(peer):
            rop = data.get("ropelength")
            if rop is not None:
                ropes.append(float(rop))
    return ropes


def find_polish_metrics(outdir: Path) -> list[tuple[Path, dict[str, Any]]]:
    """N=300 polish metrics only (exclude N600/N1200 ladder labels)."""
    hits: list[tuple[Path, dict[str, Any]]] = []
    for p in sorted(outdir.glob("*_polish.metrics.json")):
        name = p.name.lower()
        if "n600" in name or "n1200" in name or "uniform" in name:
            continue
        data = load_json(p)
        if data:
            hits.append((p, data))
    return hits


def find_analytic_geometry(outdir: Path) -> Path | None:
    for p in sorted(outdir.glob("*_analytic_D1.txt")):
        if p.is_file():
            return p
    for p in sorted(outdir.glob("*analytic*.txt")):
        if "uniform" in p.name.lower():
            continue
        if p.is_file():
            return p
    return None


def pick_primary_polish(
    outdir: Path, polishes: list[tuple[Path, dict[str, Any]]]
) -> tuple[Path, dict[str, Any]] | None:
    if not polishes:
        return None
    # Unknot: do not treat RR polish as canonical baseline.
    if outdir.name == "knot_0.1":
        analytic = find_analytic_geometry(outdir)
        if analytic is not None:
            return analytic, {
                "ropelength": 2.0 * math.pi,
                "residual": 0.0,
                "thickness": 0.5,
                "stop_reason": "analytic",
                "residual_converged": True,
                "analytic": True,
            }
    sel = load_json(outdir / "seed_selection.json") or {}
    selected = sel.get("selected")
    if selected:
        stem = Path(selected).stem
        matches = [
            (path, data)
            for path, data in polishes
            if stem in path.name or path.name.startswith(stem) or stem in path.stem
        ]
        if matches:
            return min(
                matches,
                key=lambda t: (
                    t[1].get("residual")
                    if t[1].get("residual") is not None
                    else float("inf")
                ),
            )
    # Prefer lowest residual
    return min(
        polishes,
        key=lambda t: (
            t[1].get("residual")
            if t[1].get("residual") is not None
            else float("inf")
        ),
    )


def find_ladder_metrics(outdir: Path, tag: str) -> dict[str, Any] | None:
    """tag = N600_polish or N1200_polish."""
    for p in outdir.glob(f"*_{tag}.metrics.json"):
        return load_json(p)
    for p in outdir.glob(f"*{tag}*.metrics.json"):
        if "uniform" in p.name.lower():
            continue
        return load_json(p)
    return None


def find_uniform_resample(outdir: Path, polish_stem: str | None) -> dict[str, Any] | None:
    cands = list(outdir.glob("*_polish_uniform_N*.resample.json"))
    if not cands:
        cands = list(outdir.glob("*_uniform_N*.resample.json"))
    if not cands:
        return None
    if polish_stem:
        preferred: list[Path] = []
        for c in cands:
            if polish_stem.replace("_polish", "") in c.stem or polish_stem in c.stem:
                preferred.append(c)
        if preferred:
            cands = preferred
    cands = sorted(cands, key=lambda p: p.stat().st_mtime)
    return load_json(cands[-1])


def check_pass_fail(ok: bool | None) -> str:
    if ok is None:
        return "not-tested"
    return "pass" if ok else "fail"


def parse_stop_residual_from_metrics(pm: dict[str, Any]) -> float | None:
    args = pm.get("ridgerunner_args") or []
    if isinstance(args, list):
        for arg in args:
            if isinstance(arg, str) and arg.startswith("--StopResidual="):
                try:
                    return float(arg.split("=", 1)[1])
                except ValueError:
                    return None
    return None


def is_stalled_polish(pm: dict[str, Any], residual: Any) -> bool:
    """Stop20/max-steps (or non-converged) with residual above candidate gate."""
    if pm.get("analytic"):
        return False
    if residual is None:
        return False
    try:
        res = float(residual)
    except (TypeError, ValueError):
        return False
    if res <= CAND_RESIDUAL:
        return False
    if pm.get("residual_converged") is True:
        return False
    stop_reason = pm.get("stop_reason")
    if stop_reason in ("stop20", "max_steps", "stop_time"):
        return True
    if pm.get("residual_converged") is False:
        return True
    stage_res = parse_stop_residual_from_metrics(pm)
    if stage_res is not None and res > stage_res:
        return True
    return False


def _normalize_dowker_tokens(code: str) -> list[int]:
    toks = re.findall(r"-?\d+", code)
    return [int(t) for t in toks]


def dowker_sign_pattern(code: str | None) -> str | None:
    if not code:
        return None
    toks = _normalize_dowker_tokens(code)
    if not toks:
        return None
    return "".join("+" if t > 0 else "-" for t in toks)


def chirality_metadata(
    outdir: Path, folder_name: str, seed: dict[str, Any]
) -> dict[str, Any]:
    group = equivalent_group_for(folder_name)
    local_dowker = None
    # Prefer checkpoint sidecars / seed selection
    for key in ("dowker_code", "dowker"):
        if seed.get(key):
            local_dowker = str(seed.get(key))
            break
    if local_dowker is None:
        for sc in sorted(outdir.glob("*.knotplot.json")):
            data = load_json(sc) or {}
            if data.get("dowker_code"):
                local_dowker = str(data["dowker_code"])
                break
    local_pat = dowker_sign_pattern(local_dowker)
    aliases = list((group or {}).get("catalog_aliases") or [])
    chirality = None
    catalog_aliases = list(aliases)
    if group and group.get("chirality_pair") and local_pat:
        # Convention: majority '+' → R, majority '-' → L (trefoil pair).
        plus = local_pat.count("+")
        minus = local_pat.count("-")
        if plus > minus:
            chirality = "R"
            catalog_aliases = list(dict.fromkeys([*aliases, "3_1_R"]))
        elif minus > plus:
            chirality = "L"
            catalog_aliases = list(dict.fromkeys([*aliases, "3_1_L"]))
    return {
        "dowker_code": local_dowker,
        "dowker_sign_pattern": local_pat,
        "chirality": chirality,
        "catalog_aliases": catalog_aliases,
        "equivalent_group": (group or {}).get("id"),
    }


def classify(outdir: Path) -> dict[str, Any]:
    outdir = outdir.resolve()
    refs = load_references()
    seed = load_json(outdir / "seed_selection.json") or {}
    topo = seed.get("topology_status", "")
    topo_ok = topo == "topology-verified" or "verified" in str(topo).lower()

    polishes = find_polish_metrics(outdir)
    primary = pick_primary_polish(outdir, polishes)
    chirality = chirality_metadata(outdir, outdir.name, seed)

    reasons: list[str] = []
    checks: dict[str, str] = {}

    if primary is None:
        # Analytic unknot without polish still classifies.
        if outdir.name == "knot_0.1":
            analytic = find_analytic_geometry(outdir)
            if analytic is not None:
                primary = (
                    analytic,
                    {
                        "ropelength": 2.0 * math.pi,
                        "residual": 0.0,
                        "thickness": 0.5,
                        "stop_reason": "analytic",
                        "residual_converged": True,
                        "analytic": True,
                    },
                )
                topo_ok = True
        if primary is None:
            status = "relaxed-seed"
            reasons.append("no ridgerunner polish metrics found")
            checks["topology"] = check_pass_fail(topo_ok if seed else None)
            return {
                "status": status,
                "ideal": False,
                "strict_near_ideal": False,
                "folder": outdir.name,
                "reference": None,
                "campaign_reference": None,
                "epsilon_R": None,
                "primary_polish": None,
                "checks": checks,
                "reason": reasons,
                "chirality": chirality.get("chirality"),
                "catalog_aliases": chirality.get("catalog_aliases"),
                "dowker_code": chirality.get("dowker_code"),
            }

    ppath, pm = primary
    residual = pm.get("residual")
    ropelength = pm.get("ropelength")
    thickness = pm.get("thickness")
    edge_ratio = pm.get("edge_length_ratio")
    edge_cv = pm.get("edge_length_cv")
    analytic = bool(pm.get("analytic"))

    ropes = [
        float(d["ropelength"])
        for _, d in polishes
        if d.get("ropelength") is not None
    ]
    camp_rop, camp_src = campaign_reference(ropes)
    r_ref, r_src = resolve_external_reference(outdir.name, refs)
    # Cross-route min can act as independent numerical reference for ε_R when
    # no external table entry exists — but only if peer spread is tight.
    peer_ropes = peer_ropelengths(outdir, outdir.name)
    external_ref_ok = r_ref is not None and r_src not in (
        None,
        CAMPAIGN_SOURCE,
        "best-known numerical",
        "none",
    )

    eps_r = None
    if r_ref and ropelength is not None and r_ref > 0:
        eps_r = (float(ropelength) - r_ref) / r_ref

    # Topology
    if analytic:
        topo_ok = True
    checks["topology"] = check_pass_fail(topo_ok)
    if topo_ok:
        reasons.append("topology verified")
    else:
        reasons.append("topology not verified")

    # Candidate residual
    cand_res_ok = residual is not None and float(residual) <= CAND_RESIDUAL
    checks["residual_candidate"] = check_pass_fail(cand_res_ok)
    if cand_res_ok:
        reasons.append(f"residual <= {CAND_RESIDUAL}")
    else:
        reasons.append(f"residual above {CAND_RESIDUAL}")

    # Strict residual
    strict_res_ok = residual is not None and float(residual) <= STRICT_RESIDUAL
    checks["residual_strict"] = check_pass_fail(strict_res_ok)
    if not strict_res_ok:
        reasons.append(f"residual above {STRICT_RESIDUAL}")

    # epsilon_R — only meaningful with an external reference
    if external_ref_ok and eps_r is not None:
        eps_ok = eps_r <= STRICT_EPS_R
        checks["ropelength_excess"] = check_pass_fail(eps_ok)
        if eps_ok:
            reasons.append("ropelength threshold passed (external reference)")
        else:
            reasons.append(
                f"ropelength excess {eps_r:.6%} above {STRICT_EPS_R:.2%}"
            )
    else:
        eps_ok = False
        checks["ropelength_excess"] = "not-tested"
        reasons.append(
            "ropelength_excess not tested (no external reference; "
            "campaign-best is not proof of near-ideal)"
        )

    # Raw RR edges → warn only
    if edge_ratio is not None and float(edge_ratio) > 1.10:
        checks["raw_edge_ratio"] = "warn"
        reasons.append(f"raw edge-ratio {edge_ratio:.4g} (warn only)")
    else:
        checks["raw_edge_ratio"] = "pass" if edge_ratio is not None else "not-tested"
    if edge_cv is not None and float(edge_cv) > 0.01:
        checks["raw_edge_cv"] = "warn"
        reasons.append(f"raw edge-CV {float(edge_cv):.4%} (warn only)")
    else:
        checks["raw_edge_cv"] = "pass" if edge_cv is not None else "not-tested"

    # Thickness
    thick_ok = None
    if thickness is not None:
        thick_ok = (
            abs(float(thickness) - TARGET_THICKNESS) / TARGET_THICKNESS
            <= STRICT_THICKNESS
        )
    checks["thickness"] = check_pass_fail(thick_ok)

    # Multi-start: in-folder polishes + equivalent topology peers
    all_ropes = list(ropes)
    all_ropes.extend(peer_ropes)
    ms_ok = None
    if len(all_ropes) >= 2:
        rmin, rmax = min(all_ropes), max(all_ropes)
        spread = (rmax - rmin) / rmin if rmin > 0 else None
        ms_ok = spread is not None and spread <= STRICT_MULTISTART
        checks["multistart_spread"] = check_pass_fail(ms_ok)
        if ms_ok:
            reasons.append("multi-start / mirror ropelength spread OK")
        else:
            reasons.append(
                f"multi-start / mirror spread above {STRICT_MULTISTART:.2%}"
            )
    else:
        checks["multistart_spread"] = "not-tested"
        reasons.append("multi-start not tested")

    # Resolution convergence N600 / N1200
    m600 = find_ladder_metrics(outdir, "N600_polish")
    m1200 = find_ladder_metrics(outdir, "N1200_polish")
    res_conv_ok = None
    if m600 and m1200:
        r600 = m600.get("ropelength")
        r1200 = m1200.get("ropelength")
        res600 = m600.get("residual")
        res1200 = m1200.get("residual")
        res_ok = (
            res600 is not None
            and res1200 is not None
            and float(res600) <= STRICT_RESIDUAL
            and float(res1200) <= STRICT_RESIDUAL
        )
        if r600 and r1200 and float(r1200) > 0:
            delta = abs(float(r1200) - float(r600)) / float(r1200)
            res_conv_ok = res_ok and delta <= STRICT_RES_CONV
        else:
            res_conv_ok = False
        checks["resolution_convergence"] = check_pass_fail(res_conv_ok)
        if res_conv_ok:
            reasons.append("resolution convergence 600->1200 OK")
        else:
            reasons.append("resolution convergence failed")
    else:
        checks["resolution_convergence"] = "not-tested"
        reasons.append("resolution convergence not yet demonstrated")

    # Uniform VortexLab mesh
    u = find_uniform_resample(outdir, ppath.stem if not analytic else None)
    uni_ok = None
    if u:
        comps = u.get("components") or []
        if comps:
            uni_ok = True
            for c in comps:
                if c.get("edge_ratio") is not None and float(c["edge_ratio"]) > UNIFORM_EDGE_RATIO:
                    uni_ok = False
                if c.get("edge_cv") is not None and float(c["edge_cv"]) > UNIFORM_EDGE_CV:
                    uni_ok = False
            ds = u.get("global_ds_ratio")
            if ds is not None and float(ds) > 1.05:
                uni_ok = False
                reasons.append(f"global_ds_ratio {float(ds):.4g} > 1.05")
        checks["uniform_mesh"] = check_pass_fail(uni_ok)
        if uni_ok:
            reasons.append("VortexLab uniform mesh OK")
        elif uni_ok is False:
            reasons.append("VortexLab uniform mesh gate failed")
    else:
        checks["uniform_mesh"] = "not-tested"

    # Constraint anomalies: residual missing / NaN
    anomaly = residual is None or (
        isinstance(residual, float) and not math.isfinite(residual)
    )
    checks["constraint_anomalies"] = "fail" if anomaly else "pass"

    stalled = is_stalled_polish(pm, residual)
    checks["residual_converged"] = check_pass_fail(
        True
        if pm.get("residual_converged") is True or analytic
        else (False if stalled or pm.get("residual_converged") is False else None)
    )

    candidate_ok = (
        topo_ok
        and cand_res_ok
        and checks["constraint_anomalies"] == "pass"
    )
    # Independent evidence required for near-ideal (external ref or mirror OK)
    independent_ok = bool(external_ref_ok and eps_ok) or (ms_ok is True)
    strict_ok = (
        candidate_ok
        and strict_res_ok
        and independent_ok
        and (eps_ok if external_ref_ok else True)
        and (ms_ok is True if ms_ok is not None else True)
        and res_conv_ok is True
        and thick_ok is True
        and uni_ok is True
    )
    local_converged = (
        candidate_ok
        and strict_res_ok
        and checks["constraint_anomalies"] == "pass"
        and not analytic
    )

    if analytic and outdir.name == "knot_0.1":
        status = "near-ideal"
        reasons.append("analytic circle is canonical 0_1")
        strict_ok = True
        checks["ropelength_excess"] = "pass"
        checks["residual_strict"] = "pass"
        checks["residual_candidate"] = "pass"
    elif strict_ok:
        status = "near-ideal"
    elif local_converged:
        status = "converged-local-candidate"
        if not independent_ok:
            reasons.append(
                "residual-converged local minimum without independent near-ideal proof"
            )
        else:
            reasons.append(
                "residual-converged local minimum; strict near-ideal gates incomplete"
            )
    elif candidate_ok:
        status = "near-ideal-candidate"
    elif stalled:
        status = "stalled-not-converged"
        reasons.append("stopped without residual convergence (stalled)")
    else:
        status = "relaxed-seed"

    ref_obj = None
    if r_ref is not None and r_src is not None:
        ref_obj = {"ropelength": r_ref, "source": r_src}
    camp_obj = None
    if camp_rop is not None:
        camp_obj = {"ropelength": camp_rop, "source": camp_src}

    return {
        "status": status,
        "ideal": False,
        "strict_near_ideal": bool(strict_ok),
        "folder": outdir.name,
        "reference": ref_obj,
        "campaign_reference": camp_obj,
        "epsilon_R": eps_r,
        "primary_polish": str(ppath),
        "primary_metrics": {
            "residual": residual,
            "ropelength": ropelength,
            "thickness": thickness,
            "edge_length_ratio": edge_ratio,
            "edge_length_cv": edge_cv,
            "stop_reason": pm.get("stop_reason"),
            "residual_converged": pm.get("residual_converged"),
            "analytic": analytic,
        },
        "checks": checks,
        "reason": reasons,
        "chirality": chirality.get("chirality"),
        "catalog_aliases": chirality.get("catalog_aliases"),
        "dowker_code": chirality.get("dowker_code"),
        "equivalent_group": chirality.get("equivalent_group"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("outdir", type=Path, help="knots/<id> folder")
    ap.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="default: outdir/catalog_status.json",
    )
    args = ap.parse_args()
    outdir = args.outdir.resolve()
    if not outdir.is_dir():
        print(f"ERROR: not a directory: {outdir}", file=sys.stderr)
        return 1
    result = classify(outdir)
    out = args.json_out or (outdir / "catalog_status.json")
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"status: {result['status']}")
    print(f"strict_near_ideal: {result['strict_near_ideal']}")
    print(f"epsilon_R: {result.get('epsilon_R')}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
