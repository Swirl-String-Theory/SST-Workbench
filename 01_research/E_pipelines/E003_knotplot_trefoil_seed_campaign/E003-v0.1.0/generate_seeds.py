from __future__ import annotations
from pathlib import Path
import json,hashlib
import numpy as np
from geometry_utils import (
    read_xyz,write_xyz,resample_closed,bishop_frame_closed,
    min_nonlocal_clearance,hash_resampled,center
)

ROOT=Path(__file__).resolve().parent
CFG=json.loads((ROOT/"campaign_config.json").read_text(encoding="utf-8"))
MAN=json.loads((ROOT/"seed_manifest.json").read_text(encoding="utf-8"))

def normalized_field(field):
    q=np.sqrt(np.mean(np.sum(field*field,axis=1)))
    if not np.isfinite(q) or q<=0: raise ValueError("degenerate perturbation field")
    return field/q

def build_seed(base,spec,d0):
    x=center(base)
    N=len(x)
    _,n,b=bishop_frame_closed(x)
    th=2*np.pi*np.arange(N)/N
    fam=spec["family"]
    if fam=="bishop_helical":
        m=int(spec["mode"]); ph=float(spec["phase_rad"]); chi=float(spec["chirality"])
        field=np.cos(m*th+ph)[:,None]*n + chi*np.sin(m*th+ph)[:,None]*b
        field=normalized_field(field)
        y=x + float(spec["amplitude_over_base_gap"])*d0*field
    elif fam=="bishop_mixed":
        m1=int(spec["mode_n"]); m2=int(spec["mode_b"])
        p1=float(spec["phase_n_rad"]); p2=float(spec["phase_b_rad"])
        w=float(spec["binormal_weight"])
        field=np.cos(m1*th+p1)[:,None]*n + w*np.sin(m2*th+p2)[:,None]*b
        field=normalized_field(field)
        y=x + float(spec["amplitude_over_base_gap"])*d0*field
    elif fam=="pca_affine":
        s=np.asarray(spec["principal_axis_scales"],float)
        if np.any(s<=0) or np.prod(s)<=0: raise ValueError("affine scales must be positive")
        C=x.T@x/len(x)
        _,V=np.linalg.eigh(C)
        A=V@np.diag(s)@V.T
        y=x@A
    else:
        raise ValueError(f"unknown seed family {fam}")
    return center(y)

def check_homotopy(base,seed,d0):
    sc=CFG["seed_safety"]
    min_h=float("inf")
    worst_u=None
    ns=int(sc["dense_clearance_samples"])
    skip=int(sc["local_skip_samples"])
    for u in np.linspace(0.0,1.0,int(sc["homotopy_steps"])):
        z=(1-u)*base+u*seed
        d=min_nonlocal_clearance(z,ns,skip)
        if d<min_h:
            min_h=d; worst_u=float(u)
    d1=min_nonlocal_clearance(seed,ns,skip)
    ok=(min_h >= float(sc["minimum_homotopy_gap_fraction"])*d0 and
        d1 >= float(sc["minimum_final_gap_fraction"])*d0)
    return ok,d1,min_h,worst_u

def main():
    base_path=ROOT/"base/base_3p1_300.txt"
    if not base_path.is_file():
        raise SystemExit("ERROR: base/base_3p1_300.txt missing; run run_05_export_base.cmd first.")
    base=resample_closed(read_xyz(base_path),int(CFG["nbeads"]))
    d0=min_nonlocal_clearance(base,int(CFG["seed_safety"]["dense_clearance_samples"]),int(CFG["seed_safety"]["local_skip_samples"]))
    if not np.isfinite(d0) or d0<=0:
        raise SystemExit("ERROR: invalid base non-adjacent gap")
    outdir=ROOT/"seeds"; outdir.mkdir(exist_ok=True)
    for p in outdir.glob("S*.txt"): p.unlink()
    resolved=[]
    failures=[]
    for spec in MAN["seeds"]:
        y=build_seed(base,spec,d0)
        ok,d1,min_h,worst_u=check_homotopy(base,y,d0)
        sid=spec["seed_id"]
        row=dict(spec)
        row.update({
            "base_gap":d0,
            "seed_gap":d1,
            "seed_gap_over_base":d1/d0,
            "minimum_homotopy_gap":min_h,
            "minimum_homotopy_gap_over_base":min_h/d0,
            "minimum_homotopy_gap_u":worst_u,
            "safety_pass":bool(ok),
            "canonical128_sha256":hash_resampled(y,128),
            "canonical64_sha256":hash_resampled(y,64),
        })
        if ok:
            path=outdir/f"{sid}_{spec['family']}.txt"
            write_xyz(path,y)
            row["file"]=path.name
            row["file_sha256"]=hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            failures.append(row)
        resolved.append(row)
    report={
        "format":"SST-TREFOIL-SEED-RESOLVED-1.0",
        "base_file":str(base_path),
        "base_gap":d0,
        "n_requested":len(MAN["seeds"]),
        "n_safe":sum(r["safety_pass"] for r in resolved),
        "n_failed":len(failures),
        "seeds":resolved
    }
    (outdir/"resolved_manifest.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(f"[SEEDS] base dense nonlocal clearance: {d0:.9g}")
    print(f"[SEEDS] requested={report['n_requested']} safe={report['n_safe']} failed={report['n_failed']}")
    for r in resolved:
        print(f"  {r['seed_id']} {r['family']:14s} gap/base={r['seed_gap_over_base']:.3f} "
              f"homotopy_min/base={r['minimum_homotopy_gap_over_base']:.3f} "
              f"{'PASS' if r['safety_pass'] else 'FAIL'}")
    if failures:
        print("ERROR: preregistered seed safety failure; amplitudes are NOT auto-tuned.")
        return 3
    hashes=[r["canonical128_sha256"] for r in resolved]
    if len(set(hashes)) != len(hashes):
        print("ERROR: preregistered initial seeds are not unique at identity128 resolution.")
        return 4
    print("[SEEDS] INITIAL UNIQUE-ID PASS:",len(hashes),"unique seeds")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
