from __future__ import annotations
from pathlib import Path
import os, shutil, math, csv, statistics
from .atlas import load_atlas, validate_pd
from .geometry import build_embedding
from .backend import measure, backend_name, native_available
from .features import FEATURE_REGISTRY, PAIR_SPACES, PRIMARY_FEATURES, applicable_to_kind, pool_rows
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
    return out


def _relative_delta(a, b):
    den=max(abs(float(a)),abs(float(b)),1e-15)
    return abs(float(a)-float(b))/den


def _asinh_standardized(rows, features):
    transformed={}
    meta={}
    for feat in features:
        vals=[abs(float(r[feat])) for r in rows]
        positive=sorted(v for v in vals if v>0.0)
        scale=statistics.median(positive) if positive else 1.0
        if scale<=0.0: scale=1.0
        tx=[math.asinh(v/scale) for v in vals]
        transformed[feat]=zscores(tx)
        meta[feat]={"transform":"asinh(abs(x)/median_positive)","median_positive_scale":scale}
    return transformed,meta


def _pair_table(rows, features):
    if len(rows)<2:
        return [],{}
    z,meta=_asinh_standardized(rows,features)
    pairs=[]
    for i in range(len(rows)):
        for j in range(i+1,len(rows)):
            d=math.sqrt(sum((z[f][i]-z[f][j])**2 for f in features))
            pairs.append({"case_a":rows[i]["case_id"],"case_b":rows[j]["case_id"],
                          "kind_a":rows[i]["kind"],"kind_b":rows[j]["kind"],"distance":d})
    pairs.sort(key=lambda x:x["distance"])
    return pairs,meta


def _feature_qualified(row, feature):
    return bool(row.get(feature+"_qualified",False))


def run_blind(root: Path, config_path: Path, force_python=False, overwrite=False):
    cfg=load_json(config_path)
    out=root/cfg["output_dir"]
    if overwrite and out.exists(): shutil.rmtree(out)
    blind=out/"BLIND"; private=out/"PRIVATE_REVEAL_DO_NOT_INCLUDE_IN_BLIND"
    blind.mkdir(parents=True,exist_ok=True); private.mkdir(parents=True,exist_ok=True)

    atlas=load_atlas(root)
    if len(atlas)!=82: raise RuntimeError(f"Expected 82 atlas objects, got {len(atlas)}")
    for r in atlas: validate_pd(r)

    resolutions=sorted({int(x) for x in cfg["resolution_ladder"]})
    if len(resolutions)<2:
        raise ValueError("resolution_ladder must contain at least two distinct resolutions")
    primary_n=resolutions[-1]; previous_n=resolutions[-2]
    reps_n=int(cfg["embedding_replicates"])
    conv_tol=float(cfg["convergence_rel_tol"])
    cv_tol=float(cfg["embedding_cv_max"])

    secret=os.urandom(32)
    mapping={}; cases=[]
    for r in atlas:
        cid=case_id(secret,r["id"])
        mapping[cid]=r["id"]
        cases.append({"case_id":cid,"kind":r["kind"],"crossings":r["crossings"],
                      "alternating":r.get("alternating"),"pd":r["pd"]})
    cases.sort(key=lambda x:x["case_id"])
    write_json(private/"mapping.json",mapping)
    (private/"secret.hex").write_text(secret.hex(),encoding="ascii")

    frozen=dict(cfg)
    frozen["backend"]=backend_name(force_python)
    frozen["native_available"]=native_available()
    frozen["primary_resolution"]=primary_n
    frozen["previous_resolution_for_gate"]=previous_n
    frozen["feature_registry"]=FEATURE_REGISTRY
    frozen["pair_spaces"]=PAIR_SPACES
    frozen["blind_forbidden_inputs"]=["reveal/historical_hypotheses.json","reveal/sm_reference_2026.json"]
    write_json(blind/"config_frozen.json",frozen)
    write_json(blind/"blind_cases.json",cases)
    commitment={
        "mapping_sha256":sha256_bytes(canonical(mapping)),
        "config_sha256":sha256_file(config_path),
        "atlas_sha256":sha256_file(root/"data"/"atlas_pd.json"),
        "provenance_sha256":sha256_file(root/"data"/"PROVENANCE.json"),
        "case_count":len(cases),
        "resolution_ladder":resolutions,
        "embedding_replicates":reps_n,
        "convergence_rel_tol":conv_tol,
        "embedding_cv_max":cv_tol,
        "canonical_constants_present_in_blind_config":False,
        "sm_reference_present_in_blind_config":False,
        "historical_particle_mapping_present_in_blind_config":False
    }
    write_json(blind/"PREREG_COMMITMENT.json",commitment)

    by_pd={sha256_bytes(canonical(r["pd"])):r for r in atlas}
    rows=[]; per_case_dir=blind/"cases"; per_case_dir.mkdir(exist_ok=True)
    for idx,c in enumerate(cases,1):
        rec=by_pd[sha256_bytes(canonical(c["pd"]))]
        per_resolution={}
        for npts in resolutions:
            reps=[]
            for rep in range(reps_n):
                geom=build_embedding(rec,npts,cfg["public_seed"],rep)
                reps.append(measure(geom,float(cfg["core_fraction"]),force_python=force_python))
            per_resolution[str(npts)]={"replicates":reps,"aggregate":_aggregate(reps)}
        hi=per_resolution[str(primary_n)]["aggregate"]
        mid=per_resolution[str(previous_n)]["aggregate"]
        row={"case_id":c["case_id"],"kind":c["kind"],"crossings":c["crossings"],
             "alternating":c.get("alternating"),**hi}
        qualifications={}
        for feat in PRIMARY_FEATURES:
            applicable=applicable_to_kind(feat,c["kind"])
            rd=_relative_delta(hi[feat],mid[feat]) if applicable else None
            hcv=float(hi[feat+"_cv"]) if applicable else None
            q=bool(applicable and rd<=conv_tol and hcv<=cv_tol)
            qualifications[feat]={"applicable":applicable,"resolution_rel_delta":rd,
                                  "embedding_cv":hcv,"qualified":q,
                                  "resolution_pair":[previous_n,primary_n]}
            row[feat+"_resolution_rel_delta"]=rd
            row[feat+"_qualified"]=q
        applicable_q=[v["qualified"] for v in qualifications.values() if v["applicable"]]
        applicable_cvs=[v["embedding_cv"] for v in qualifications.values() if v["applicable"] and v["embedding_cv"] is not None]
        row["embedding_robustness"]=math.exp(-mean(applicable_cvs)) if applicable_cvs else 0.0
        row["case_all_applicable_features_qualified"]=bool(applicable_q and all(applicable_q))
        rows.append(row)
        write_json(per_case_dir/f'{c["case_id"]}.json',{
            "case":c,"resolution_ladder":resolutions,"primary_resolution":primary_n,
            "per_resolution":per_resolution,"feature_qualification":qualifications,
            "primary_aggregate":hi
        })
        if idx%10==0 or idx==len(cases): print(f"[blind] {idx}/{len(cases)}")

    write_json(blind/"FEATURES.json",rows)
    fields=list(rows[0].keys())
    with (blind/"FEATURES.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

    pair_meta={}
    for space,spec in PAIR_SPACES.items():
        raw_rows=pool_rows(rows,spec["pool"])
        qualified_rows=[r for r in raw_rows if all(_feature_qualified(r,f) for f in spec["features"])]
        raw_pairs,raw_transform=_pair_table(raw_rows,spec["features"])
        qual_pairs,qual_transform=_pair_table(qualified_rows,spec["features"])
        stem=space.upper()
        write_json(blind/f"PAIRS_{stem}_RAW.json",raw_pairs)
        write_json(blind/f"PAIRS_{stem}_QUALIFIED.json",qual_pairs)
        write_json(blind/f"PAIRS_{stem}_NEIGHBORS.json",qual_pairs[:int(cfg["pair_top_n"])])
        pair_meta[space]={"pool":spec["pool"],"features":spec["features"],
                          "raw_case_count":len(raw_rows),"qualified_case_count":len(qualified_rows),
                          "raw_pair_count":len(raw_pairs),"qualified_pair_count":len(qual_pairs),
                          "raw_transform":raw_transform,"qualified_transform":qual_transform}
    write_json(blind/"PAIR_SPACE_METADATA.json",pair_meta)

    qual_counts={}
    for feat in PRIMARY_FEATURES:
        qual_counts[feat]={
            "knots":sum(r["kind"]=="knot" and r.get(feat+"_qualified",False) for r in rows),
            "links":sum(r["kind"]=="link" and r.get(feat+"_qualified",False) for r in rows),
            "all":sum(bool(r.get(feat+"_qualified",False)) for r in rows),
        }
    gate={
        "atlas_count":len(rows),"knot_count":sum(r["kind"]=="knot" for r in rows),
        "link_count":sum(r["kind"]=="link" for r in rows),"all_pd_valid":True,
        "backend":backend_name(force_python),"native_required_by_config":bool(cfg.get("strict_native",False)),
        "native_available":native_available(),"blind_measurement_complete":True,
        "resolution_ladder":resolutions,"primary_resolution":primary_n,
        "embedding_replicates":reps_n,"feature_qualified_case_counts":qual_counts,
        "pair_spaces":pair_meta,"contact_ratio_status":"DIAGNOSTIC_ONLY_RESOLUTION_DEPENDENT",
        "physical_interpretation_gate":"NOT_OPENED"
    }
    write_json(blind/"GATES.json",gate)
    report=f"""# A055 v0.1.1 — BLIND report

- Cases: **{len(rows)}** = 35 knots + 47 links.
- Backend: **{backend_name(force_python)}**.
- Resolution ladder: **{resolutions}** points/component.
- Primary resolution: **{primary_n}**; convergence gate uses **{previous_n} -> {primary_n}**.
- Embedding replicates per resolution: **{reps_n}**.
- Feature convergence tolerance: **{conv_tol:.3g}** relative.
- Embedding-CV tolerance: **{cv_tol:.3g}**.
- SM particle labels visible to blind stage: **no**.
- Historical particle mapping visible to blind stage: **no**.

## v0.1.1 corrections

`contact_ratio = min_distance / mean_segment` is retained only as a diagnostic because it explicitly changes when the discretization resolution changes.  The primary contact observable is now `min_distance` after the common mean-component-length normalization.

Feature domains are preregistered.  `linking_strength` is link-only and can no longer place knots at a numerical floor.  Mixed knot/link distance uses only bending, Neumann and minimum-distance observables with common semantics.  Knot-only and link-only distance spaces add their domain-specific observables.

Every primary feature receives its own resolution-convergence and embedding-stability gate.  Qualified pair tables contain only cases that pass all features required by that pair space.

## Scientific scope

These remain PD-derived screening observables, not PKLSA-relaxed vortex equilibria or particle masses.  The reveal stage may test preregistered mass-pattern resemblance only after the BLIND tree is sealed.
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
