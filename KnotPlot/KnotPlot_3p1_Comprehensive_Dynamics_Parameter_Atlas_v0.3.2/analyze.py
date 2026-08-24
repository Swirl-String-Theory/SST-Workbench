from __future__ import annotations
from pathlib import Path
import json,hashlib,math,csv,re,sys
import numpy as np

ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"parameter_manifest.json").read_text())
TH=float(D["effect_threshold_normalized_rms"])

def read_xyz(path):
    rows=[]
    for line in path.read_text(encoding="utf-8",errors="replace").splitlines():
        s=line.strip()
        if not s or s.startswith(("#","%")): continue
        parts=s.replace(","," ").split()
        if len(parts)<3: continue
        try: rows.append([float(parts[0]),float(parts[1]),float(parts[2])])
        except ValueError: pass
    a=np.asarray(rows,float)
    if a.ndim!=2 or a.shape[0]<4 or a.shape[1]!=3:
        raise ValueError(f"bad XYZ {path}: shape {a.shape}")
    return a

def center(a): return a-a.mean(axis=0)

def kabsch_rms(a,b):
    if a.shape!=b.shape: return float("nan")
    aa=center(a); bb=center(b)
    h=aa.T@bb
    u,s,vt=np.linalg.svd(h)
    r=vt.T@u.T
    if np.linalg.det(r)<0:
        vt[-1]*=-1; r=vt.T@u.T
    d=aa@r-bb
    return float(np.sqrt(np.mean(np.sum(d*d,axis=1))))

def length(a):
    return float(np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1).sum())

def rg(a):
    c=center(a); return float(np.sqrt(np.mean(np.sum(c*c,axis=1))))

def turns(a):
    e1=a-np.roll(a,1,axis=0); e2=np.roll(a,-1,axis=0)-a
    n1=np.linalg.norm(e1,axis=1); n2=np.linalg.norm(e2,axis=1)
    cos=np.sum(e1*e2,axis=1)/np.maximum(n1*n2,1e-30)
    ang=np.arccos(np.clip(cos,-1,1))
    return float(np.mean(ang)),float(np.max(ang))

def min_nonlocal_point_distance(a,skip=3):
    n=len(a); best=float("inf")
    for i in range(n):
        d=np.linalg.norm(a-a[i],axis=1)
        for off in range(-skip,skip+1):
            d[(i+off)%n]=np.inf
        best=min(best,float(np.min(d)))
    return best

def hash_arr(a):
    x=np.asarray(a,dtype="<f8")
    return hashlib.sha256(x.tobytes()).hexdigest()

def metrics(path):
    a=read_xyz(path)
    mt,xt=turns(a)
    return {
        "file":str(path),"n":len(a),"sha256_geometry":hash_arr(a),
        "length":length(a),"rg":rg(a),"mean_turn":mt,"max_turn":xt,
        "min_nonlocal_point_distance":min_nonlocal_point_distance(a),
        "_array":a
    }

def pairwise_max(items):
    best=(0.0,None,None)
    for i in range(len(items)):
        for j in range(i+1,len(items)):
            a=items[i]["metrics"]["_array"]; b=items[j]["metrics"]["_array"]
            r=kabsch_rms(a,b)
            scale=max((items[i]["metrics"]["rg"]+items[j]["metrics"]["rg"])/2,1e-30)
            nr=r/scale
            if nr>best[0]: best=(nr,items[i]["candidate"],items[j]["candidate"])
    return best

def analyze(stage):
    (ROOT/"analysis").mkdir(parents=True, exist_ok=True)
    audit_files=sorted((ROOT/"logs"/stage).glob("*_audit.json"))
    audits=[json.loads(p.read_text()) for p in audit_files]
    byfam={}
    for a in audits: byfam.setdefault(a["family"],[]).append(a)
    final_suffix="_i00100.txt" if stage=="probe" else "_i01000.txt"
    start_suffix="_i00000.txt"
    report={"version":"0.3.0","stage":stage,"families":{}}
    accepted=[]
    rows=[]
    for famdef in D["families"]:
        fam=famdef["name"]; aa=byfam.get(fam,[])
        statuses={x["status"] for x in aa}
        fr={"category":famdef["category"],"kind":famdef["kind"],"statuses":sorted(statuses),"candidates":[]}
        if not aa:
            fr["classification"]="NOT_RUN"; report["families"][fam]=fr; continue
        if "RUN_FAILED" in statuses:
            fr["classification"]="RUN_FAILED"; report["families"][fam]=fr; continue
        if statuses=={"REJECTED"}:
            fr["classification"]="REJECTED_BY_KNOTPLOT"; report["families"][fam]=fr; continue
        if "REJECTED" in statuses:
            fr["classification"]="PARTIAL_REJECTION"; report["families"][fam]=fr; continue
        accepted.append(fam)
        items=[]
        start_hashes=set()
        for a in sorted(aa,key=lambda x:x["candidate"]):
            cid=a["candidate"]
            sp=ROOT/"out"/stage/f"{cid}{start_suffix}"
            fp=ROOT/"out"/stage/f"{cid}{final_suffix}"
            if not sp.is_file() or not fp.is_file(): continue
            sm=metrics(sp); fm=metrics(fp)
            start_hashes.add(sm["sha256_geometry"])
            rec={"candidate":cid,"start":sm,"metrics":fm}
            items.append(rec)
            rows.append({
                "stage":stage,"family":fam,"candidate":cid,
                **{k:v for k,v in fm.items() if not k.startswith("_")}
            })
        fr["unique_start_geometries"]=len(start_hashes)
        if len(start_hashes)!=1:
            fr["classification"]="INVALID_NONCOMMON_START"
        elif len(items)<2:
            fr["classification"]="INSUFFICIENT_OUTPUTS"
        else:
            nr,c1,c2=pairwise_max(items)
            fr["max_pairwise_normalized_rms"]=nr
            fr["max_pair"]= [c1,c2]
            fr["unique_final_geometries"]=len({x["metrics"]["sha256_geometry"] for x in items})
            if nr>=1e-2: cls="EFFECTIVE_STRONG"
            elif nr>=1e-3: cls="EFFECTIVE_MEDIUM"
            elif nr>=TH: cls="EFFECTIVE_WEAK"
            else: cls="NULL_AT_"+("100" if stage=="probe" else "1000")
            fr["classification"]=cls
        # Strip arrays from JSON
        for x in items:
            x["start"].pop("_array",None); x["metrics"].pop("_array",None)
        fr["candidates"]=items
        report["families"][fam]=fr

    report["accepted_families"]=accepted
    out=ROOT/"analysis"/("PROBE.json" if stage=="probe" else "EXTENDED.json")
    out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    csvp=ROOT/"analysis"/("probe_metrics.csv" if stage=="probe" else "extended_metrics.csv")
    if rows:
        cols=list(rows[0].keys())
        with csvp.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=cols); w.writeheader(); w.writerows(rows)

    md=["# KnotPlot 3.1 Parameter Effect Atlas — "+stage.upper(),"",
        "> This is a preparation/relaxation sensitivity atlas. It is **not** a physical Euler stability proof.","",
        "| family | category | classification | max normalized RMS |",
        "|---|---|---:|---:|"]
    order=[]
    for fam,fr in report["families"].items():
        nr=fr.get("max_pairwise_normalized_rms")
        md.append(f"| {fam} | {fr.get('category','')} | **{fr.get('classification','')}** | {'' if nr is None else f'{nr:.6g}'} |")
        if nr is not None: order.append((nr,fam,fr.get("classification")))
    md+=["","## Effect ranking",""]
    for nr,fam,cls in sorted(order,reverse=True):
        md.append(f"- `{fam}`: {nr:.6g} — {cls}")
    (ROOT/"analysis"/("PROBE.md" if stage=="probe" else "EXTENDED.md")).write_text("\n".join(md)+"\n",encoding="utf-8")

    # downstream manifest from unique extended finals
    if stage=="extended":
        seen=set(); ds=[]
        for fam,fr in report["families"].items():
            for c in fr.get("candidates",[]):
                h=c["metrics"]["sha256_geometry"]
                if h in seen: continue
                seen.add(h)
                ds.append({
                    "family":fam,"candidate":c["candidate"],
                    "classification":fr.get("classification"),
                    "geometry_sha256":h,"file":c["metrics"]["file"]
                })
        with (ROOT/"analysis"/"downstream_unique_i01000.csv").open("w",newline="",encoding="utf-8") as f:
            if ds:
                w=csv.DictWriter(f,fieldnames=ds[0].keys()); w.writeheader(); w.writerows(ds)
    print((ROOT/"analysis"/("PROBE.md" if stage=="probe" else "EXTENDED.md")).read_text())
    return 0

if __name__=="__main__":
    if len(sys.argv)!=2 or sys.argv[1] not in ("probe","extended"):
        raise SystemExit("usage: analyze.py probe|extended")
    raise SystemExit(analyze(sys.argv[1]))
