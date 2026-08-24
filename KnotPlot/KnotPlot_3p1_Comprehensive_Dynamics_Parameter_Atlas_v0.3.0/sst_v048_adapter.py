from __future__ import annotations
import argparse, csv, json, os, re, shutil, sys, time
from pathlib import Path
from collections import Counter

ATLAS=Path(__file__).resolve().parent
CONTRACT=json.loads((ATLAS/"sst_v048_bridge_contract.json").read_text(encoding="utf-8"))
DEFAULT_TARGET=Path(CONTRACT["target_default_path"])

def target_path(cli=None):
    p=(cli or os.environ.get("SST_V048_DIR") or str(DEFAULT_TARGET)).strip()
    return Path(p)

def pyexe(target):
    return target/".venv"/"Scripts"/"python.exe"

def load_version(target):
    p=target/"VERSION.json"
    if not p.is_file():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))

def preflight(target):
    required=[
        "VERSION.json","run_install.cmd",
        "sst_blind/multitopology.py","sst_blind/io.py","sst_blind/spectral_extension.py",
        CONTRACT["configs"]["screen"],CONTRACT["configs"]["spectral_k16"],
        CONTRACT["configs"]["spectral_k24"],CONTRACT["configs"]["spectral_k32"],
        CONTRACT["configs"]["spectral_k48"],CONTRACT["configs"]["spectral_k64"],
        CONTRACT["configs"]["spectral_plan"],CONTRACT["configs"]["full_confirm"],
    ]
    rows=[]
    for rel in required:
        q=target/rel
        rows.append((rel,q.is_file(),str(q)))
    ver=load_version(target)
    ok=all(x[1] for x in rows) and str(ver.get("version") or ver.get("package_version"))=="0.4.8"
    out={
        "target":str(target),
        "exists":target.is_dir(),
        "version":ver,
        "python":str(pyexe(target)),
        "venv_python_exists":pyexe(target).is_file(),
        "required_files":[{"path":r,"ok":o,"absolute":a} for r,o,a in rows],
        "ok_contract":ok,
    }
    (ATLAS/"analysis").mkdir(parents=True,exist_ok=True)
    (ATLAS/"analysis"/"SST_V048_PREFLIGHT.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print("SST v0.4.8 BRIDGE PREFLIGHT")
    print("="*78)
    print("Target :",target)
    print("Version:",ver.get("version") or ver.get("package_version"))
    for r,o,a in rows:
        print(("PASS" if o else "FAIL"),r)
    print("Venv   :",("PASS" if pyexe(target).is_file() else "MISSING"),pyexe(target))
    print("="*78)
    if not ok:
        print("PREFLIGHT FAILED: exact v0.4.8 contract is incomplete.")
        return 2
    print("PREFLIGHT CONTRACT PASS")
    if not pyexe(target).is_file():
        print("NOTE: venv missing; run target run_install.cmd before executing bridge stages.")
        return 3
    return 0

def import_target(target):
    # Important: native_ext/build paths and configs are relative to target root.
    os.chdir(target)
    sys.path.insert(0,str(target))
    from sst_blind.multitopology import run_panel
    from sst_blind.spectral_extension import load_rung_by_source,evaluate_triplet,write_extension_outputs
    return run_panel,load_rung_by_source,evaluate_triplet,write_extension_outputs

def read_screen_manifest():
    p=ATLAS/"stability_handoff"/"stability_candidates_screen.csv"
    if not p.is_file():
        raise FileNotFoundError(
            f"{p} missing. Run run_reanalyze_shape_and_prepare_stability.cmd first."
        )
    with p.open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    if not rows:
        raise RuntimeError("stability_candidates_screen.csv is empty")
    return rows

def sanitize_source(s):
    s=re.sub(r"[^A-Za-z0-9_.+-]+","_",str(s))
    return s[:180]

def build_entries():
    rows=read_screen_manifest()
    entries=[]; seen=set()
    for r in rows:
        h=r["raw_sha256"]
        if h in seen:
            continue
        seen.add(h)
        rel=r["raw_handoff_file"]
        q=(ATLAS/rel).resolve()
        if not q.is_file():
            raise FileNotFoundError(q)
        src=sanitize_source(r["candidate"])
        entries.append({
            "source":src,
            "kind":"knotplot",
            "topology_class":"knot",
            "canonical_id":"3_1",
            "path":str(q),
            "atlas_candidate":r["candidate"],
            "atlas_family":r["family"],
            "atlas_value":r.get("value"),
            "atlas_raw_sha256":h,
            "atlas_shape_classification":r.get("shape_classification"),
            "atlas_parameterization_role":r.get("parameterization_role"),
            "atlas_priority_tier":r.get("priority_tier"),
            "atlas_selection_reason":r.get("selection_reason"),
        })
    return entries

def ensure_output_root():
    p=ATLAS/"sst_v048_outputs"
    p.mkdir(parents=True,exist_ok=True)
    return p

def load_results_by_source(folder,load_rung_by_source):
    return load_rung_by_source(folder)

def write_flat_summary(folder,data):
    rows=[]
    for src,x in sorted(data.items()):
        r=x["result"]; g=r.get("gates",{}); m=r.get("metrics",{})
        rows.append({
            "source":src,
            "status":r.get("status"),
            "normalized_growth":m.get("normalized_growth"),
            "analysis_scope":m.get("analysis_scope"),
            "P0_geometry_core_clear":g.get("P0_geometry_core_clear"),
            "P1_jacobian_converged":g.get("P1_jacobian_converged"),
            "P2_linear_growth_bounded":g.get("P2_linear_growth_bounded"),
            "P3_nearest_relevant_separates":g.get("P3_nearest_relevant_separates"),
            "P4_TBK_collective_stabilizes":g.get("P4_TBK_collective_stabilizes"),
            "P5_short_ringdown_bounded":g.get("P5_short_ringdown_bounded"),
            "P7_RPO_recurrence":g.get("P7_RPO_recurrence"),
            "P8_Floquet_bounded":g.get("P8_Floquet_bounded"),
            "floquet_radius":(r.get("floquet",{}) or {}).get("spectral_radius_excluding_neutral"),
            "rpo_candidate":bool((r.get("rpo",{}) or {}).get("candidate") is not None),
            "core_clearance_radii":m.get("core_clearance_radii"),
        })
    if rows:
        p=Path(folder)/"ATLAS_BRIDGE_SUMMARY.csv"
        with p.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
            w.writeheader();w.writerows(rows)

def run_screen(target,backend="openmp"):
    run_panel,load_rung,_,_=import_target(target)
    entries=build_entries()
    out=ensure_output_root()/"01_screen_panel_extended_fp64"
    cfg=target/CONTRACT["configs"]["screen"]
    print(f"[ATLAS->SST] SCREEN entries={len(entries)} backend={backend}")
    final,_,_=run_panel(entries,cfg,out,backend=backend,resume=True)
    data=load_rung(out)
    write_flat_summary(out,data)
    print(json.dumps({"overall":final["overall"],"datasets":final["dataset_count"],"out":str(out)},indent=2))
    return 0

def spectral_stage(run_panel,load_rung,entries,cfg,out,backend):
    final,_,_=run_panel(entries,cfg,out,backend=backend,resume=True)
    return load_rung(out),final

def run_spectral(target,backend="sycl-dd32"):
    run_panel,load_rung,evaluate_triplet,write_extension_outputs=import_target(target)
    entries=build_entries()
    bysrc={e["source"]:e for e in entries}
    sources=set(bysrc)
    out=ensure_output_root()/"02_adaptive_spectral_v048"
    out.mkdir(parents=True,exist_ok=True)
    plan=json.loads((target/CONTRACT["configs"]["spectral_plan"]).read_text(encoding="utf-8"))
    policy=plan["policy"]
    (out/"SPECTRAL_EXTENSION_PLAN_PREREGISTERED.json").write_text(
        json.dumps(plan,indent=2)+"\n",encoding="utf-8"
    )
    data={}; growth={s:{} for s in sources}; decisions={}; stop_at={}

    specs=[
        (16,"00_S0_N720_K16",CONTRACT["configs"]["spectral_k16"]),
        (24,"01_S1_N720_K24",CONTRACT["configs"]["spectral_k24"]),
        (32,"02_S2_N720_K32",CONTRACT["configs"]["spectral_k32"]),
        (48,"03_S3_N720_K48",CONTRACT["configs"]["spectral_k48"]),
        (64,"04_S4_N720_K64",CONTRACT["configs"]["spectral_k64"]),
    ]

    active=set(sources)
    for k,dirname,cfgrel in specs:
        if k>=48 and not active:
            break
        stage_sources=sources if k<=32 else active
        selected=[bysrc[s] for s in sorted(stage_sources)]
        ro=out/dirname
        print("="*78)
        print(f"[ATLAS->SST] SPECTRAL k={k} active={len(selected)} backend={backend}")
        print("="*78)
        data[k],final=spectral_stage(run_panel,load_rung,selected,target/cfgrel,ro,backend)
        for s in stage_sources:
            growth[s][k]=float(data[k][s]["result"]["metrics"]["normalized_growth"])

        if k==32:
            newly=[]
            for s in sorted(active):
                d=evaluate_triplet([16,24,32],[data[16][s]["result"],data[24][s]["result"],data[32][s]["result"]],policy)
                decisions[s]=d
                if d["resolved"]:
                    stop_at[s]=32;newly.append(s)
            active-=set(newly)
            print(f"[ATLAS->SST] resolved@32={len(newly)} remaining={len(active)}")
        elif k==48:
            newly=[]
            for s in sorted(active):
                d=evaluate_triplet([24,32,48],[data[24][s]["result"],data[32][s]["result"],data[48][s]["result"]],policy)
                decisions[s]=d
                if d["resolved"]:
                    stop_at[s]=48;newly.append(s)
            active-=set(newly)
            print(f"[ATLAS->SST] resolved@48={len(newly)} remaining={len(active)}")
        elif k==64:
            for s in sorted(active):
                decisions[s]=evaluate_triplet([32,48,64],[data[32][s]["result"],data[48][s]["result"],data[64][s]["result"]],policy)

    records=[]
    for s in sorted(sources):
        d=decisions.get(s)
        if d is None:
            records.append({
                "source":s,"topology_class":"knot","canonical_id":"3_1",
                "classification":"INCOMPLETE","growth_verdict":None,
                "final_kmax":max(growth[s]) if growth[s] else None,
                "final_growth":growth[s].get(max(growth[s])) if growth[s] else None,
                "growth_by_k":{str(k):v for k,v in sorted(growth[s].items())},
                "decision":{},"reasons":["missing_required_spectral_rungs"],
            })
            continue
        if s in stop_at:
            k=stop_at[s]
            cls=f"SPECTRAL_CONVERGED_K{k}"
            reasons=[]
        else:
            k=64
            cls="SPECTRAL_UNRESOLVED_AT_K64"
            reasons=d.get("reasons",[])
        records.append({
            "source":s,"topology_class":"knot","canonical_id":"3_1",
            "classification":cls,
            "growth_verdict":d.get("growth_verdict"),
            "final_kmax":k,
            "final_growth":float(d["growth_values"][-1]),
            "growth_by_k":{str(kk):vv for kk,vv in sorted(growth[s].items())},
            "decision":d,"reasons":reasons,
        })
    write_extension_outputs(out,records,plan)
    print(json.dumps(dict(Counter(r["classification"] for r in records)),indent=2))
    return 0

def spectral_pass_sources():
    p=ensure_output_root()/"02_adaptive_spectral_v048"/"SPECTRAL_EXTENSION_RESULTS.json"
    if not p.is_file():
        raise FileNotFoundError("Run spectral stage first: "+str(p))
    d=json.loads(p.read_text(encoding="utf-8"))
    return {
        r["source"] for r in d.get("records",[])
        if str(r.get("classification","")).startswith("SPECTRAL_CONVERGED")
        and r.get("growth_verdict")=="PASS"
    }

def run_confirm(target,backend="openmp"):
    run_panel,load_rung,_,_=import_target(target)
    good=spectral_pass_sources()
    entries=[e for e in build_entries() if e["source"] in good]
    out=ensure_output_root()/"03_full_dynamics_R5_fp64"
    out.mkdir(parents=True,exist_ok=True)
    if not entries:
        (out/"NO_PROMOTED_CANDIDATES.txt").write_text(
            "No spectrally converged P2 PASS candidate was eligible for full-dynamics confirmation.\n",
            encoding="utf-8"
        )
        print("[ATLAS->SST] no candidates promoted to full dynamics.")
        return 0
    cfg=target/CONTRACT["configs"]["full_confirm"]
    print(f"[ATLAS->SST] FULL CONFIRM entries={len(entries)} backend={backend}")
    final,_,_=run_panel(entries,cfg,out,backend=backend,resume=True)
    data=load_rung(out)
    write_flat_summary(out,data)
    print(json.dumps({"overall":final["overall"],"datasets":final["dataset_count"],"out":str(out)},indent=2))
    return 0

def read_rung_if_exists(folder,load_rung):
    p=Path(folder)
    if (p/"unblind_manifest.json").is_file() and (p/"pre_unblind").is_dir():
        return load_rung(p)
    return {}

def read_atlas_handoff_map():
    p=ATLAS/"stability_handoff"/"stability_candidates_screen.csv"
    with p.open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    # sanitize source exactly as build_entries
    return {sanitize_source(r["candidate"]):r for r in rows}

def synthesize(target):
    _,load_rung,_,_=import_target(target)
    screen=read_rung_if_exists(ensure_output_root()/"01_screen_panel_extended_fp64",load_rung)
    confirm=read_rung_if_exists(ensure_output_root()/"03_full_dynamics_R5_fp64",load_rung)
    sp=ensure_output_root()/"02_adaptive_spectral_v048"/"SPECTRAL_EXTENSION_RESULTS.json"
    spectral={}
    if sp.is_file():
        d=json.loads(sp.read_text(encoding="utf-8"))
        spectral={r["source"]:r for r in d.get("records",[])}
    amap=read_atlas_handoff_map()
    sources=sorted(set(amap)|set(screen)|set(spectral)|set(confirm))
    rows=[]
    for s in sources:
        a=amap.get(s,{})
        sr=(screen.get(s) or {}).get("result",{})
        cr=(confirm.get(s) or {}).get("result",{})
        spec=spectral.get(s,{})
        sg=sr.get("gates",{}); sm=sr.get("metrics",{})
        cg=cr.get("gates",{}); cm=cr.get("metrics",{})
        cls=spec.get("classification")
        gv=spec.get("growth_verdict")
        if not spec:
            overall="NOT_SPECTRALLY_TESTED"
        elif cls=="SPECTRAL_UNRESOLVED_AT_K64":
            overall="SPECTRAL_UNRESOLVED"
        elif str(cls).startswith("SPECTRAL_CONVERGED") and gv=="FAIL":
            overall="LINEAR_UNSTABLE_SPECTRALLY_CONVERGED"
        elif str(cls).startswith("SPECTRAL_CONVERGED") and gv=="PASS":
            if not cr:
                overall="SPECTRALLY_BOUNDED_AWAITING_FULL_DYNAMICS"
            elif cr.get("status")=="PASS":
                if cg.get("P7_RPO_recurrence") is True and cg.get("P8_Floquet_bounded") is True:
                    overall="FULL_DYNAMICS_PASS_RPO_FLOQUET_BOUNDED"
                elif cg.get("P7_RPO_recurrence") is True:
                    overall="FULL_DYNAMICS_PASS_RPO_FOUND_FLOQUET_NOT_BOUNDED_OR_NOT_EVALUATED"
                else:
                    overall="FULL_DYNAMICS_PASS_NO_RPO_RECURRENCE"
            else:
                overall="FULL_DYNAMICS_FAIL"
        else:
            overall="INCOMPLETE"
        rows.append({
            "source":s,
            "atlas_candidate":a.get("candidate"),
            "family":a.get("family"),
            "value":a.get("value"),
            "shape_classification":a.get("shape_classification"),
            "parameterization_role":a.get("parameterization_role"),
            "screen_status":sr.get("status"),
            "screen_growth":sm.get("normalized_growth"),
            "screen_P0":sg.get("P0_geometry_core_clear"),
            "screen_P1":sg.get("P1_jacobian_converged"),
            "screen_P2":sg.get("P2_linear_growth_bounded"),
            "screen_P5":sg.get("P5_short_ringdown_bounded"),
            "screen_P7_RPO":sg.get("P7_RPO_recurrence"),
            "screen_P8_Floquet":sg.get("P8_Floquet_bounded"),
            "spectral_classification":cls,
            "spectral_growth_verdict":gv,
            "spectral_final_kmax":spec.get("final_kmax"),
            "spectral_final_growth":spec.get("final_growth"),
            "confirm_status":cr.get("status"),
            "confirm_growth":cm.get("normalized_growth"),
            "confirm_P0":cg.get("P0_geometry_core_clear"),
            "confirm_P1":cg.get("P1_jacobian_converged"),
            "confirm_P2":cg.get("P2_linear_growth_bounded"),
            "confirm_P5":cg.get("P5_short_ringdown_bounded"),
            "confirm_P7_RPO":cg.get("P7_RPO_recurrence"),
            "confirm_P8_Floquet":cg.get("P8_Floquet_bounded"),
            "confirm_floquet_radius":(cr.get("floquet",{}) or {}).get("spectral_radius_excluding_neutral"),
            "sst_stability_class":overall,
        })
    ad=ATLAS/"analysis";ad.mkdir(parents=True,exist_ok=True)
    cp=ad/"SST_V048_STABILITY_MATRIX.csv"
    if rows:
        with cp.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
            w.writeheader();w.writerows(rows)
    counts=Counter(r["sst_stability_class"] for r in rows)
    md=[
        "# KnotPlot Parameter Atlas -> SST v0.4.8 Stability Matrix","",
        "Important: v0.4.8 internally rescales every geometry to total arclength 2π. These results test normalized shape dynamics, not absolute KnotPlot scale.","",
        "## Classification counts",""
    ]
    for k,v in sorted(counts.items()):
        md.append(f"- **{k}**: {v}")
    md += ["","## Candidates","",
           "| family | candidate | shape class | spectral | confirm | RPO | Floquet | SST class |",
           "|---|---|---|---|---|---:|---:|---|"]
    for r in rows:
        md.append(
            f"| {r.get('family')} | {r.get('atlas_candidate')} | {r.get('shape_classification')} | "
            f"{r.get('spectral_classification')} / {r.get('spectral_growth_verdict')} | "
            f"{r.get('confirm_status')} | {r.get('confirm_P7_RPO')} | {r.get('confirm_P8_Floquet')} | "
            f"**{r.get('sst_stability_class')}** |"
        )
    md += ["","## Gate policy","",
           "- Spectral convergence uses the exact v0.4.8 adaptive N=720 k_max=16→24→32→48→64 decision rule.",
           "- Only spectrally converged P2 PASS candidates are promoted to the R5 full-dynamics CPU/FP64 confirmation.",
           "- v0.4.8 critical full-dynamics status is P0 ∧ P1 ∧ P2 ∧ P5.",
           "- P7 RPO recurrence and P8 Floquet boundedness are retained as separate diagnostic evidence, not silently promoted to critical gates."]
    (ad/"SST_V048_STABILITY_MATRIX.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print((ad/"SST_V048_STABILITY_MATRIX.md").read_text(encoding="utf-8"))
    return 0

def main():
    ap=argparse.ArgumentParser(description="Exact bridge from KnotPlot atlas to SST v0.4.8 custom-geometry panel")
    ap.add_argument("--mode",required=True,choices=["preflight","screen","spectral","confirm","synthesize"])
    ap.add_argument("--target",default=None)
    ap.add_argument("--backend",default=None)
    a=ap.parse_args()
    target=target_path(a.target)
    if a.mode=="preflight":
        return preflight(target)
    rc=preflight(target)
    if rc not in (0,):
        return rc
    if a.mode=="screen":
        return run_screen(target,a.backend or "openmp")
    if a.mode=="spectral":
        return run_spectral(target,a.backend or "sycl-dd32")
    if a.mode=="confirm":
        return run_confirm(target,a.backend or "openmp")
    if a.mode=="synthesize":
        return synthesize(target)
    return 2

if __name__=="__main__":
    raise SystemExit(main())
