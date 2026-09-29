from __future__ import annotations
import argparse, csv, hashlib, json, os, platform, secrets, shutil, sys, time, zipfile
from pathlib import Path
import numpy as np
from .seed import base_centerline, localized_packet
from .spectral import wave_numbers, dealias_mask, rk4_step
from .diagnostics import diagnostics, blowup_fit
from .pklsa import (
    E010_VERSION, TOPOLOGY_ID, resolve_workbench_root, locate_e010, validate_e010_release,
    select_trefoil_carriers, load_carrier_centerline, canonicalize_centerline, sha256_file,
)

NAME = "SST_Euler_Regularity_BKM_Singularity_Gate"
VERSION = "v0.3.0"
CATALOG_ID = "A047"


def dump(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def blind_token(secret: bytes, text: str, n=16):
    return hashlib.sha256(secret + text.encode("utf-8")).hexdigest()[:n]


def make_packet_basis(principal):
    p = np.asarray(principal, float); p /= np.linalg.norm(p)
    ref = np.array([1., 0., 0.]) if abs(p[0]) < 0.8 else np.array([0., 1., 0.])
    a = np.cross(p, ref); a /= np.linalg.norm(a); return p, a


def run_one(centerline, spec, case_id, outdir):
    N = spec["N"]; L = spec["L"]; dt = spec["dt"]; T = spec["T"]
    uh = base_centerline(centerline, N, L, spec["core_sigma"])
    d0 = diagnostics(uh, L)
    if spec.get("packet_epsilon", 0.0) > 0:
        p, a = make_packet_basis(d0["principal_strain_vector"]); kv = spec["packet_k"] * p
        idx = d0["hot_index"]; dx = L / N; x0 = [-0.5 * L + (ii + 0.5) * dx for ii in idx]
        uh = localized_packet(uh, L, spec["packet_epsilon"], kv, a, x0, spec["packet_sigma"])
    kx, ky, kz, k2 = wave_numbers(N, L); mask = dealias_mask(N, kx, ky, kz); uh *= mask[None, ...]
    rows = []; bkm = 0.0; prev = None; t = 0.0; steps = int(round(T / dt)); sample_every = max(1, spec["sample_every"]); t0 = time.time()
    for step in range(steps + 1):
        if step % sample_every == 0 or step == steps:
            d = diagnostics(uh, L); d["t"] = float(t)
            if prev is not None: bkm += 0.5 * (prev["max_omega"] + d["max_omega"]) * (d["t"] - prev["t"])
            d["bkm_integral_sampled"] = float(bkm); rows.append(d); prev = d
        if step < steps: uh = rk4_step(uh, dt, L, mask); t += dt
    fit = blowup_fit([r["t"] for r in rows], [r["max_omega"] for r in rows])
    e0, e1 = rows[0]["energy"], rows[-1]["energy"]
    summary = {
        "case_id": case_id, "geometry_id": spec["geometry_id"], "group_id": spec["group_id"], "profile_id": spec["profile_id"],
        "N": N, "dt": dt, "T": T, "runtime_s": time.time() - t0,
        "energy_rel_drift": abs(e1 - e0) / max(abs(e0), 1e-30), "max_div_rms": max(r["div_rms"] for r in rows),
        "omega_growth": max(r["max_omega"] for r in rows) / rows[0]["max_omega"], "bkm_integral": rows[-1]["bkm_integral_sampled"],
        "blowup_fit": fit,
    }
    summary["numerically_valid"] = bool(summary["energy_rel_drift"] < spec["energy_drift_limit"] and summary["max_div_rms"] < spec["div_rms_limit"])
    dump(Path(outdir) / f"case_{case_id}_timeseries.json", rows); dump(Path(outdir) / f"case_{case_id}_summary.json", summary)
    return summary


def convergence_assessment(summaries):
    # Resolution convergence is never pooled across different centerlines or source families.
    by_geometry = {}
    for s in summaries: by_geometry.setdefault(s["geometry_id"], []).append(s)
    geometry_results = []; escalated = []
    for gid, rows in sorted(by_geometry.items()):
        valid = [x for x in rows if x["numerically_valid"]]
        candidates = [x for x in valid if x["blowup_fit"].get("candidate", False)]
        tstars = [x["blowup_fit"].get("t_star") for x in candidates if x["blowup_fit"].get("t_star")]
        distinct_N = len({x["N"] for x in candidates}); spread = None; conv = False
        if len(tstars) >= 3 and distinct_N >= 3:
            spread = (max(tstars) - min(tstars)) / np.mean(tstars); conv = spread < 0.10
        row = {"geometry_id": gid, "group_id": rows[0].get("group_id"), "valid_replays": len(valid), "candidate_replays": len(candidates),
               "candidate_distinct_N": distinct_N, "tstar_relative_spread": None if spread is None else float(spread), "converged_candidate": bool(conv)}
        geometry_results.append(row)
        if conv: escalated.append(gid)
    groups = {}
    for s in summaries:
        g = s.get("group_id") or "group_unspecified"
        groups.setdefault(g, {"geometry_ids": set(), "runs": 0, "valid_runs": 0, "candidate_runs": 0})
        groups[g]["geometry_ids"].add(s["geometry_id"]); groups[g]["runs"] += 1
        groups[g]["valid_runs"] += int(bool(s["numerically_valid"]))
        groups[g]["candidate_runs"] += int(bool(s["numerically_valid"] and s["blowup_fit"].get("candidate", False)))
    group_summary = [{"group_id": k, "geometry_count": len(v.pop("geometry_ids")), **v} for k, v in sorted(groups.items())]
    return {
        "verdict": "ESCALATE_BKM_CANDIDATE" if escalated else "NO_CONVERGED_BKM_CANDIDATE_IN_WINDOW",
        "geometry_count": len(by_geometry), "anonymous_independence_group_count": len(groups),
        "valid_runs": sum(x["numerically_valid"] for x in summaries),
        "candidate_runs": sum(bool(x["numerically_valid"] and x["blowup_fit"].get("candidate", False)) for x in summaries),
        "escalated_geometry_ids": escalated, "per_geometry": geometry_results, "per_anonymous_group": group_summary,
        "interpretation": "Finite-window numerical gate only. Different E010 carriers never count as resolution replications of one another. Independence groups are stratification labels, not replication multipliers. NO_CONVERGED does not prove Euler regularity."
    }


def write_summary_csv(path, summaries):
    fields = ["case_id", "geometry_id", "group_id", "profile_id", "N", "dt", "T", "runtime_s", "energy_rel_drift", "max_div_rms", "omega_growth", "bkm_integral", "numerically_valid"]
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for s in summaries: w.writerow({k: s.get(k) for k in fields})


def create_archives(root, outbase, reveal_dir):
    # Normalize every path into the same absolute coordinate system before
    # computing archive names.  On Windows Path.cwd() is absolute while the
    # default outbase is relative; mixing those forms makes relative_to() fail.
    root = Path(root).resolve()

    def _under_root(path):
        path = Path(path)
        return path.resolve() if path.is_absolute() else (root / path).resolve()

    outbase = _under_root(outbase)
    reveal_dir = _under_root(reveal_dir)
    archive_base = outbase.parent

    blind_zip = root.parent / f"{NAME}_{VERSION}-outputs_BLIND.zip"
    revealed_zip = root.parent / f"{NAME}_{VERSION}-outputs_REVEALED.zip"
    combined_zip = root.parent / f"{NAME}_{VERSION}-outputs.zip"

    def ztree(zpath, paths):
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for p in paths:
                p = _under_root(p)
                if p.is_file():
                    z.write(p, p.relative_to(archive_base))
                elif p.exists():
                    for f in p.rglob("*"):
                        if f.is_file():
                            z.write(f, f.relative_to(archive_base))

    ztree(blind_zip, [outbase / "BLIND"])
    ztree(revealed_zip, [outbase / "BLIND", reveal_dir])
    ztree(combined_zip, [outbase])
    return [str(blind_zip), str(revealed_zip), str(combined_zip)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/e010_v031_basic.json")
    ap.add_argument("--workbench-root", default=None)
    ap.add_argument("--e010-root", default=None)
    ap.add_argument("--e010-output", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-archives", action="store_true")
    args = ap.parse_args()
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    wb = resolve_workbench_root(args.workbench_root)
    e010_root, e010_out = locate_e010(wb, args.e010_root, args.e010_output)

    # Fail closed on the frozen E010-v0.3.1 source-native trefoil contract before any PDE work.
    release = validate_e010_release(e010_out, require_core_gates=cfg["dataset"].get("require_core_release_gates", True))
    selected, selection_audit, e010_summary = select_trefoil_carriers(e010_out, cfg["dataset"].get("selection", {}))

    outbase = Path(args.out or f"{NAME}_{VERSION}-outputs"); blind = outbase / "BLIND"; reveal = outbase / "REVEALED"
    if outbase.exists(): shutil.rmtree(outbase)
    blind.mkdir(parents=True); reveal.mkdir(parents=True)
    secret = secrets.token_bytes(32); base = cfg["base"]; profiles = cfg["profiles"]
    prepared = []; reveal_map = {}; census = []

    strict_raw = bool(cfg["dataset"].get("strict_raw_hash", True))
    strict_geometry = bool(cfg["dataset"].get("strict_geometry_hash", True))
    for carrier in selected:
        raw, source_audit = load_carrier_centerline(carrier, wb, e010_root, strict_raw_hash=strict_raw, strict_geometry_hash=strict_geometry)
        centerline, cmeta = canonicalize_centerline(raw, base["centerline_samples"], base["target_rms_radius"])
        gid = "geom_" + blind_token(secret, carrier.carrier_id, 16)
        source_group = carrier.independence_group or "UNSPECIFIED"
        group_id = "group_" + blind_token(secret, "independence|" + source_group, 12)
        census.append({"geometry_id": gid, "group_id": group_id, "component_count": 1, "input_points": int(len(raw)),
                       "canonical_coordinate_sha256": cmeta["canonical_coordinate_sha256"]})
        reveal_map[gid] = {
            "e010_carrier_id": carrier.carrier_id, "topology_id": TOPOLOGY_ID,
            "source_family": carrier.source_family, "source_role": carrier.source_role, "representation": carrier.representation,
            "catalog_id": carrier.catalog_id, "variant_id": carrier.variant_id,
            "independence_group": carrier.independence_group, "provider_group": carrier.provider_group,
            "lineage_group": carrier.lineage_group, "method_group": carrier.method_group,
            "evidence_independence_class": carrier.evidence_independence_class,
            "parent_source_family": carrier.parent_source_family,
            "literature_hard_gate_pass": carrier.literature_hard_gate_pass,
            "literature_gate_status": carrier.literature_gate_status,
            "e010_geometry_sha256": carrier.geometry_sha256,
            "source": source_audit, "carrier_metadata": carrier.metadata, "canonicalization": cmeta,
            "anonymous_group_id": group_id,
        }
        for profile in profiles:
            spec = {**base, **profile, "geometry_id": gid, "group_id": group_id, "profile_id": str(profile["id"])}
            cid = "case_" + blind_token(secret, carrier.carrier_id + "|" + json.dumps(profile, sort_keys=True), 16)
            prepared.append((centerline, spec, cid))
            reveal_map.setdefault("cases", {})[cid] = {"geometry_id": gid, "e010_carrier_id": carrier.carrier_id, "profile_id": profile["id"], "N": spec["N"], "dt": spec["dt"], "packet_epsilon": spec.get("packet_epsilon", 0.0)}

    e010_release_path = e010_out / "RELEASE.json"
    e010_summary_path = e010_out / "poc" / "atlas" / TOPOLOGY_ID / "qualification" / "summary.json"
    manifest = {
        "catalog_id": CATALOG_ID, "name": NAME, "version": VERSION,
        "epistemic_status": "E010-PKLSA-v0.3.1 source-native trefoil Euler/BKM numerical falsification gate; not a proof of regularity or singularity",
        "equation": "3D incompressible unforced Euler, periodic pseudo-spectral rotational form",
        "dataset": {
            "upstream": "E010 SST Parametric Knot-Link Seed Atlas v0.3.1 production 3_1 POC",
            "topology_id": TOPOLOGY_ID, "selected_geometry_count": len(selected),
            "anonymous_independence_group_count": len({x["group_id"] for x in census}),
            "selection_audit": selection_audit,
            "e010_release_sha256": sha256_file(e010_release_path), "e010_trefoil_summary_sha256": sha256_file(e010_summary_path),
            "dependency_policy": "Carriers within one E010 independence group are shape-population members, not independent confirmations. Mirrors/duplicates are excluded by default. Resolution convergence is assessed only within the same geometry."
        },
        "blind_census": census,
        "blind_cases": [{"case_id": cid, "geometry_id": spec["geometry_id"], "group_id": spec["group_id"], "profile_id": spec["profile_id"], "N": spec["N"], "dt": spec["dt"], "T": spec["T"]} for _, spec, cid in prepared],
        "common_numerics": {"L": base["L"], "core_sigma": base["core_sigma"], "target_rms_radius": base["target_rms_radius"], "centerline_samples": base["centerline_samples"], "sample_every": base["sample_every"], "energy_drift_limit": base["energy_drift_limit"], "div_rms_limit": base["div_rms_limit"]},
        "platform": {"python": sys.version, "platform": platform.platform(), "numpy": np.__version__},
    }
    dump(blind / "run_manifest.json", manifest)
    summaries = [run_one(centerline, spec, cid, blind) for centerline, spec, cid in prepared]
    assessment = convergence_assessment(summaries)
    dump(blind / "summary.json", {"assessment": assessment, "runs": summaries}); write_summary_csv(blind / "summary.csv", summaries)

    dump(reveal / "case_reveal_map.json", reveal_map)
    dump(reveal / "e010_pklsa_v031_provenance.json", {
        "workbench_root": str(wb), "e010_root": str(e010_root), "e010_output": str(e010_out),
        "e010_version": E010_VERSION, "e010_release": release, "e010_trefoil_poc_summary": e010_summary,
        "selection_audit": selection_audit,
        "scientific_boundary": "E010 qualifies geometry/source/topology. A047 separately tests finite-window Euler/BKM behavior. Neither layer by itself establishes SST particle stability."
    })
    v_swirl = 1.09384563e6; r_c = 1.40897017e-15; rho_f = 7.0e-7; t_c = r_c / v_swirl; omega_c = 2 * v_swirl / r_c
    dump(reveal / "sst_scale_mapping.json", {"v_swirl_m_s": v_swirl, "r_c_m": r_c, "rho_f_kg_m3": rho_f, "t_c_s": t_c, "omega_c_s_inv": omega_c, "mapping_note": "Blind solver used none of these values. Physical mapping remains post-hoc only."})
    archives = [] if args.no_archives else create_archives(Path.cwd(), outbase, reveal)
    print(json.dumps({"assessment": assessment, "selection_audit": selection_audit, "archives": archives, "output": str(outbase)}, indent=2))


if __name__ == "__main__": main()
