from __future__ import annotations
from pathlib import Path
import math, random, itertools, csv
from .util import *
from .blind import verify_seal

POSITIVE_FEATURES=["bend_energy","abs_neumann_energy","contact_ratio","abs_writhe","linking_strength"]

def _feature_value(r,f):
    v=abs(float(r[f]))
    if f in ("abs_writhe","linking_strength"): v += 1e-6
    return max(v,1e-12)

def _target_shape(masses):
    lm=sorted(math.log(max(float(m),1e-15)) for m in masses)
    mm=sum(lm)/3.0
    return (lm[0]-mm,lm[1]-mm,lm[2]-mm),mm

def _build_triplet_cache(rows, feat, pool):
    rr=[r for r in rows if pool=="all" or r["kind"]==pool[:-1]]
    ordered=sorted((math.log(_feature_value(r,feat)),_feature_value(r,feat),r["case_id"]) for r in rr)
    out=[]
    n=len(ordered)
    for i in range(n-2):
        xi,vi,ci=ordered[i]
        for j in range(i+1,n-1):
            xj,vj,cj=ordered[j]
            for k in range(j+1,n):
                xk,vk,ck=ordered[k]
                xm=(xi+xj+xk)/3.0
                out.append((xi-xm,xj-xm,xk-xm,xm,ci,cj,ck,vi,vj,vk))
    return out

def _best_triplet_cached(cache, masses):
    tm,tmean=_target_shape(masses)
    best_err=float("inf"); best=None
    t0,t1,t2=tm
    for c0,c1,c2,xmean,ca,cb,cc,v0,v1,v2 in cache:
        d0=c0-t0; d1=c1-t1; d2=c2-t2
        err2=(d0*d0+d1*d1+d2*d2)/3.0
        if err2 < best_err:
            best_err=err2
            best=(xmean,ca,cb,cc,v0,v1,v2)
    xmean,ca,cb,cc,v0,v1,v2=best
    return {
        "log_rms":math.sqrt(best_err),
        "scale":math.exp(tmean-xmean),
        "case_ids":[ca,cb,cc],
        "feature_values":[v0,v1,v2]
    }

def run_reveal(root: Path, out: Path):
    ok,seal=verify_seal(out)
    if not ok: raise RuntimeError(f"Blind seal verification failed: {seal}")
    blind=out/"BLIND"; private=out/"PRIVATE_REVEAL_DO_NOT_INCLUDE_IN_BLIND"; rev=out/"REVEALED"
    rev.mkdir(parents=True,exist_ok=True)
    mapping=load_json(private/"mapping.json")
    rows=load_json(blind/"FEATURES.json")
    for r in rows: r["topology_id"]=mapping[r["case_id"]]
    write_json(rev/"FEATURES_REVEALED.json",rows)
    with (rev/"FEATURES_REVEALED.csv").open("w",newline="",encoding="utf-8") as f:
        fields=list(rows[0].keys()); w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

    hist=load_json(root/"reveal"/"historical_hypotheses.json")
    sm=load_json(root/"reveal"/"sm_reference_2026.json")
    write_json(rev/"HISTORICAL_HYPOTHESES_SNAPSHOT.json",hist)
    write_json(rev/"SM_REFERENCE_SNAPSHOT.json",sm)

    inv={v:k for k,v in mapping.items()}
    a=inv["5_2"]; b=inv["6_1"]
    allpairs=load_json(blind/"PAIR_ALL.json")
    knotpairs=[p for p in allpairs if p["kind_a"]=="knot" and p["kind_b"]=="knot"]
    target=next(p for p in knotpairs if {p["case_a"],p["case_b"]}=={a,b})
    rank=1+next(i for i,p in enumerate(knotpairs) if {p["case_a"],p["case_b"]}=={a,b})
    historical_result={
        "u_candidate":"5_2","d_candidate":"6_1",
        "blind_feature_distance":target["distance"],
        "rank_among_all_knot_pairs_by_blind_distance":rank,
        "knot_pair_count":len(knotpairs),
        "rank_fraction":rank/len(knotpairs),
        "interpretation":"Lower rank means the historical pair is more nearly adjacent in the preregistered blind screening feature space. This is not a quark identification."
    }
    write_json(rev/"HISTORICAL_5_2_6_1_CHECK.json",historical_result)

    cfg=load_json(blind/"config_frozen.json")
    masses=sm["masses"]
    fit={}
    rng=random.Random(5401001)
    triplet_cache={(feat,pool):_build_triplet_cache(rows,feat,pool)
                   for feat in POSITIVE_FEATURES for pool in ("knots","links","all")}
    for group,names in sm["groups"].items():
        ms=[masses[n] for n in names]
        fit[group]={"particle_names":names,"masses_MeV":ms,"features":{}}
        span=max(ms)/min(ms)
        for feat in POSITIVE_FEATURES:
            feat_out={}
            for pool in ("knots","links","all"):
                best=_best_triplet_cached(triplet_cache[(feat,pool)],ms)
                # null: preserve min/max span, randomize middle log-position
                null_best=[]
                nnull=int(cfg.get("null_targets",5))
                lo=min(ms); hi=max(ms)
                for _ in range(nnull):
                    t=rng.random()
                    mid=lo*math.exp(t*math.log(hi/lo))
                    nb=_best_triplet_cached(triplet_cache[(feat,pool)],[lo,mid,hi])
                    null_best.append(nb["log_rms"])
                p=(1+sum(x<=best["log_rms"] for x in null_best))/(1+len(null_best))
                best["null_best_log_rms"]=null_best
                best["look_elsewhere_null_fraction"]=p
                best["topologies"]=[mapping[c] for c in best["case_ids"]]
                feat_out[pool]=best
            fit[group]["features"][feat]=feat_out
    write_json(rev/"SM_RATIO_SEARCH.json",fit)

    bestlines=[]
    for group,g in fit.items():
        candidates=[]
        for feat,fd in g["features"].items():
            x=fd["all"]
            candidates.append((x["log_rms"],feat,x))
        candidates.sort(key=lambda q:q[0])
        e,feat,x=candidates[0]
        bestlines.append(f"- **{group}**: best all-atlas proxy `{feat}` -> {x['topologies']}; log-RMS={e:.6g}; null fraction={x['look_elsewhere_null_fraction']:.3g}.")
    report=f"""# A054 v0.1.0 — REVEALED report

Blind seal verified: `{seal}`.

## Historical VAM/SST quark check

Historical mapping: `u -> 5_2`, `d -> 6_1` (twist-knot pair).

- Blind feature-space rank among knot pairs: **{rank}/{len(knotpairs)}**
- Rank fraction: **{rank/len(knotpairs):.6f}**
- Frozen feature distance: **{target["distance"]:.9g}**

This is an independent adjacency diagnostic because `5_2/6_1` was not available to the blind stage.

## Exploratory SM mass-pattern reveal

{chr(10).join(bestlines)}

The triplet search fits one free overall scale and compares only the *shape* of three masses in log-space. The reported null fraction uses random intermediate target positions at the same total mass span and repeats the full atlas search.

## Mandatory interpretation limits

1. v0.1.0 does **not** identify a knot/link with an SM particle.
2. PD-derived embeddings are presentation ensembles, not PKLSA ideal/relaxed vortex equilibria.
3. Higgs spin-0/scalar dynamics, gauge charge, color, chirality, weak isospin, lifetime and couplings are **not tested**.
4. Quark masses are scheme/scale dependent; their reveal is diagnostic only.
5. A convincing next stage requires replacing the screening geometry with PKLSA/finite-core dynamics while keeping this blind/reveal protocol fixed.
"""
    (rev/"REPORT_REVEALED.md").write_text(report,encoding="utf-8")
    write_json(rev/"REVEAL_STATUS.json",{
        "blind_seal_verified":True,
        "historical_quark_check":"COMPLETED",
        "sm_mass_pattern_search":"COMPLETED_EXPLORATORY",
        "higgs_identification":"NOT_TESTED",
        "particle_identification":"NOT_ESTABLISHED"
    })
    return rev
