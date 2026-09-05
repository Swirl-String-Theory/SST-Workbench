from __future__ import annotations
from pathlib import Path
import csv,json,hashlib
import numpy as np
from geometry_utils import read_xyz,resample_closed,hash_resampled,kabsch_rms,curve_length,min_nonlocal_clearance

ROOT=Path(__file__).resolve().parent
HIST=json.loads((ROOT/"reference/v0.1.7_seen_canonical64_sha256.json").read_text(encoding="utf-8"))
SEEN=set(HIST["canonical64_sha256"])

def rows_for(pattern):
    return sorted((ROOT/"out").glob(pattern))

def main():
    finals=rows_for("*_i10000.txt")
    starts=rows_for("*_i00000.txt")
    if not finals:
        print("ERROR: no production *_i10000.txt files in out"); return 2
    data=[]
    groups={}
    for p in finals:
        x=read_xyz(p)
        h128=hash_resampled(x,128); h64=hash_resampled(x,64)
        cid=p.name[:-len("_i10000.txt")]
        row={
            "candidate":cid,
            "file":p.name,
            "canonical128_sha256":h128,
            "canonical64_sha256":h64,
            "seen_v0.1.7":h64 in SEEN,
            "length":curve_length(x),
            "dense_nonlocal_clearance":min_nonlocal_clearance(x,400,5),
        }
        p0=ROOT/"out"/f"{cid}_i00000.txt"
        if p0.is_file():
            x0=read_xyz(p0)
            row["start_to_final_kabsch_rms"]=kabsch_rms(resample_closed(x0,128),resample_closed(x,128))
        else:
            row["start_to_final_kabsch_rms"]=None
        data.append(row)
        groups.setdefault(h128,[]).append(cid)
    unique=list(groups)
    seen_unique=sum(any(r["canonical128_sha256"]==h and r["seen_v0.1.7"] for r in data) for h in unique)
    novel_unique=len(unique)-seen_unique

    # Rotation-invariant near-duplicate audit among exact-unique representatives.
    reps=[]
    for h,cids in groups.items():
        p=ROOT/"out"/f"{cids[0]}_i10000.txt"
        reps.append((h,cids[0],resample_closed(read_xyz(p),128)))
    near_pairs=[]
    for i in range(len(reps)):
        hi,ci,xi=reps[i]
        scale=max(np.sqrt(np.mean(np.sum(xi*xi,axis=1))),1e-300)
        for j in range(i+1,len(reps)):
            hj,cj,xj=reps[j]
            rms=kabsch_rms(xi,xj)/scale
            if rms < 1e-8:
                near_pairs.append({"a":ci,"b":cj,"normalized_kabsch_rms":rms})

    report={
        "format":"SST-TREFOIL-SEED-CAMPAIGN-REPORT-1.0",
        "n_source_i10000":len(finals),
        "n_source_i00000":len(starts),
        "n_unique_identity128":len(unique),
        "n_duplicates_removed":len(finals)-len(unique),
        "n_seen_v0.1.7_unique":seen_unique,
        "n_novel_unique":novel_unique,
        "confirmatory_input_pass":novel_unique>=8,
        "preferred_target_pass":novel_unique>=12,
        "max_exact_multiplicity":max(map(len,groups.values())),
        "near_duplicate_pairs_after_kabsch":near_pairs,
        "exact_duplicate_groups":[{"hash":h,"candidates":c} for h,c in groups.items() if len(c)>1],
        "rows":data
    }
    ad=ROOT/"analysis"; ad.mkdir(exist_ok=True)
    (ad/"REPORT.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    if data:
        with (ad/"candidates.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(data[0].keys()))
            w.writeheader(); w.writerows(data)
    md=[
        "# Trefoil Seed Campaign Report",
        "",
        f"- Production `i10000` files: **{len(finals)}**",
        f"- Unique identity128 endpoints: **{len(unique)}**",
        f"- Exact duplicate files removed: **{len(finals)-len(unique)}**",
        f"- Unique endpoints already seen in v0.1.7: **{seen_unique}**",
        f"- Novel unique endpoints: **{novel_unique}**",
        f"- Phase-delay v0.2 confirmatory input gate (`>=8 novel`): **{'PASS' if novel_unique>=8 else 'INSUFFICIENT'}**",
        f"- Preferred target (`>=12 novel`): **{'PASS' if novel_unique>=12 else 'NOT MET'}**",
        f"- Rotation-invariant near-duplicate pairs at normalized Kabsch RMS < 1e-8: **{len(near_pairs)}**",
        "",
        "This report is a dataset-generation audit, not a phase-delay physics result."
    ]
    (ad/"REPORT.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print("\n".join(md))
    return 0 if novel_unique>=8 else 3

if __name__=="__main__":
    raise SystemExit(main())
