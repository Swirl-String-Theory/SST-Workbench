from __future__ import annotations
import argparse, csv, hashlib, inspect, json, math, os, random, re, shutil, sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
CONTRACT = json.loads((ROOT/"handoff_contract.json").read_text(encoding="utf-8"))
WORKSPACE = ROOT.parent
REF_DESIGN = ROOT/"reference/Trefoil_Balance_Point_Campaign_v0.1.0_balance_design.json"

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()

def read_xyz(path: Path) -> np.ndarray:
    rows=[]
    for raw in Path(path).read_text(encoding="utf-8",errors="ignore").splitlines():
        vals=[]
        for t in raw.replace(","," ").split():
            try: vals.append(float(t))
            except Exception: pass
        if len(vals)>=3: rows.append(vals[:3])
    a=np.asarray(rows,float)
    if a.ndim!=2 or a.shape[0]<8 or a.shape[1]!=3:
        raise ValueError(f"Bad XYZ file {path}: shape={a.shape}")
    scale=max(float(np.ptp(a,axis=0).max()),1.0)
    if np.linalg.norm(a[0]-a[-1]) < 1e-12*scale:
        a=a[:-1]
    return a

def curve_length(a):
    return float(np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1).sum())

def rg(a):
    c=a-a.mean(axis=0,keepdims=True)
    return float(np.sqrt(np.mean(np.sum(c*c,axis=1))))

def resample_closed(a,n=300):
    seg=np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1)
    if np.any(~np.isfinite(seg)) or np.any(seg<=0):
        raise ValueError("Non-finite or zero segment")
    s=np.r_[0.0,np.cumsum(seg)]
    aa=np.vstack([a,a[0]])
    t=np.linspace(0,s[-1],int(n),endpoint=False)
    return np.column_stack([np.interp(t,s,aa[:,j]) for j in range(3)])

def write_xyz(path,a):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    np.savetxt(path,np.asarray(a,float),fmt="%.17g")

def linear_slope(xs,ys):
    x=np.asarray(xs,float); y=np.asarray(ys,float)
    A=np.c_[x,np.ones_like(x)]
    m,_=np.linalg.lstsq(A,y,rcond=None)[0]
    return float(m)

def workspace_path(rel):
    return (WORKSPACE/Path(rel)).resolve()

def balance_root():
    env=os.environ.get("TREFOIL_BALANCE_ROOT","").strip()
    return Path(env).resolve() if env else workspace_path(CONTRACT["workspace_layout"]["balance_campaign_root"])

def balance_out():
    env=os.environ.get("TREFOIL_BALANCE_OUT","").strip()
    return Path(env).resolve() if env else workspace_path(CONTRACT["workspace_layout"]["balance_out"])

def load_design():
    live=balance_root()/"balance_design.json"
    ref=json.loads(REF_DESIGN.read_text(encoding="utf-8"))
    if live.is_file():
        d=json.loads(live.read_text(encoding="utf-8"))
        # The handoff is designed specifically for this frozen 10x2 campaign.
        if d.get("n_settings")!=10 or d.get("n_variants")!=2:
            raise RuntimeError(f"Unexpected live balance design: {live}")
        return d,live
    return ref,REF_DESIGN

def checkpoint_path(variant,setting,it):
    return balance_out()/f"{variant}__{setting}_i{it:05d}.txt"

def analyze_balance():
    d,design_path=load_design()
    out=balance_out()
    if not out.is_dir():
        raise FileNotFoundError(f"Balance output directory missing: {out}")
    rows=[]; by={}
    early_its=[0,25,100]
    for v in d["variants"]:
        for s in d["settings"]:
            rid=f"{v['id']}__{s['id']}"
            points={}
            for it in [0,25,100,1000,10000]:
                p=checkpoint_path(v["id"],s["id"],it)
                if not p.is_file():
                    raise FileNotFoundError(f"Required balance checkpoint missing: {p}")
                a=read_xyz(p)
                points[it]={"length":curve_length(a),"rg":rg(a),"path":str(p)}
            L0=points[0]["length"]; R0=points[0]["rg"]
            for it,q in points.items():
                q["E"]=0.5*((q["length"]/L0-1.0)+(q["rg"]/R0-1.0))
            early=linear_slope(early_its,[points[i]["E"] for i in early_its])*100.0
            final_path=checkpoint_path(v["id"],s["id"],10000)
            rec={
                "run_id":rid,"variant":v["id"],"variant_name":v["name"],
                "setting":s["id"],"role":s["role"],"group":s["group"],
                "charge":s["charge"],"hooke":s["hooke"],"power":s["power"],
                "early_E_per_100":early,
                "abs_early_E_per_100":abs(early),
                "E_i01000":points[1000]["E"],
                "E_i10000":points[10000]["E"],
                "source_i10000":str(final_path),
                "source_i10000_sha256":sha256_file(final_path),
                "n_points_i10000":len(read_xyz(final_path)),
            }
            rows.append(rec); by[(v["id"],s["id"])]=rec

    # Deterministic upstream-only selection diagnostics.
    common=[]
    for s in d["settings"]:
        rr=[by[(v["id"],s["id"])] for v in d["variants"]]
        common.append({
            "setting":s["id"],
            "worst_abs_early":max(abs(r["early_E_per_100"]) for r in rr),
            "worst_abs_final":max(abs(r["E_i10000"]) for r in rr),
        })
    common.sort(key=lambda x:(x["worst_abs_early"],x["worst_abs_final"],x["setting"]))
    common_best=common[0]["setting"]
    individual_best={}
    for v in d["variants"]:
        rr=[by[(v["id"],s["id"])] for s in d["settings"]]
        rr.sort(key=lambda r:(abs(r["early_E_per_100"]),abs(r["E_i10000"]),r["setting"]))
        individual_best[v["id"]]=rr[0]["setting"]

    def zero_info(variant,setting_ids,param):
        pts=[]
        for sid in setting_ids:
            r=by[(variant,sid)]
            pts.append((float(r[param]),float(r["early_E_per_100"]),sid))
        pts.sort()
        zero=[]
        for (x1,y1,s1),(x2,y2,s2) in zip(pts[:-1],pts[1:]):
            if y1==0.0:
                zero.append({"estimate":x1,"between":[s1,s1]})
            elif y1*y2<0:
                x=x1-y1*(x2-x1)/(y2-y1)
                zero.append({"estimate":float(x),"between":[s1,s2]})
        if zero:
            z=min(zero,key=lambda z:abs(z["estimate"]-np.median([p[0] for p in pts])))
            nearest=min(pts,key=lambda p:abs(p[0]-z["estimate"]))[2]
            return {"points":pts,"zero_crossings":zero,"preferred_zero":z,"nearest_actual_setting":nearest}
        nearest=min(pts,key=lambda p:abs(p[1]))[2]
        return {"points":pts,"zero_crossings":[],"preferred_zero":None,"nearest_actual_setting":nearest}

    brackets={}
    for v in d["variants"]:
        brackets[v["id"]]={
            "q":zero_info(v["id"],["QLO","QCEN","QHI"],"charge"),
            "h":zero_info(v["id"],["HLO","R50","HHI"],"hooke"),
        }

    report={
        "format":"TREFOIL-BALANCE-UPSTREAM-SELECTION-ANALYSIS-1.0",
        "design_path":str(design_path),
        "balance_out":str(out),
        "rows":rows,
        "common_best_setting":common_best,
        "individual_best_settings":individual_best,
        "brackets":brackets,
        "selection_does_not_read_tbk_outputs":True,
    }
    (ROOT/"analysis").mkdir(exist_ok=True)
    (ROOT/"analysis/BALANCE_SELECTION_ANALYSIS.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return d,report,by

def selected_keys(mode,d,report,by):
    variants=[v["id"] for v in d["variants"]]
    if mode=="all20":
        return [(v["id"],s["id"],"ALL20") for v in d["variants"] for s in d["settings"]]
    if mode=="core":
        return [(vid,sid,"CORE_FROZEN_Q_BRACKET") for vid in variants for sid in ("B00","QLO","QCEN","QHI")]
    if mode=="full_balance":
        return [(vid,sid,"FULL_BALANCE_RAY") for vid in variants for sid in ("B00","R25","R50","R75","R100")]
    if mode!="selected":
        raise ValueError(mode)

    reasons={}
    def add(vid,sid,reason):
        reasons.setdefault((vid,sid),[]).append(reason)
    for vid in variants:
        add(vid,"B00","BASELINE_CONTROL")
        add(vid,report["common_best_setting"],"COMMON_BEST_ACROSS_EMBEDDINGS")
        add(vid,report["individual_best_settings"][vid],"INDIVIDUAL_BEST_EARLY_ZERO")
        add(vid,report["brackets"][vid]["q"]["nearest_actual_setting"],"NEAREST_ACTUAL_Q_ZERO")
        add(vid,report["brackets"][vid]["h"]["nearest_actual_setting"],"NEAREST_ACTUAL_H_ZERO")
    return [(vid,sid,"+".join(reasons[(vid,sid)])) for vid,sid in sorted(reasons)]

def prepare_mode(mode,d,report,by):
    root=ROOT/"prepared"/mode
    if root.exists(): shutil.rmtree(root)
    inp=root/"inputs"; canon=root/"canonical_300"
    inp.mkdir(parents=True); canon.mkdir(parents=True)

    keys=selected_keys(mode,d,report,by)
    seed=int(CONTRACT["selection_policy"]["blind_seed"])
    tmp=[]
    for vid,sid,reason in keys:
        r=by[(vid,sid)]
        token=hashlib.sha256(
            f"{seed}|{r['source_i10000_sha256']}|{vid}|{sid}|{mode}".encode("utf-8")
        ).hexdigest()
        tmp.append((token,vid,sid,reason,r))
    tmp.sort()

    public=[]; private=[]
    for i,(_,vid,sid,reason,r) in enumerate(tmp,1):
        bid=f"BALX_{i:03d}"
        src=Path(r["source_i10000"])
        dst=inp/f"{bid}.txt"
        shutil.copy2(src,dst)
        a=read_xyz(src)
        c=resample_closed(a,300)
        cp=canon/f"{bid}_arclength300.txt"
        write_xyz(cp,c)
        public.append({
            "source":bid,
            "kind":"knotplot",
            "topology_class":"knot",
            "canonical_id":"3_1",
            "input_file":str(dst.relative_to(ROOT)).replace("\\","/"),
            "raw_sha256":sha256_file(dst),
        })
        private.append({
            "source":bid,
            "mode":mode,
            "variant":vid,
            "setting":sid,
            "selection_reason":reason,
            "charge":r["charge"],"hooke":r["hooke"],"power":r["power"],
            "early_E_per_100":r["early_E_per_100"],
            "E_i01000":r["E_i01000"],
            "E_i10000":r["E_i10000"],
            "original_balance_file":r["source_i10000"],
            "original_sha256":r["source_i10000_sha256"],
            "raw_handoff_file":str(dst.relative_to(ROOT)).replace("\\","/"),
            "raw_handoff_sha256":sha256_file(dst),
            "canonical_300_file":str(cp.relative_to(ROOT)).replace("\\","/"),
            "canonical_300_sha256":sha256_file(cp),
            "orientation_reversed":False,
            "scale_modified_for_target":False,
        })

    (root/"PUBLIC_ENTRIES.json").write_text(json.dumps(public,indent=2)+"\n",encoding="utf-8")
    (root/"PRIVATE_PROVENANCE.json").write_text(json.dumps(private,indent=2)+"\n",encoding="utf-8")
    with (root/"PRIVATE_PROVENANCE.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(private[0].keys()));w.writeheader();w.writerows(private)

    lock={
        "format":"TREFOIL-BALANCE-TBK-HANDOFF-SELECTION-LOCK-1.0",
        "mode":mode,
        "n_entries":len(public),
        "selection_logic":"upstream balance response only; no TBK/RPO output read",
        "public_entries_sha256":sha256_file(root/"PUBLIC_ENTRIES.json"),
        "private_provenance_sha256":sha256_file(root/"PRIVATE_PROVENANCE.json"),
        "files":{p.name:sha256_file(p) for p in sorted(inp.glob("*.txt"))},
    }
    (root/"SELECTION_LOCK.json").write_text(json.dumps(lock,indent=2)+"\n",encoding="utf-8")
    return lock

def prepare_all():
    d,report,by=analyze_balance()
    locks={}
    for mode in CONTRACT["selection_policy"]["modes"]:
        locks[mode]=prepare_mode(mode,d,report,by)
    summary={
        "format":"TREFOIL-BALANCE-TBK-HANDOFF-PREPARED-1.0",
        "default_mode":CONTRACT["selection_policy"]["default_mode"],
        "locks":locks,
        "common_best_setting":report["common_best_setting"],
        "individual_best_settings":report["individual_best_settings"],
        "brackets":report["brackets"],
    }
    (ROOT/"analysis/PREPARED_SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print("HANDOFF PREPARE PASS")
    print("Balance out:",balance_out())
    print("Common best:",report["common_best_setting"])
    print("Individual best:",report["individual_best_settings"])
    for m,l in locks.items(): print(f"  {m:12s}: {l['n_entries']} blinded entries")
    return 0

def target_candidates():
    env=os.environ.get("SST_TBK_TARGET","").strip()
    if env:
        return [Path(env).resolve()]
    return [
        workspace_path(CONTRACT["workspace_layout"]["target_v048"]),
        workspace_path(CONTRACT["workspace_layout"]["target_v046"]),
    ]

def target_version(target):
    p=target/"VERSION.json"
    if not p.is_file(): return {}
    return json.loads(p.read_text(encoding="utf-8"))

def target_kind(target):
    v=str(target_version(target).get("version") or target_version(target).get("package_version") or "")
    if v=="0.4.8": return "v048"
    if v.startswith("0.4.6"): return "v046"
    return "unknown"

def resolve_target(prefer="auto"):
    cands=target_candidates()
    if prefer=="v048":
        cands=sorted(cands,key=lambda p:0 if target_kind(p)=="v048" else 1)
    elif prefer=="v046":
        cands=sorted(cands,key=lambda p:0 if target_kind(p)=="v046" else 1)
    else:
        cands=sorted(cands,key=lambda p:0 if target_kind(p)=="v048" else 1)
    for p in cands:
        if p.is_dir() and target_kind(p) in ("v048","v046"):
            return p
    raise FileNotFoundError("No supported TBK/RPO target found. Set SST_TBK_TARGET or use the documented workspace layout.")

def required_for(target,kind):
    common=["VERSION.json","run_install.cmd","sst_blind/multitopology.py","sst_blind/io.py"]
    if kind=="v048":
        v=CONTRACT["v048"]
        return common+[
            v["screen_config"],v["spectral"]["k16"],v["spectral"]["k24"],
            v["spectral"]["k32"],v["spectral"]["k48"],v["spectral"]["k64"],
            v["spectral"]["plan"],v["full_confirm_config"],
            "sst_blind/spectral_extension.py",
        ]
    v=CONTRACT["v046"]
    return common+[v["full_config"]]

def preflight(prefer="auto"):
    target=resolve_target(prefer)
    kind=target_kind(target)
    req=required_for(target,kind)
    rows=[{"path":r,"ok":(target/r).is_file()} for r in req]
    py=target/".venv/Scripts/python.exe"
    result={
        "target":str(target),"kind":kind,"version":target_version(target),
        "venv_python":str(py),"venv_exists":py.is_file(),
        "required":rows,"ok_contract":all(r["ok"] for r in rows),
    }
    (ROOT/"analysis/TARGET_PREFLIGHT.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("TARGET PREFLIGHT")
    print("Target :",target)
    print("Kind   :",kind)
    print("Version:",result["version"].get("version") or result["version"].get("package_version"))
    for r in rows: print("PASS" if r["ok"] else "FAIL",r["path"])
    print("TARGET VENV:", "PASS" if py.is_file() else "MISSING")
    if not result["ok_contract"]: return 2
    if not py.is_file(): return 3
    return 0

def import_target(target,need_spectral=False):
    os.chdir(target)
    sys.path.insert(0,str(target))
    from sst_blind.multitopology import run_panel
    if need_spectral:
        from sst_blind.spectral_extension import load_rung_by_source,evaluate_triplet,write_extension_outputs
        return run_panel,load_rung_by_source,evaluate_triplet,write_extension_outputs
    return run_panel,None,None,None

def mode_entries(mode):
    p=ROOT/"prepared"/mode/"PUBLIC_ENTRIES.json"
    if not p.is_file():
        raise FileNotFoundError(f"{p} missing; run prepare first.")
    rows=json.loads(p.read_text(encoding="utf-8"))
    out=[]
    for r in rows:
        q=(ROOT/r["input_file"]).resolve()
        if not q.is_file(): raise FileNotFoundError(q)
        # Deliberately no q/h/p, variant or selection reason in target entry.
        out.append({
            "source":r["source"],
            "kind":"knotplot",
            "topology_class":"knot",
            "canonical_id":"3_1",
            "path":str(q),
        })
    return out

def call_run_panel(run_panel,entries,cfg,out,backend,resume=True):
    kwargs={"backend":backend}
    try:
        sig=inspect.signature(run_panel)
        if "resume" in sig.parameters: kwargs["resume"]=resume
    except Exception:
        pass
    return run_panel(entries,cfg,out,**kwargs)

def compact_results(results):
    rows={}
    for bid,r in results.items():
        g=r.get("gates",{}) or {}; m=r.get("metrics",{}) or {}
        floq=r.get("floquet",{}) or {}; rpo=r.get("rpo",{}) or {}
        rows[bid]={
            "status":r.get("status"),
            "gates":{k:g.get(k) for k in sorted(g)},
            "normalized_growth":m.get("normalized_growth"),
            "analysis_scope":m.get("analysis_scope"),
            "core_clearance_radii":m.get("core_clearance_radii"),
            "rpo_found":bool(m.get("rpo_found") or rpo.get("candidate") is not None),
            "floquet_radius":floq.get("spectral_radius_excluding_neutral"),
        }
    return rows

def write_stage(stage,target,mode,backend,final,results,mapping,outdir):
    d={
        "format":"TREFOIL-BALANCE-TBK-STAGE-RESULTS-1.0",
        "stage":stage,"target":str(target),"target_kind":target_kind(target),
        "mode":mode,"backend":backend,"out_dir":str(outdir),
        "overall":final.get("overall"),"dataset_count":final.get("dataset_count",len(results)),
        "results":compact_results(results),
    }
    p=ROOT/"tbk_outputs"/target_kind(target)/f"{stage}_HANDOFF_STAGE_RESULTS.json"
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,indent=2)+"\n",encoding="utf-8")
    return d

def run_screen_v048(mode="selected"):
    target=resolve_target("v048")
    if target_kind(target)!="v048": raise RuntimeError("v0.4.8 target required")
    run_panel,_,_,_=import_target(target)
    entries=mode_entries(mode)
    out=ROOT/"tbk_outputs/v048/01_screen_fp64"
    cfg=target/CONTRACT["v048"]["screen_config"]
    final,results,mapping=call_run_panel(run_panel,entries,cfg,out,"openmp",True)
    write_stage("01_screen_fp64",target,mode,"openmp",final,results,mapping,out)
    print(json.dumps({"overall":final.get("overall"),"datasets":len(results),"out":str(out)},indent=2))
    return 0

def run_spectral_v048(mode="selected",backend="sycl-dd32"):
    target=resolve_target("v048")
    if target_kind(target)!="v048": raise RuntimeError("v0.4.8 target required")
    run_panel,load_rung,evaluate_triplet,write_extension_outputs=import_target(target,True)
    entries=mode_entries(mode); bysrc={e["source"]:e for e in entries}; sources=set(bysrc)
    out=ROOT/"tbk_outputs/v048/02_adaptive_spectral"
    out.mkdir(parents=True,exist_ok=True)
    sv=CONTRACT["v048"]["spectral"]
    plan=json.loads((target/sv["plan"]).read_text(encoding="utf-8"))
    policy=plan["policy"]
    (out/"SPECTRAL_EXTENSION_PLAN_PREREGISTERED.json").write_text(json.dumps(plan,indent=2)+"\n",encoding="utf-8")
    specs=[
        (16,"00_K16",sv["k16"]),
        (24,"01_K24",sv["k24"]),
        (32,"02_K32",sv["k32"]),
        (48,"03_K48",sv["k48"]),
        (64,"04_K64",sv["k64"]),
    ]
    data={}; growth={s:{} for s in sources}; decisions={}; stop_at={}
    active=set(sources)
    for k,dirname,cfgrel in specs:
        if k>=48 and not active: break
        stage_sources=sources if k<=32 else active
        selected=[bysrc[s] for s in sorted(stage_sources)]
        ro=out/dirname
        print(f"[HANDOFF->v0.4.8] spectral k={k} N={len(selected)} backend={backend}")
        final,results,mapping=call_run_panel(run_panel,selected,target/cfgrel,ro,backend,True)
        data[k]=load_rung(ro)
        for s in stage_sources:
            growth[s][k]=float(data[k][s]["result"]["metrics"]["normalized_growth"])
        if k==32:
            newly=[]
            for s in sorted(active):
                d=evaluate_triplet([16,24,32],[data[16][s]["result"],data[24][s]["result"],data[32][s]["result"]],policy)
                decisions[s]=d
                if d["resolved"]:
                    stop_at[s]=32; newly.append(s)
            active-=set(newly)
        elif k==48:
            newly=[]
            for s in sorted(active):
                d=evaluate_triplet([24,32,48],[data[24][s]["result"],data[32][s]["result"],data[48][s]["result"]],policy)
                decisions[s]=d
                if d["resolved"]:
                    stop_at[s]=48; newly.append(s)
            active-=set(newly)
        elif k==64:
            for s in sorted(active):
                decisions[s]=evaluate_triplet([32,48,64],[data[32][s]["result"],data[48][s]["result"],data[64][s]["result"]],policy)

    records=[]
    for s in sorted(sources):
        d=decisions.get(s)
        if d is None:
            records.append({"source":s,"classification":"INCOMPLETE","growth_verdict":None,
                            "growth_by_k":{str(k):v for k,v in sorted(growth[s].items())},
                            "reasons":["missing_required_spectral_rungs"]})
            continue
        if s in stop_at:
            k=stop_at[s]; cls=f"SPECTRAL_CONVERGED_K{k}"; reasons=[]
        else:
            k=64; cls="SPECTRAL_UNRESOLVED_AT_K64"; reasons=d.get("reasons",[])
        records.append({
            "source":s,"topology_class":"knot","canonical_id":"3_1",
            "classification":cls,"growth_verdict":d.get("growth_verdict"),
            "final_kmax":k,"final_growth":float(d["growth_values"][-1]),
            "growth_by_k":{str(kk):vv for kk,vv in sorted(growth[s].items())},
            "decision":d,"reasons":reasons,
        })
    write_extension_outputs(out,records,plan)
    summary={
        "format":"TREFOIL-BALANCE-TBK-SPECTRAL-1.0","mode":mode,"backend":backend,
        "records":records,"classification_counts":dict(Counter(r["classification"] for r in records)),
    }
    p=ROOT/"tbk_outputs/v048/02_adaptive_spectral_HANDOFF_STAGE_RESULTS.json"
    p.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary["classification_counts"],indent=2))
    return 0

def spectral_pass_sources():
    p=ROOT/"tbk_outputs/v048/02_adaptive_spectral_HANDOFF_STAGE_RESULTS.json"
    if not p.is_file(): raise FileNotFoundError("Run v0.4.8 spectral stage first")
    d=json.loads(p.read_text(encoding="utf-8"))
    return {r["source"] for r in d["records"]
            if str(r.get("classification","")).startswith("SPECTRAL_CONVERGED")
            and r.get("growth_verdict")=="PASS"}

def run_confirm_v048(mode="selected"):
    target=resolve_target("v048")
    run_panel,_,_,_=import_target(target)
    good=spectral_pass_sources()
    entries=[e for e in mode_entries(mode) if e["source"] in good]
    out=ROOT/"tbk_outputs/v048/03_full_confirm_fp64"; out.mkdir(parents=True,exist_ok=True)
    if not entries:
        d={"format":"TREFOIL-BALANCE-TBK-STAGE-RESULTS-1.0","stage":"03_full_confirm_fp64",
           "mode":mode,"backend":"openmp","overall":"NO_PROMOTED_CANDIDATES","dataset_count":0,"results":{}}
        (ROOT/"tbk_outputs/v048/03_full_confirm_fp64_HANDOFF_STAGE_RESULTS.json").write_text(json.dumps(d,indent=2)+"\n")
        (out/"NO_PROMOTED_CANDIDATES.txt").write_text("No spectrally converged P2 PASS candidate was promoted.\n")
        print("[HANDOFF->v0.4.8] no candidates promoted.")
        return 0
    cfg=target/CONTRACT["v048"]["full_confirm_config"]
    final,results,mapping=call_run_panel(run_panel,entries,cfg,out,"openmp",True)
    write_stage("03_full_confirm_fp64",target,mode,"openmp",final,results,mapping,out)
    print(json.dumps({"overall":final.get("overall"),"datasets":len(results),"out":str(out)},indent=2))
    return 0

def run_full_v046(mode="selected"):
    target=resolve_target("v046")
    if target_kind(target)!="v046": raise RuntimeError("v0.4.6 target required")
    run_panel,_,_,_=import_target(target)
    entries=mode_entries(mode)
    out=ROOT/"tbk_outputs/v046/01_full_fp64"
    cfg=target/CONTRACT["v046"]["full_config"]
    final,results,mapping=call_run_panel(run_panel,entries,cfg,out,"openmp",True)
    write_stage("01_full_fp64",target,mode,"openmp",final,results,mapping,out)
    print(json.dumps({"overall":final.get("overall"),"datasets":len(results),"out":str(out)},indent=2))
    return 0

def verify_selection_lock(mode="selected"):
    root=ROOT/"prepared"/mode
    lock=json.loads((root/"SELECTION_LOCK.json").read_text(encoding="utf-8"))
    bad=[]
    if sha256_file(root/"PUBLIC_ENTRIES.json")!=lock["public_entries_sha256"]: bad.append("PUBLIC_ENTRIES.json")
    if sha256_file(root/"PRIVATE_PROVENANCE.json")!=lock["private_provenance_sha256"]: bad.append("PRIVATE_PROVENANCE.json")
    for fn,h in lock["files"].items():
        p=root/"inputs"/fn
        if not p.is_file() or sha256_file(p)!=h: bad.append(str(p))
    if bad:
        print("SELECTION LOCK FAIL:",bad)
        return 2
    print(f"SELECTION LOCK PASS: mode={mode} n={lock['n_entries']}")
    return 0

def summarize(mode="selected"):
    root=ROOT/"prepared"/mode
    prov={r["source"]:r for r in json.loads((root/"PRIVATE_PROVENANCE.json").read_text(encoding="utf-8"))}
    candidates=[]
    for kind in ("v048","v046"):
        droot=ROOT/"tbk_outputs"/kind
        if not droot.is_dir(): continue
        for p in sorted(droot.glob("*_HANDOFF_STAGE_RESULTS.json")):
            d=json.loads(p.read_text(encoding="utf-8"))
            stage=d.get("stage",p.stem)
            if "records" in d:  # spectral summary
                for r in d["records"]:
                    bid=r["source"]
                    candidates.append({"target":kind,"stage":"02_adaptive_spectral","source":bid,**prov.get(bid,{}),
                                       "status":r.get("classification"),"growth_verdict":r.get("growth_verdict"),
                                       "normalized_growth":r.get("final_growth"),"gates":None,
                                       "rpo_found":None,"floquet_radius":None})
            else:
                for bid,r in d.get("results",{}).items():
                    candidates.append({"target":kind,"stage":stage,"source":bid,**prov.get(bid,{}),
                                       "status":r.get("status"),"growth_verdict":None,
                                       "normalized_growth":r.get("normalized_growth"),
                                       "gates":r.get("gates"),"rpo_found":r.get("rpo_found"),
                                       "floquet_radius":r.get("floquet_radius")})
    (ROOT/"analysis").mkdir(exist_ok=True)
    report={
        "format":"TREFOIL-BALANCE-TO-TBK-RPO-SUMMARY-1.0",
        "mode":mode,
        "historical_reference_user_stated":["2.2.1","4.2.1"],
        "historical_reference_used_for_selection":False,
        "rows":candidates,
    }
    (ROOT/"analysis/TBK_RPO_HANDOFF_SUMMARY.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    # Flat CSV
    flat=[]
    for r in candidates:
        q=dict(r); gates=q.pop("gates",None) or {}
        for k,v in gates.items(): q[f"gate_{k}"]=v
        flat.append(q)
    if flat:
        cols=sorted(set().union(*(r.keys() for r in flat)))
        with (ROOT/"analysis/TBK_RPO_HANDOFF_SUMMARY.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(flat)

    # Best human-readable report.
    lines=[
        "# Trefoil Balance -> TBK/RPO Handoff Summary","",
        f"- Candidate mode: **{mode}**",
        "- Historical comparison context supplied upstream: **2.2.1** and **4.2.1** were prior PASS links.",
        "- That historical fact was **not used** to select or rank trefoil inputs.","",
        "| target | stage | blind | variant | setting | q | h | p | balance early E/100 | target status | growth verdict | growth | RPO | Floquet radius |",
        "|---|---|---|---|---|---:|---:|---:|---:|---|---|---:|---|---:|",
    ]
    for r in candidates:
        lines.append(
            f"| {r.get('target','')} | {r.get('stage','')} | {r.get('source','')} | "
            f"{r.get('variant','')} | {r.get('setting','')} | "
            f"{r.get('charge','')} | {r.get('hooke','')} | {r.get('power','')} | "
            f"{r.get('early_E_per_100','')} | {r.get('status','')} | "
            f"{r.get('growth_verdict','')} | {r.get('normalized_growth','')} | "
            f"{r.get('rpo_found','')} | {r.get('floquet_radius','')} |"
        )
    lines += ["","## Interpretation guardrail","",
              "The handoff reports the target falsifier's own status/gates without redefining them.",
              "A KnotPlot balance state that remains TBK/RPO FAIL does not become stable by preparation alone.",
              "A trefoil PASS would show that a balance-selected trefoil can enter the target package's accepted dynamical sector; it would not by itself prove SST."]
    (ROOT/"analysis/TBK_RPO_HANDOFF_SUMMARY.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("WROTE analysis/TBK_RPO_HANDOFF_SUMMARY.md")
    return 0

def main():
    ap=argparse.ArgumentParser()
    sp=ap.add_subparsers(dest="cmd",required=True)
    p=sp.add_parser("preflight"); p.add_argument("--prefer",choices=["auto","v048","v046"],default="auto")
    sp.add_parser("prepare")
    p=sp.add_parser("verify-lock"); p.add_argument("--mode",default="selected",choices=CONTRACT["selection_policy"]["modes"])
    p=sp.add_parser("screen-v048"); p.add_argument("--mode",default="selected",choices=CONTRACT["selection_policy"]["modes"])
    p=sp.add_parser("spectral-v048"); p.add_argument("--mode",default="selected",choices=CONTRACT["selection_policy"]["modes"]); p.add_argument("--backend",default="sycl-dd32")
    p=sp.add_parser("confirm-v048"); p.add_argument("--mode",default="selected",choices=CONTRACT["selection_policy"]["modes"])
    p=sp.add_parser("full-v046"); p.add_argument("--mode",default="selected",choices=CONTRACT["selection_policy"]["modes"])
    p=sp.add_parser("summarize"); p.add_argument("--mode",default="selected",choices=CONTRACT["selection_policy"]["modes"])
    a=ap.parse_args()
    if a.cmd=="preflight": return preflight(a.prefer)
    if a.cmd=="prepare": return prepare_all()
    if a.cmd=="verify-lock": return verify_selection_lock(a.mode)
    if a.cmd=="screen-v048": return run_screen_v048(a.mode)
    if a.cmd=="spectral-v048": return run_spectral_v048(a.mode,a.backend)
    if a.cmd=="confirm-v048": return run_confirm_v048(a.mode)
    if a.cmd=="full-v046": return run_full_v046(a.mode)
    if a.cmd=="summarize": return summarize(a.mode)
    raise AssertionError(a.cmd)

if __name__=="__main__":
    raise SystemExit(main())
