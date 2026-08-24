from __future__ import annotations
from pathlib import Path
import json,hashlib,csv,sys
import numpy as np

ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"parameter_manifest.json").read_text(encoding="utf-8"))
TH=float(D["effect_threshold_normalized_rms"])

ANALYSIS_VERSION="0.3.3"
SHAPE_RESAMPLE_POINTS=256

def read_xyz(path):
    rows=[]
    for line in path.read_text(encoding="utf-8",errors="replace").splitlines():
        s=line.strip()
        if not s or s.startswith(("#","%")):
            continue
        parts=s.replace(","," ").split()
        if len(parts)<3:
            continue
        try:
            rows.append([float(parts[0]),float(parts[1]),float(parts[2])])
        except ValueError:
            pass
    a=np.asarray(rows,float)
    if a.ndim!=2 or a.shape[0]<4 or a.shape[1]!=3:
        raise ValueError(f"bad XYZ {path}: shape {a.shape}")
    scale=max(float(np.ptp(a,axis=0).max()),1.0)
    if np.linalg.norm(a[0]-a[-1]) < 1e-12*scale:
        a=a[:-1]
    return a

def center(a):
    a=np.asarray(a,float)
    return a-a.mean(axis=0,keepdims=True)

def curve_length(a):
    a=np.asarray(a,float)
    return float(np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1).sum())

def rg(a):
    c=center(a)
    return float(np.sqrt(np.mean(np.sum(c*c,axis=1))))

def resample_closed_arclength(a,n=SHAPE_RESAMPLE_POINTS):
    a=np.asarray(a,float)
    seg=np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1)
    if np.any(~np.isfinite(seg)) or np.any(seg<=0):
        raise ValueError("curve contains non-finite or zero-length segment")
    s=np.concatenate([[0.0],np.cumsum(seg)])
    aa=np.vstack([a,a[0]])
    target=np.linspace(0.0,s[-1],int(n),endpoint=False)
    out=np.column_stack([np.interp(target,s,aa[:,j]) for j in range(3)])
    return out

def kabsch_rms(a,b):
    """Minimize RMS of A@R against B using a proper rotation."""
    if a.shape!=b.shape:
        return float("nan")
    aa=center(a)
    bb=center(b)
    h=aa.T@bb
    u,_,vt=np.linalg.svd(h)
    if np.linalg.det(u@vt)<0:
        u[:,-1]*=-1
    r=u@vt
    d=aa@r-bb
    return float(np.sqrt(np.mean(np.sum(d*d,axis=1))))

def legacy_indexed_normalized_rms(a,b):
    if a.shape!=b.shape:
        return float("nan")
    rr=kabsch_rms(a,b)
    scale=max((rg(a)+rg(b))/2.0,1e-30)
    return rr/scale

def cyclic_shape_normalized_rms(a,b,n=SHAPE_RESAMPLE_POINTS):
    """
    Parameterization-invariant closed-curve metric:
      1. uniform arclength resampling,
      2. all cyclic choices of curve origin,
      3. proper Kabsch rotation,
      4. minimum RMS.

    Traversal reversal is intentionally not searched: the campaign preserves
    oriented centerlines. Scale is not fitted away.
    """
    aa=resample_closed_arclength(a,n)
    bb=resample_closed_arclength(b,n)
    best=float("inf")
    best_shift=0
    for shift in range(int(n)):
        rr=kabsch_rms(aa,np.roll(bb,shift,axis=0))
        if rr<best:
            best=rr
            best_shift=shift
    scale=max((rg(aa)+rg(bb))/2.0,1e-30)
    return best/scale,int(best_shift)

def turns(a):
    e1=a-np.roll(a,1,axis=0)
    e2=np.roll(a,-1,axis=0)-a
    n1=np.linalg.norm(e1,axis=1)
    n2=np.linalg.norm(e2,axis=1)
    cos=np.sum(e1*e2,axis=1)/np.maximum(n1*n2,1e-30)
    ang=np.arccos(np.clip(cos,-1,1))
    return float(np.mean(ang)),float(np.max(ang))

def min_nonlocal_point_distance(a,skip=3):
    n=len(a)
    best=float("inf")
    for i in range(n):
        dd=np.linalg.norm(a-a[i],axis=1)
        for off in range(-skip,skip+1):
            dd[(i+off)%n]=np.inf
        best=min(best,float(np.min(dd)))
    return best

def hash_arr(a):
    return hashlib.sha256(np.asarray(a,dtype="<f8").tobytes()).hexdigest()

def metrics(path):
    a=read_xyz(path)
    mt,xt=turns(a)
    return {
        "file":str(path),
        "n":len(a),
        "sha256_geometry":hash_arr(a),
        "length":curve_length(a),
        "rg":rg(a),
        "mean_turn":mt,
        "max_turn":xt,
        "min_nonlocal_point_distance":min_nonlocal_point_distance(a),
        "_array":a,
    }

def pairwise_summary(items):
    best_shape=(0.0,None,None,None)
    best_legacy=(0.0,None,None)
    pairs=[]
    for i in range(len(items)):
        for j in range(i+1,len(items)):
            a=items[i]["metrics"]["_array"]
            b=items[j]["metrics"]["_array"]
            legacy=legacy_indexed_normalized_rms(a,b)
            shape,shift=cyclic_shape_normalized_rms(a,b)
            c1=items[i]["candidate"]
            c2=items[j]["candidate"]
            pairs.append({
                "candidate_a":c1,
                "candidate_b":c2,
                "shape_invariant_normalized_rms":shape,
                "legacy_indexed_normalized_rms":legacy,
                "best_cyclic_shift":shift,
            })
            if np.isfinite(shape) and shape>best_shape[0]:
                best_shape=(shape,c1,c2,shift)
            if np.isfinite(legacy) and legacy>best_legacy[0]:
                best_legacy=(legacy,c1,c2)
    return best_shape,best_legacy,pairs

def classify(nr,stage):
    if nr>=1e-2:
        return "EFFECTIVE_STRONG"
    if nr>=1e-3:
        return "EFFECTIVE_MEDIUM"
    if nr>=TH:
        return "EFFECTIVE_WEAK"
    return "NULL_AT_"+("100" if stage=="probe" else "1000")

def analyze(stage):
    (ROOT/"analysis").mkdir(parents=True,exist_ok=True)
    audits=[]
    for p in sorted((ROOT/"logs"/stage).glob("*_audit.json")):
        try:
            audits.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    byfam={}
    for a in audits:
        byfam.setdefault(a["family"],[]).append(a)

    final_suffix="_i00100.txt" if stage=="probe" else "_i01000.txt"
    start_suffix="_i00000.txt"
    report={
        "version":ANALYSIS_VERSION,
        "stage":stage,
        "metric":{
            "classification_metric":"shape_invariant_normalized_rms",
            "shape_resample_points":SHAPE_RESAMPLE_POINTS,
            "uniform_arclength_resampling":True,
            "cyclic_origin_alignment":True,
            "proper_kabsch_rotation":True,
            "orientation_reversal_alignment":False,
            "scale_fitted_away":False,
            "normalization":"mean radius of gyration of the two resampled curves",
            "legacy_metric_retained":"legacy_indexed_normalized_rms",
        },
        "families":{},
    }
    accepted=[]
    rows=[]

    for famdef in D["families"]:
        fam=famdef["name"]
        aa=byfam.get(fam,[])
        statuses={x["status"] for x in aa}
        fr={
            "category":famdef["category"],
            "kind":famdef["kind"],
            "statuses":sorted(statuses),
            "candidates":[],
        }

        if not aa:
            fr["classification"]="NOT_RUN"
            report["families"][fam]=fr
            continue
        if "RUN_FAILED" in statuses:
            fr["classification"]="RUN_FAILED"
            report["families"][fam]=fr
            continue
        if statuses=={"REJECTED"}:
            fr["classification"]="REJECTED_BY_KNOTPLOT"
            report["families"][fam]=fr
            continue
        if "REJECTED" in statuses:
            fr["classification"]="PARTIAL_REJECTION"
            report["families"][fam]=fr
            continue

        accepted.append(fam)
        items=[]
        start_hashes=set()
        for a in sorted(aa,key=lambda x:x["candidate"]):
            cid=a["candidate"]
            sp=ROOT/"out"/stage/f"{cid}{start_suffix}"
            fp=ROOT/"out"/stage/f"{cid}{final_suffix}"
            if not sp.is_file() or not fp.is_file():
                continue
            sm=metrics(sp)
            fm=metrics(fp)
            start_hashes.add(sm["sha256_geometry"])
            rec={"candidate":cid,"start":sm,"metrics":fm}
            items.append(rec)
            rows.append({
                "stage":stage,
                "family":fam,
                "candidate":cid,
                **{k:v for k,v in fm.items() if not k.startswith("_")},
            })

        fr["unique_start_geometries"]=len(start_hashes)
        if len(start_hashes)!=1:
            fr["classification"]="INVALID_NONCOMMON_START"
        elif len(items)<2:
            fr["classification"]="INSUFFICIENT_OUTPUTS"
        else:
            shape_best,legacy_best,pairs=pairwise_summary(items)
            nr,c1,c2,shift=shape_best
            lnr,lc1,lc2=legacy_best

            fr["max_pairwise_shape_invariant_normalized_rms"]=nr
            fr["max_shape_pair"]=[c1,c2]
            fr["max_shape_pair_cyclic_shift"]=shift

            fr["max_pairwise_legacy_indexed_normalized_rms"]=lnr
            fr["max_legacy_pair"]=[lc1,lc2]

            # Backward-readable aliases now point to the corrected metric.
            fr["max_pairwise_normalized_rms"]=nr
            fr["max_pair"]=[c1,c2]
            fr["pairwise_metric_audit"]=pairs
            fr["unique_final_geometries"]=len({
                x["metrics"]["sha256_geometry"] for x in items
            })
            fr["classification"]=classify(nr,stage)

        for x in items:
            x["start"].pop("_array",None)
            x["metrics"].pop("_array",None)
        fr["candidates"]=items
        report["families"][fam]=fr

    report["accepted_families"]=accepted

    out=ROOT/"analysis"/("PROBE.json" if stage=="probe" else "EXTENDED.json")
    # Preserve the old report automatically if present.
    if out.is_file():
        legacy=ROOT/"analysis"/(("PROBE_v0.3.2_LEGACY.json") if stage=="probe"
                               else ("EXTENDED_v0.3.2_LEGACY.json"))
        if not legacy.is_file():
            legacy.write_bytes(out.read_bytes())
    out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")

    csvp=ROOT/"analysis"/("probe_metrics.csv" if stage=="probe" else "extended_metrics.csv")
    if rows:
        cols=list(rows[0].keys())
        with csvp.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=cols)
            w.writeheader()
            w.writerows(rows)

    md=[
        "# KnotPlot 3.1 Parameter Effect Atlas — "+stage.upper()+" (v0.3.3)",
        "",
        "> Preparation/relaxation sensitivity atlas; not a physical Euler stability proof.",
        "",
        "Classification uses **uniform-arclength + cyclic-origin + proper-Kabsch RMS**.",
        "The v0.3.2 bead-index RMS is retained only as an audit metric.",
        "",
        "| family | category | classification | shape-invariant RMS | legacy indexed RMS |",
        "|---|---|---:|---:|---:|",
    ]
    order=[]
    for fam,fr in report["families"].items():
        nr=fr.get("max_pairwise_shape_invariant_normalized_rms")
        lnr=fr.get("max_pairwise_legacy_indexed_normalized_rms")
        md.append(
            f"| {fam} | {fr.get('category','')} | **{fr.get('classification','')}** | "
            f"{'' if nr is None else f'{nr:.6g}'} | "
            f"{'' if lnr is None else f'{lnr:.6g}'} |"
        )
        if nr is not None:
            order.append((nr,fam,fr.get("classification"),lnr))

    md+=["","## Shape-invariant effect ranking",""]
    for nr,fam,cls,lnr in sorted(order,reverse=True):
        md.append(f"- `{fam}`: shape={nr:.6g}; legacy-indexed={lnr:.6g} — {cls}")

    md+=["","## Metric audit note","",
         "- v0.3.2 paired bead index `i` with bead index `i` after rigid alignment.",
         "- v0.3.3 uniformly resamples both closed curves in arclength and searches all cyclic origins before Kabsch.",
         "- This suppresses false effect inflation from tangential bead redistribution.",
         "- Physical scale differences are deliberately retained.",
         "- Curve traversal reversal is not searched."]

    mdp=ROOT/"analysis"/("PROBE.md" if stage=="probe" else "EXTENDED.md")
    if mdp.is_file():
        legacy=ROOT/"analysis"/(("PROBE_v0.3.2_LEGACY.md") if stage=="probe"
                               else ("EXTENDED_v0.3.2_LEGACY.md"))
        if not legacy.is_file():
            legacy.write_bytes(mdp.read_bytes())
    mdp.write_text("\n".join(md)+"\n",encoding="utf-8")

    print(f"WROTE {out}")
    print(f"WROTE {mdp}")
    return 0

if __name__=="__main__":
    stage=sys.argv[1] if len(sys.argv)>1 else "probe"
    if stage not in ("probe","extended"):
        raise SystemExit("usage: analyze.py probe|extended")
    raise SystemExit(analyze(stage))
