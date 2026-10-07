from __future__ import annotations
from pathlib import Path
import os, math, csv, shutil, json
from .atlas import load_atlas, validate_pd
from .dynamics_v2 import inspect_static, run_knot_dynamic
from .util import *
from .workbench import detect_workbench_root, find_c006_version
from .backend import native_available
from .c006_bridge import native_preflight

def _median(xs):
    xs=sorted(float(x) for x in xs)
    if not xs:return None
    n=len(xs); return xs[n//2] if n%2 else .5*(xs[n//2-1]+xs[n//2])

def run_blind(root:Path,config_path:Path,workbench_root=None,force_python=False,overwrite=False):
    cfg=load_json(config_path); out=root/cfg["output_dir"]
    if overwrite and out.exists(): shutil.rmtree(out)
    blind=out/"BLIND"; private=out/"PRIVATE_REVEAL_DO_NOT_INCLUDE_IN_BLIND"
    blind.mkdir(parents=True,exist_ok=True); private.mkdir(parents=True,exist_ok=True)
    atlas=load_atlas(root)
    for r in atlas: validate_pd(r)
    wb=None; c006_preflight=None
    if cfg["geometry_mode"]=="workbench_pklsa":
        wb=detect_workbench_root(workbench_root)
        if force_python and cfg.get("c006_native",{}).get("required",True):
            raise RuntimeError("C006_NATIVE_REQUIRED: --force-python is forbidden for production campaigns")
        if cfg.get("c006_native",{}).get("required",True):
            c006_preflight=native_preflight(find_c006_version(wb),cfg["c006_native"])
    secret=os.urandom(32); mapping={}; cases=[]
    for r in atlas:
        cid=case_id(secret,r["id"]); mapping[cid]=r["id"]
        cases.append({"case_id":cid,"kind":r["kind"],"crossings":r["crossings"],"alternating":r.get("alternating")})
    cases.sort(key=lambda x:x["case_id"])
    write_json(private/"mapping.json",mapping); (private/"secret.hex").write_text(secret.hex(),encoding="ascii")
    frozen=dict(cfg); frozen["workbench_root"]=str(wb) if wb else None
    frozen["blind_forbidden_inputs"]=["reveal/historical_hypotheses.json","reveal/sm_reference_2026.json"]
    write_json(blind/"config_frozen.json",frozen)
    if c006_preflight is not None:
        write_json(blind/"C006_NATIVE_PREFLIGHT.json",c006_preflight)
    write_json(blind/"PREREG_COMMITMENT.json",{
        "config_sha256":sha256_file(config_path),"atlas_sha256":sha256_file(root/"data"/"atlas_pd.json"),
        "case_count":len(cases),"target_blind":True,"historical_mapping_visible":False,"sm_reference_visible":False,
        "geometry_mode":cfg["geometry_mode"],"workbench_root":str(wb) if wb else None})
    byid={r["id"]:r for r in atlas}; rows=[]; dyn_dir=blind/"dynamics"; dyn_dir.mkdir(exist_ok=True)
    for i,c in enumerate(cases,1):
        tid=mapping[c["case_id"]]; rec=byid[tid]
        if wb is None:
            static={"status":"PORTABLE_CI_NO_WORKBENCH","static_anchors":[]}
        else:
            static=inspect_static(wb,tid,cfg["e011_provider_groups"])
        dyn={"status":"NOT_ATTEMPTED"}
        eligible=bool(wb and static.get("status")=="STATIC_READY")
        if rec["kind"]=="link":
            dyn={"status":"LINK_DYNAMICS_NOT_IMPLEMENTED_V0_2",
                 "reason":"C006-v0.3.0/E012-v0.2.0 authoritative contract is one-centerline counter-channel dynamics; v0.2.1 fails closed for multi-component links."}
        elif eligible:
            try:
                dyn=run_knot_dynamic(wb,tid,cfg,force_python=force_python)
                cov=dyn.get("provider_coverage",{}).get("status")
                dyn["status"]="SINGLE_PROVIDER_ONLY" if cov=="SINGLE_PROVIDER_ONLY" else "COMPLETED"
            except Exception as e:
                dyn={"status":"DYNAMIC_FAIL_CLOSED","error":repr(e)}
        # Blind summary contains no topology ID.
        anchors=static.get("static_anchors",[])
        rops=[a["Rop"] for a in anchors if isinstance(a.get("Rop"),(int,float))]
        wrs=[a["Wr"] for a in anchors if isinstance(a.get("Wr"),(int,float))]
        modes=dyn.get("agreed_modes",[]) if isinstance(dyn,dict) else []
        row={"case_id":c["case_id"],"kind":rec["kind"],"crossings":rec["crossings"],
             "static_status":static.get("status"),"static_provider_count":len(anchors),
             "ropelength_hat":_median(rops),"abs_writhe_hat":abs(_median(wrs)) if wrs else None,
             "dynamic_status":dyn.get("status"),"dimensionless_dynamic_qualified":bool(dyn.get("dimensionless_dynamic_qualified",False)),
             "true_floquet_qualified":bool(dyn.get("true_floquet_qualified",False)),
             "particle_promotion_qualified":bool(dyn.get("particle_promotion_qualified",False)),
             "qualified_mode_count":len(modes)}
        for m in range(1,int(cfg["dynamic_feature_mode_count"])+1):
            x=next((x for x in modes if int(x["mode_m"])==m),None)
            row[f"omega_m{m}_hat"]=x.get("omega_hat") if x else None
            row[f"kD_m{m}"]=x.get("kD") if x else None
        fl=dyn.get("true_floquet",[])
        good=[x for x in fl if x.get("accepted")]
        row["true_floquet_phase_abs_hat"]=_median([abs(x["phase_turns"]) for x in good]) if good else None
        row["true_floquet_moddev_hat"]=_median([x["multiplier_modulus_deviation_max"] for x in good]) if good else None
        rows.append(row)
        write_json(dyn_dir/f'{c["case_id"]}.json',{"case":c,"static":static,"dynamic":dyn})
        if i%5==0 or i==len(cases): print(f"[A055 v0.2.1 blind] {i}/{len(cases)}")
    write_json(blind/"FEATURES.json",rows)
    with (blind/"FEATURES.csv").open("w",newline="",encoding="utf-8") as f:
        fields=list(rows[0].keys()); w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    counts={"static_ready":sum(r["static_status"]=="STATIC_READY" for r in rows),
            "single_provider_only":sum(r["dynamic_status"]=="SINGLE_PROVIDER_ONLY" for r in rows),
            "dynamic_fail_closed":sum(r["dynamic_status"]=="DYNAMIC_FAIL_CLOSED" for r in rows),
            "dynamic_completed":sum(r["dynamic_status"]=="COMPLETED" for r in rows),
            "dynamic_qualified":sum(r["dimensionless_dynamic_qualified"] for r in rows),
            "true_floquet_qualified":sum(r["true_floquet_qualified"] for r in rows),
            "particle_promotion_qualified":sum(r["particle_promotion_qualified"] for r in rows),
            "links_static_only":sum(r["kind"]=="link" and r["static_status"]=="STATIC_READY" for r in rows)}
    write_json(blind/"GATES.json",{"atlas_count":82,"counts":counts,"geometry_mode":cfg["geometry_mode"],
        "c006_native_preflight":c006_preflight,
        "provider_policy":"SINGLE_PROVIDER_MAY_RUN_DIAGNOSTIC_DYNAMICS_BUT_CANNOT_PROMOTE",
        "link_dynamic_policy":"FAIL_CLOSED_STATIC_ONLY_V0_2_1","true_floquet_policy":cfg["true_floquet"],
        "physical_particle_interpretation":"NOT_OPENED"})
    (blind/"REPORT_BLIND.md").write_text(f"""# A055 v0.2.1 — BLIND report

Population: **82** topologies (35 knots, 47 links).

Geometry authority: **{cfg['geometry_mode']}**.
Particle/SM labels visible: **no**.
Historical `5_2/6_1` mapping visible: **no**.

Production knot chain:
`E011 STATIC_READY providers -> E011 ropelength normalization -> C006 projected Kelvin generator -> eigenvector branch tracking -> same-generator RPO -> cross-provider agreement -> conditional true relative-return monodromy`.

Links fail closed at the dynamics boundary in v0.2.1.  Their static PKLSA/topology evidence is retained, but they cannot enter a dynamic particle-mass fit until a multi-component dynamics contract is separately implemented and preregistered.

Counts:
- STATIC_READY: {counts['static_ready']}
- SINGLE_PROVIDER_ONLY diagnostic dynamics: {counts['single_provider_only']}
- dynamic fail-closed: {counts['dynamic_fail_closed']}
- full-provider dynamics completed: {counts['dynamic_completed']}
- dimensionless dynamic qualified: {counts['dynamic_qualified']}
- true-Floquet qualified: {counts['true_floquet_qualified']}
- particle-promotion qualified: {counts['particle_promotion_qualified']}
""",encoding="utf-8")
    return out

def seal_blind(out:Path):
    blind=out/"BLIND"; files=sorted(p for p in blind.rglob("*") if p.is_file() and p.name!="BLIND_SEAL.json")
    manifest={str(p.relative_to(blind)).replace("\\","/"):sha256_file(p) for p in files}
    seal={"files":manifest,"manifest_sha256":sha256_bytes(canonical(manifest))}
    write_json(blind/"BLIND_SEAL.json",seal); return seal

def verify_seal(out:Path):
    blind=out/"BLIND"; seal=load_json(blind/"BLIND_SEAL.json")
    for rel,h in seal["files"].items():
        p=blind/rel
        if not p.exists() or sha256_file(p)!=h:return False,rel
    return True,seal["manifest_sha256"]
