from __future__ import annotations
from pathlib import Path
import csv, hashlib, json, shutil, sys
import numpy as np

ROOT=Path(__file__).resolve().parent
DESIGN=json.loads((ROOT/"parameter_manifest.json").read_text(encoding="utf-8"))
SHAPE_PATH=ROOT/"analysis"/"SHAPE_CANONICAL_EXTENDED.json"

sys.path.insert(0,str(ROOT))
from shape_canonical_analysis import read_xyz,closed_arclength_resample,length,rg,sha_array

def fmt_xyz(a):
    return "".join(f"{x:.17g} {y:.17g} {z:.17g}\n" for x,y,z in np.asarray(a,float))

def values_for_family(famdef):
    return famdef.get("values",[])

def choose_screen_candidates(famdef,fr):
    candidates={c["candidate"]:c for c in fr.get("candidates",[])}
    if not candidates:
        return []
    vals=famdef.get("values",[])
    default=famdef.get("default")
    chosen=[]
    if famdef.get("kind") in ("numeric","integer"):
        numeric=[]
        for c in candidates.values():
            try: numeric.append((float(c["value"]),c))
            except Exception: pass
        if numeric:
            numeric.sort(key=lambda x:x[0])
            chosen += [numeric[0][1],numeric[-1][1]]
            if default is not None:
                chosen += [min(numeric,key=lambda x:abs(x[0]-float(default)))[1]]
    else:
        chosen += list(candidates.values())
    # Also force in the pair that maximizes canonical shape separation.
    for cid in fr.get("max_shape_pair",[]) or []:
        if cid in candidates:
            chosen.append(candidates[cid])
    out=[]; seen=set()
    for c in chosen:
        if c["candidate"] not in seen:
            seen.add(c["candidate"]); out.append(c)
    return out

def priority(famdef,fr):
    cls=fr.get("shape_classification","")
    role=fr.get("parameterization_role","")
    cat=famdef.get("category","")
    if cls=="EFFECTIVE_STRONG" and cat=="core_force":
        return 1,"core-force strong shape effect"
    if cls=="EFFECTIVE_STRONG" and cat=="numerical":
        return 1,"numerical robustness / pathway sensitivity"
    if cls=="EFFECTIVE_STRONG":
        return 2,"secondary strong shape effect"
    if cls=="EFFECTIVE_MEDIUM":
        return 3,"medium shape effect"
    if cls=="EFFECTIVE_WEAK":
        return 4,"weak shape effect"
    return 9,"not selected"

def main():
    if not SHAPE_PATH.is_file():
        raise SystemExit("ERROR: run shape_canonical_analysis.py --stage extended first")
    rep=json.loads(SHAPE_PATH.read_text(encoding="utf-8"))
    hand=ROOT/"stability_handoff"
    rawdir=hand/"raw_xyz"
    arcdir=hand/"arclength300_xyz"
    if hand.exists():
        shutil.rmtree(hand)
    rawdir.mkdir(parents=True); arcdir.mkdir(parents=True)

    famdefs={f["name"]:f for f in DESIGN["families"]}
    all_rows=[]; screen_rows=[]
    exact_seen={}
    # Find the most common exact geometry among all accepted candidates as baseline.
    allc=[]
    for fam,fr in rep["families"].items():
        for c in fr.get("candidates",[]):
            allc.append((fam,fr,c))
    counts={}
    for fam,fr,c in allc:
        counts[c["raw_sha256"]]=counts.get(c["raw_sha256"],0)+1
    baseline_hash=max(counts,key=counts.get) if counts else None

    def stage_candidate(fam,fr,c,tier,reason,is_screen):
        src=Path(c["file"])
        if not src.is_absolute():
            src=ROOT/src
        if not src.is_file():
            return None
        a=read_xyz(src); arc=closed_arclength_resample(a,300)
        h=c["raw_sha256"]
        slug=c["candidate"].replace("/","_").replace("\\","_")
        rawp=rawdir/f"{slug}.txt"
        arcp=arcdir/f"{slug}.txt"
        if h not in exact_seen:
            rawp.write_text(fmt_xyz(a),encoding="utf-8",newline="\n")
            arcp.write_text(fmt_xyz(arc),encoding="utf-8",newline="\n")
            exact_seen[h]=(rawp,arcp,slug)
        else:
            rawp,arcp,slug0=exact_seen[h]
        row={
            "candidate":c["candidate"],"family":fam,
            "category":famdefs[fam]["category"],
            "value":c.get("value"),
            "shape_classification":fr.get("shape_classification"),
            "parameterization_role":fr.get("parameterization_role"),
            "shape_family_max_normalized_rms":fr.get("max_shape_arclength_phase_normalized_rms"),
            "raw_family_max_normalized_rms":fr.get("max_raw_indexed_normalized_rms"),
            "priority_tier":tier,"selection_reason":reason,
            "is_baseline_geometry":h==baseline_hash,
            "raw_sha256":h,
            "source_file":str(src),
            "raw_handoff_file":str(rawp.relative_to(ROOT)),
            "arclength300_handoff_file":str(arcp.relative_to(ROOT)),
            "length":length(a),"rg":rg(a),
            "exact_duplicate_of":"" if slug==c["candidate"] else slug,
        }
        return row

    for famdef in DESIGN["families"]:
        fam=famdef["name"]; fr=rep["families"].get(fam,{})
        cls=fr.get("shape_classification","")
        if cls not in ("EFFECTIVE_STRONG","EFFECTIVE_MEDIUM","EFFECTIVE_WEAK"):
            continue
        tier,reason=priority(famdef,fr)
        for c in fr.get("candidates",[]):
            row=stage_candidate(fam,fr,c,tier,reason,False)
            if row: all_rows.append(row)
        for c in choose_screen_candidates(famdef,fr):
            row=stage_candidate(fam,fr,c,tier,reason,True)
            if row: screen_rows.append(row)

    # Ensure at least one baseline geometry is present in screen manifest.
    if baseline_hash and not any(r["is_baseline_geometry"] for r in screen_rows):
        for fam,fr,c in allc:
            if c["raw_sha256"]==baseline_hash:
                row=stage_candidate(fam,fr,c,0,"modal exact baseline geometry",True)
                if row: screen_rows.insert(0,row)
                break

    # Exact dedupe screen list by raw hash, keeping best priority.
    best={}
    for r in screen_rows:
        h=r["raw_sha256"]
        if h not in best or int(r["priority_tier"])<int(best[h]["priority_tier"]):
            best[h]=r
    screen_rows=sorted(best.values(),key=lambda r:(int(r["priority_tier"]),r["family"],r["candidate"]))

    for name,rows in (("stability_candidates_full.csv",all_rows),("stability_candidates_screen.csv",screen_rows)):
        p=hand/name
        if rows:
            with p.open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
                w.writeheader(); w.writerows(rows)

    manifest={
        "version":"0.3.3",
        "source_shape_report":str(SHAPE_PATH.relative_to(ROOT)),
        "baseline_raw_sha256":baseline_hash,
        "full_candidate_rows":len(all_rows),
        "screen_unique_exact_geometries":len(screen_rows),
        "raw_geometry_policy":"preserve KnotPlot scale and point order; exact source XYZ",
        "arclength_geometry_policy":"closed uniform arclength resample to 300; scale preserved; orientation preserved",
        "physical_interpretation":"These are preparation candidates. Stability must be decided by the downstream SST dynamical falsifier, not by KnotPlot relaxation scores.",
        "requested_downstream":"SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact"
    }
    (hand/"handoff_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest,indent=2))

if __name__=="__main__":
    main()
