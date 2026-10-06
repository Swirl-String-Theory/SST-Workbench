from __future__ import annotations
from pathlib import Path
import json, os, shutil, math, itertools, csv
from .atlas import load_atlas, validate_pd, component_cycles
from .geometry import build_embedding
from .backend import measure, backend_name, native_available
from .util import *

AGG_FEATURES=["total_length","bend_energy","min_distance","mean_segment","contact_ratio",
              "neumann_energy","abs_neumann_energy","writhe","abs_writhe",
              "linking_strength","linking_residual","component_count"]

def _aggregate(reps):
    out={}
    for k in AGG_FEATURES:
        vals=[float(r[k]) for r in reps]
        out[k]=mean(vals)
        out[k+"_cv"]=cv(vals)
    out["embedding_robustness"]=math.exp(-mean([out[x+"_cv"] for x in
        ["bend_energy","contact_ratio","abs_neumann_energy","abs_writhe","linking_strength"]]))
    return out

def run_blind(root: Path, config_path: Path, force_python=False, overwrite=False):
    cfg=load_json(config_path)
    out=root/cfg["output_dir"]
    if overwrite and out.exists(): shutil.rmtree(out)
    blind=out/"BLIND"; private=out/"PRIVATE_REVEAL_DO_NOT_INCLUDE_IN_BLIND"
    blind.mkdir(parents=True,exist_ok=True); private.mkdir(parents=True,exist_ok=True)

    atlas=load_atlas(root)
    if len(atlas)!=82: raise RuntimeError(f"Expected 82 atlas objects, got {len(atlas)}")
    for r in atlas: validate_pd(r)

    secret=os.urandom(32)
    mapping={}
    cases=[]
    for r in atlas:
        cid=case_id(secret,r["id"])
        mapping[cid]=r["id"]
        cases.append({
            "case_id":cid, "kind":r["kind"], "crossings":r["crossings"],
            "alternating":r.get("alternating"), "pd":r["pd"]
        })
    cases.sort(key=lambda x:x["case_id"])
    write_json(private/"mapping.json",mapping)
    (private/"secret.hex").write_text(secret.hex(),encoding="ascii")

    frozen=dict(cfg)
    frozen["backend"]=backend_name(force_python)
    frozen["native_available"]=native_available()
    frozen["blind_forbidden_inputs"]=["reveal/historical_hypotheses.json","reveal/sm_reference_2026.json"]
    write_json(blind/"config_frozen.json",frozen)
    write_json(blind/"blind_cases.json",cases)
    commitment={
        "mapping_sha256":sha256_bytes(canonical(mapping)),
        "config_sha256":sha256_file(config_path),
        "atlas_sha256":sha256_file(root/"data"/"atlas_pd.json"),
        "provenance_sha256":sha256_file(root/"data"/"PROVENANCE.json"),
        "case_count":len(cases),
        "canonical_constants_present_in_blind_config":False,
        "sm_reference_present_in_blind_config":False,
        "historical_particle_mapping_present_in_blind_config":False
    }
    write_json(blind/"PREREG_COMMITMENT.json",commitment)

    # case lookup by PD hash; source IDs are intentionally not carried into results
    by_pd={sha256_bytes(canonical(r["pd"])):r for r in atlas}
    rows=[]
    per_case_dir=blind/"cases"; per_case_dir.mkdir(exist_ok=True)
    for idx,c in enumerate(cases,1):
        rec=by_pd[sha256_bytes(canonical(c["pd"]))]
        reps=[]
        for rep in range(int(cfg["embedding_replicates"])):
            geom=build_embedding(rec,int(cfg["points_per_component"]),cfg["public_seed"],rep)
            m=measure(geom,float(cfg["core_fraction"]),force_python=force_python)
            reps.append(m)
        a=_aggregate(reps)
        row={"case_id":c["case_id"],"kind":c["kind"],"crossings":c["crossings"],
             "alternating":c.get("alternating"),**a}
        rows.append(row)
        write_json(per_case_dir/f'{c["case_id"]}.json',{"case":c,"replicates":reps,"aggregate":a})
        if idx%10==0 or idx==len(cases):
            print(f"[blind] {idx}/{len(cases)}")

    write_json(blind/"FEATURES.json",rows)
    fields=list(rows[0].keys())
    with (blind/"FEATURES.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

    # Unsupervised feature-space pair distances: fixed before reveal.
    feats=cfg["feature_set"]
    zs={}
    for feat in feats:
        vals=[math.log(max(1e-15,abs(float(r[feat])))) for r in rows]
        zs[feat]=zscores(vals)
    pairs=[]
    for i in range(len(rows)):
        for j in range(i+1,len(rows)):
            d=math.sqrt(sum((zs[f][i]-zs[f][j])**2 for f in feats))
            pairs.append({"case_a":rows[i]["case_id"],"case_b":rows[j]["case_id"],
                          "kind_a":rows[i]["kind"],"kind_b":rows[j]["kind"],"distance":d})
    pairs.sort(key=lambda x:x["distance"])
    write_json(blind/"PAIR_NEIGHBORS.json",pairs[:int(cfg["pair_top_n"])])
    write_json(blind/"PAIR_ALL.json",pairs)

    gate={
        "atlas_count":len(rows),
        "knot_count":sum(r["kind"]=="knot" for r in rows),
        "link_count":sum(r["kind"]=="link" for r in rows),
        "all_pd_valid":True,
        "backend":backend_name(force_python),
        "native_required_by_config":bool(cfg.get("strict_native",False)),
        "native_available":native_available(),
        "blind_measurement_complete":True,
        "physical_interpretation_gate":"NOT_OPENED"
    }
    write_json(blind/"GATES.json",gate)
    report=f"""# A054 v0.1.0 — BLIND report

- Cases: **{len(rows)}** = 35 knots + 47 links.
- Backend: **{backend_name(force_python)}**.
- SM particle labels visible to blind stage: **no**.
- Historical particle mapping visible to blind stage: **no**.
- PD-derived embedding ensemble: {cfg["embedding_replicates"]} replicates, {cfg["points_per_component"]} points/component.
- Main output: frozen feature vectors and unsupervised pair-neighbor distances.

## Scientific scope

The Gauss/Neumann, bending, contact and presentation-robustness quantities in v0.1.0 are **screening observables** on deterministic 3D realizations of the PD presentations. They are not PKLSA-relaxed ideal geometry, not a solved Euler vortex, and not particle masses. A particle claim is therefore prohibited at this stage.

The reveal layer may test whether pre-existing hypotheses or SM mass-ratio patterns are unusually close to the frozen spectrum, with explicit look-elsewhere diagnostics.
"""
    (blind/"REPORT_BLIND.md").write_text(report,encoding="utf-8")
    return out

def seal_blind(out: Path):
    blind=out/"BLIND"
    files=sorted(p for p in blind.rglob("*") if p.is_file() and p.name!="BLIND_SEAL.json")
    manifest={str(p.relative_to(blind)).replace("\\","/"):sha256_file(p) for p in files}
    seal={"files":manifest,"manifest_sha256":sha256_bytes(canonical(manifest))}
    write_json(blind/"BLIND_SEAL.json",seal)
    return seal

def verify_seal(out: Path):
    blind=out/"BLIND"; seal=load_json(blind/"BLIND_SEAL.json")
    current={}
    for rel,h in seal["files"].items():
        p=blind/rel
        if not p.exists(): return False,f"missing {rel}"
        current[rel]=sha256_file(p)
    if current!=seal["files"]: return False,"hash mismatch"
    return True,seal["manifest_sha256"]
