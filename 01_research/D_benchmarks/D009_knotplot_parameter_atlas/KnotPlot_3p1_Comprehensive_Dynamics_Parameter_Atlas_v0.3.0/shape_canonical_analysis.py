from __future__ import annotations
from pathlib import Path
import argparse, csv, hashlib, json, math, re
import numpy as np

ROOT=Path(__file__).resolve().parent
DESIGN=json.loads((ROOT/"parameter_manifest.json").read_text(encoding="utf-8"))
TH=float(DESIGN.get("effect_threshold_normalized_rms",1e-5))

def read_xyz(path: Path) -> np.ndarray:
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
        raise ValueError(f"bad XYZ {path}: shape={a.shape}")
    return a

def center(a):
    return np.asarray(a,float)-np.asarray(a,float).mean(axis=0)

def kabsch_rms(a,b):
    """Row-vector Kabsch: minimize ||A R - B|| with R = U V^T."""
    if a.shape!=b.shape:
        return float("nan")
    aa=center(a); bb=center(b)
    h=aa.T@bb
    u,s,vt=np.linalg.svd(h)
    r=u@vt
    if np.linalg.det(r)<0:
        u=u.copy()
        u[:,-1]*=-1
        r=u@vt
    d=aa@r-bb
    return float(np.sqrt(np.mean(np.sum(d*d,axis=1))))

def closed_arclength_resample(a,n=300):
    a=np.asarray(a,float)
    d=np.roll(a,-1,axis=0)-a
    seg=np.linalg.norm(d,axis=1)
    total=float(seg.sum())
    if not np.isfinite(total) or total<=0:
        raise ValueError("non-positive closed curve length")
    nodes=np.concatenate([[0.0],np.cumsum(seg)])
    ext=np.vstack([a,a[0]])
    target=np.linspace(0.0,total,n,endpoint=False)
    out=np.empty((n,3),float)
    for k in range(3):
        out[:,k]=np.interp(target,nodes,ext[:,k])
    return out

def phase_kabsch_rms(a,b,allow_reverse=False):
    """Minimize Kabsch RMS over cyclic phase. Orientation is preserved by default."""
    if a.shape!=b.shape:
        return float("nan"),None,False
    best=(float("inf"),None,False)
    variants=[(b,False)]
    if allow_reverse:
        variants.append((b[::-1].copy(),True))
    for bv,rev in variants:
        for shift in range(len(bv)):
            r=kabsch_rms(a,np.roll(bv,shift,axis=0))
            if r<best[0]:
                best=(r,shift,rev)
    return best

def length(a):
    return float(np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1).sum())

def rg(a):
    c=center(a)
    return float(np.sqrt(np.mean(np.sum(c*c,axis=1))))

def turns(a):
    e1=a-np.roll(a,1,axis=0)
    e2=np.roll(a,-1,axis=0)-a
    n1=np.linalg.norm(e1,axis=1); n2=np.linalg.norm(e2,axis=1)
    co=np.sum(e1*e2,axis=1)/np.maximum(n1*n2,1e-30)
    ang=np.arccos(np.clip(co,-1,1))
    return float(np.mean(ang)),float(np.max(ang))

def sha_array(a):
    return hashlib.sha256(np.asarray(a,dtype="<f8").tobytes()).hexdigest()

def candidate_value(candidate,family):
    token=candidate.split("__",1)[1]
    if token in ("on","off","true","false"):
        return token
    token=token.replace("m","-").replace("p",".")
    try:
        return float(token)
    except Exception:
        return token

def effect_class(nr,stage="extended"):
    suffix="1000" if stage=="extended" else "100"
    if nr>=1e-2: return "EFFECTIVE_STRONG"
    if nr>=1e-3: return "EFFECTIVE_MEDIUM"
    if nr>=TH: return "EFFECTIVE_WEAK"
    return f"NULL_AT_{suffix}"

def pairwise_family(items,nresample=300):
    best_raw=(0.0,None,None)
    best_shape=(0.0,None,None,None)
    rows=[]
    for i in range(len(items)):
        for j in range(i+1,len(items)):
            A=items[i]; B=items[j]
            a=A["array"]; b=B["array"]
            scale=max((A["rg"]+B["rg"])/2,1e-30)
            raw=kabsch_rms(a,b)/scale if a.shape==b.shape else float("nan")
            ar=A["arc"]; br=B["arc"]
            sr,shift,rev=phase_kabsch_rms(ar,br,allow_reverse=False)
            shape=sr/max((rg(ar)+rg(br))/2,1e-30)
            rec={
                "a":A["candidate"],"b":B["candidate"],
                "raw_indexed_normalized_rms":raw,
                "shape_arclength_phase_normalized_rms":shape,
                "best_phase_shift":shift,
                "orientation_reversed":rev,
            }
            rows.append(rec)
            if np.isfinite(raw) and raw>best_raw[0]:
                best_raw=(raw,A["candidate"],B["candidate"])
            if np.isfinite(shape) and shape>best_shape[0]:
                best_shape=(shape,A["candidate"],B["candidate"],shift)
    return best_raw,best_shape,rows

def parameterization_role(raw,shape):
    if raw is None or shape is None or not np.isfinite(raw) or not np.isfinite(shape):
        return "UNDETERMINED"
    if raw<TH and shape<TH:
        return "NULL"
    ratio=shape/max(raw,1e-30)
    if raw>=1e-2 and shape<1e-3 and ratio<=0.10:
        return "REPARAMETERIZATION_DOMINATED"
    if raw>=1e-3 and ratio<=0.25:
        return "MIXED_REPARAMETERIZATION_DOMINANT"
    if shape>=TH:
        return "GEOMETRY_DOMINANT"
    return "INDEXING_EFFECT_ONLY"

def family_status_from_audits(stage,fam):
    audits=[]
    for p in sorted((ROOT/"logs"/stage).glob(f"{fam}__*_audit.json")):
        try:
            audits.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            pass
    if not audits:
        return "NOT_RUN"
    statuses={a.get("status","") for a in audits}
    for a in audits:
        if a.get("status")=="HEADLESS_UNSUPPORTED":
            return "HEADLESS_UNSUPPORTED"
        lp=a.get("log")
        if lp:
            q=Path(lp)
            if not q.is_absolute():
                q=ROOT/q
            if q.is_file():
                t=q.read_text(encoding="utf-8",errors="replace").lower()
                if "freeglut" in t and ("glutsetwindow" in t or "glutinit" in t):
                    return "HEADLESS_UNSUPPORTED"
    if "RUN_FAILED" in statuses:
        return "RUN_FAILED"
    if statuses=={"REJECTED"}:
        return "REJECTED_BY_KNOTPLOT"
    if "REJECTED" in statuses:
        return "PARTIAL_REJECTION"
    return "ACCEPTED"

def analyze(stage="extended",nresample=300):
    (ROOT/"analysis").mkdir(parents=True,exist_ok=True)
    suffix="_i01000.txt" if stage=="extended" else "_i00100.txt"
    report={
        "version":"0.3.3",
        "stage":stage,
        "n_arclength_resample":nresample,
        "kabsch_convention":"row vectors, H=A.T@B, R=U@Vt, det(R)>0",
        "cyclic_phase_alignment":True,
        "orientation_reversal_allowed":False,
        "families":{}
    }
    summary_rows=[]
    pair_rows=[]
    for famdef in DESIGN["families"]:
        fam=famdef["name"]
        status=family_status_from_audits(stage,fam)
        fr={
            "category":famdef["category"],"kind":famdef["kind"],
            "default":famdef.get("default"),"runtime_status":status,
        }
        if status!="ACCEPTED":
            fr["shape_classification"]=status
            report["families"][fam]=fr
            continue
        items=[]
        for fp in sorted((ROOT/"out"/stage).glob(f"{fam}__*{suffix}")):
            cid=fp.name[:-len(suffix)]
            a=read_xyz(fp)
            arc=closed_arclength_resample(a,nresample)
            mt,xt=turns(a)
            items.append({
                "candidate":cid,
                "value":candidate_value(cid,fam),
                "file":str(fp),
                "array":a,
                "arc":arc,
                "n":len(a),"length":length(a),"rg":rg(a),
                "mean_turn":mt,"max_turn":xt,
                "raw_sha256":sha_array(a),
                "arclength_sha256":sha_array(arc),
            })
        if len(items)<2:
            fr["shape_classification"]="INSUFFICIENT_OUTPUTS"
            fr["n_candidates"]=len(items)
            report["families"][fam]=fr
            continue
        br,bs,pairs=pairwise_family(items,nresample)
        raw=br[0]; shape=bs[0]
        fr.update({
            "n_candidates":len(items),
            "max_raw_indexed_normalized_rms":raw,
            "max_raw_pair":[br[1],br[2]],
            "max_shape_arclength_phase_normalized_rms":shape,
            "max_shape_pair":[bs[1],bs[2]],
            "max_shape_phase_shift":bs[3],
            "raw_effect_classification":effect_class(raw,stage),
            "shape_classification":effect_class(shape,stage),
            "parameterization_role":parameterization_role(raw,shape),
            "shape_to_raw_ratio":shape/max(raw,1e-30),
            "unique_raw_sha256":len({x["raw_sha256"] for x in items}),
            "candidates":[{k:v for k,v in x.items() if k not in ("array","arc")} for x in items],
        })
        report["families"][fam]=fr
        summary_rows.append({
            "family":fam,"category":famdef["category"],
            "runtime_status":status,
            "raw_indexed_normalized_rms":raw,
            "shape_arclength_phase_normalized_rms":shape,
            "shape_to_raw_ratio":fr["shape_to_raw_ratio"],
            "raw_effect_classification":fr["raw_effect_classification"],
            "shape_classification":fr["shape_classification"],
            "parameterization_role":fr["parameterization_role"],
            "max_raw_pair":" | ".join(fr["max_raw_pair"]),
            "max_shape_pair":" | ".join(fr["max_shape_pair"]),
        })
        for r in pairs:
            r.update({"family":fam,"category":famdef["category"]})
            pair_rows.append(r)

    base=ROOT/"analysis"/f"SHAPE_CANONICAL_{stage.upper()}"
    (base.with_suffix(".json")).write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    if summary_rows:
        with (base.with_suffix(".csv")).open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(summary_rows[0].keys()))
            w.writeheader(); w.writerows(summary_rows)
    if pair_rows:
        pp=ROOT/"analysis"/f"SHAPE_CANONICAL_{stage.upper()}_PAIRS.csv"
        with pp.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(pair_rows[0].keys()))
            w.writeheader(); w.writerows(pair_rows)

    md=[
        f"# Shape-Canonical KnotPlot 3.1 Atlas — {stage.upper()}","",
        "> Raw indexed RMS is bead-index sensitive. Shape RMS first uniformly resamples the closed curve by arclength, then minimizes over cyclic phase and proper 3-D rotations.","",
        "| family | raw indexed RMS | shape RMS | shape/raw | shape class | role |",
        "|---|---:|---:|---:|---|---|"
    ]
    ranked=[]
    for fam,fr in report["families"].items():
        if "max_shape_arclength_phase_normalized_rms" not in fr:
            md.append(f"| {fam} |  |  |  | {fr.get('shape_classification','')} |  |")
            continue
        raw=fr["max_raw_indexed_normalized_rms"]
        shape=fr["max_shape_arclength_phase_normalized_rms"]
        ratio=fr["shape_to_raw_ratio"]
        md.append(f"| {fam} | {raw:.6g} | {shape:.6g} | {ratio:.4g} | **{fr['shape_classification']}** | {fr['parameterization_role']} |")
        ranked.append((shape,fam,fr))
    md += ["","## Shape-effect ranking",""]
    for shape,fam,fr in sorted(ranked,reverse=True):
        md.append(f"- `{fam}`: shape={shape:.6g}; raw={fr['max_raw_indexed_normalized_rms']:.6g}; {fr['parameterization_role']}")
    md += ["","## Interpretation gate","",
           "- `REPARAMETERIZATION_DOMINATED`: large bead-index movement, small canonical shape change.",
           "- `GEOMETRY_DOMINANT`: arclength/phase canonicalization does not remove the effect.",
           "- Orientation reversal is deliberately **not** allowed, preserving curve orientation/circulation semantics."]
    (base.with_suffix(".md")).write_text("\n".join(md)+"\n",encoding="utf-8")
    print((base.with_suffix(".md")).read_text(encoding="utf-8"))
    return report

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--stage",choices=["probe","extended"],default="extended")
    ap.add_argument("--nresample",type=int,default=300)
    a=ap.parse_args()
    analyze(a.stage,a.nresample)
