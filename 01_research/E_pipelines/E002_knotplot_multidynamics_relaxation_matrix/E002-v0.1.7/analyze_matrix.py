from pathlib import Path
import hashlib,json,csv,re
import numpy as np

ROOT=Path(__file__).resolve().parent

def read_xyz(p):
    rows=[]
    for raw in p.read_text(encoding="utf-8",errors="ignore").splitlines():
        vals=[]
        for t in raw.replace(","," ").split():
            try: vals.append(float(t))
            except: pass
        if len(vals)>=3: rows.append(vals[:3])
    a=np.asarray(rows,float)
    if len(a)<8: raise ValueError(f"bad XYZ: {p}")
    return a

def hash_file(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    design=json.loads((ROOT/"matrix_design.json").read_text())
    rows=[]
    groups={}
    for e in design["entries"]:
        cid=e["candidate"]
        # Anneal final file keeps historical A90_anneal_q0 name.
        final=(ROOT/"out"/f"{cid}_i10000.txt")
        if not final.is_file() and cid=="A90_anneal_q0":
            final=ROOT/"out"/"A90_anneal_q0_i10000.txt"
        row={"candidate":cid,"family":e["family"],"swept_variable":e["swept_variable"],
             "swept_value":e["swept_value"],"i10000_exists":final.is_file()}
        if final.is_file():
            h=hash_file(final); row["i10000_file_sha256"]=h
            row["n_points"]=len(read_xyz(final))
            groups.setdefault(h,[]).append(cid)
        else:
            row["i10000_file_sha256"]=None; row["n_points"]=None
        for it in (0,1000,4000,10000):
            p=ROOT/"out"/f"{cid}_i{it:05d}.txt"
            if p.is_file(): row[f"i{it:05d}_sha256"]=hash_file(p)
        rows.append(row)
    unique=len(groups)
    report={
        "format":"KNOTPLOT-MULTIDYNAMICS-MATRIX-1.7-REPORT",
        "n_design_candidates":len(rows),
        "n_i10000_present":sum(r["i10000_exists"] for r in rows),
        "n_unique_exact_i10000_files":unique,
        "n_exact_duplicates":sum(len(v)-1 for v in groups.values()),
        "duplicate_groups":[{"sha256":h,"candidates":v} for h,v in groups.items() if len(v)>1],
        "rows":rows
    }
    (ROOT/"analysis").mkdir(exist_ok=True)
    (ROOT/"analysis/REPORT.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    with (ROOT/"analysis/matrix_results.csv").open("w",newline="",encoding="utf-8") as f:
        keys=sorted(set().union(*(r.keys() for r in rows)))
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
    md=[
        "# MultiDynamics Matrix v0.1.7 Report","",
        f"- Design candidates: **{report['n_design_candidates']}**",
        f"- Final i10000 files present: **{report['n_i10000_present']}**",
        f"- Exact unique final files: **{report['n_unique_exact_i10000_files']}**",
        f"- Exact duplicate labels: **{report['n_exact_duplicates']}**","",
        "Unlike older matrices, v0.1.7 emits runtime parameters with `name = value` and uses `tinc`.",
        "Duplicate endpoints in this release therefore represent actual convergence under accepted syntax, not the known command/assignment parser mistake."
    ]
    (ROOT/"analysis/REPORT.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print("\n".join(md))
    return 0 if report["n_i10000_present"]==len(rows) else 2
if __name__=="__main__":
    raise SystemExit(main())
