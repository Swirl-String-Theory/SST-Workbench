from __future__ import annotations
from pathlib import Path
import math, random, csv, gzip, hashlib, bisect
from .util import *
from .blind import verify_seal
from .features import FEATURE_REGISTRY, PRIMARY_FEATURES, pool_rows


def _feature_value(r, feat):
    return abs(float(r[feat]))


def _target_shape(masses):
    lm=sorted(math.log(float(m)) for m in masses)
    mm=sum(lm)/3.0
    return (lm[0]-mm,lm[1]-mm,lm[2]-mm),mm,lm


def _eligible_rows(rows, feat, pool, positive_floor):
    rr=pool_rows(rows,pool)
    out=[]
    for r in rr:
        if not r.get(feat+"_qualified",False):
            continue
        v=_feature_value(r,feat)
        if FEATURE_REGISTRY[feat].get("requires_positive_for_ratio",False) and v<=positive_floor:
            continue
        out.append(r)
    return out


def _build_triplet_cache(rows, feat):
    ordered=sorted((math.log(_feature_value(r,feat)),_feature_value(r,feat),r["case_id"]) for r in rows)
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
    tm,tmean,_=_target_shape(masses)
    best_err2=float("inf"); best=None
    t0,t1,t2=tm
    for c0,c1,c2,xmean,ca,cb,cc,v0,v1,v2 in cache:
        d0=c0-t0; d1=c1-t1; d2=c2-t2
        err2=(d0*d0+d1*d1+d2*d2)/3.0
        if err2 < best_err2:
            best_err2=err2
            best=(xmean,ca,cb,cc,v0,v1,v2)
    xmean,ca,cb,cc,v0,v1,v2=best
    return {"log_rms":math.sqrt(max(0.0,best_err2)),"scale":math.exp(tmean-xmean),
            "case_ids":[ca,cb,cc],"feature_values":[v0,v1,v2]}


def _null_line(cache, span):
    # Target centered log-vector for [0, t*span, span]: p*t + q.
    p=(-span/3.0, 2.0*span/3.0, -span/3.0)
    q=(-span/3.0, -span/3.0, 2.0*span/3.0)
    a=sum(x*x for x in p)/3.0
    lines=[]
    for c0,c1,c2,*_ in cache:
        c=(c0,c1,c2)
        b=(-2.0/3.0)*sum(p[i]*(c[i]-q[i]) for i in range(3))
        intercept=(1.0/3.0)*sum((c[i]-q[i])**2 for i in range(3))
        lines.append((b,intercept))
    return a,lines


def _lower_envelope(lines):
    # Minimum of y=m*x+b for x increasing.  Sort slopes descending so the
    # active minimum slopes decrease as x increases.
    by_slope={}
    for m,b in lines:
        key=m
        old=by_slope.get(key)
        if old is None or b<old[1]:
            by_slope[key]=(m,b)
    ordered=sorted(by_slope.values(), key=lambda z:z[0], reverse=True)
    hull=[]; starts=[]
    for m,b in ordered:
        if not hull:
            hull.append((m,b)); starts.append(float("-inf")); continue
        while hull:
            pm,pb=hull[-1]
            if abs(pm-m)<1e-18:
                x=float("inf")
            else:
                x=(b-pb)/(pm-m)
            if x<=starts[-1]:
                hull.pop(); starts.pop()
                if not hull: break
            else:
                break
        if not hull:
            hull.append((m,b)); starts.append(float("-inf"))
        else:
            pm,pb=hull[-1]
            x=(b-pb)/(pm-m)
            hull.append((m,b)); starts.append(x)
    return hull,starts


def _envelope_value(hull, starts, x):
    i=bisect.bisect_right(starts,x)-1
    if i<0: i=0
    m,b=hull[i]
    return m*x+b


def _quantiles(values, qs=(0.0,0.01,0.05,0.5,0.95,0.99,1.0)):
    s=sorted(values); n=len(s)
    out={}
    for q in qs:
        if n==1: v=s[0]
        else:
            pos=q*(n-1); lo=int(math.floor(pos)); hi=int(math.ceil(pos)); f=pos-lo
            v=s[lo]*(1-f)+s[hi]*f
        out[f"q{q:.2f}"]=v
    return out


def _null_distribution(cache, masses, t_values):
    _,_,lm=_target_shape(masses)
    span=lm[2]-lm[0]
    a,lines=_null_line(cache,span)
    hull,starts=_lower_envelope(lines)
    vals=[]
    for t in t_values:
        e2=a*t*t+_envelope_value(hull,starts,t)
        vals.append(math.sqrt(max(0.0,e2)))
    return vals,{"candidate_triplets":len(cache),"envelope_lines":len(hull),"target_log_span":span}


def _historical_check(rows, mapping, blind):
    inv={v:k for k,v in mapping.items()}
    a=inv["5_2"]; b=inv["6_1"]
    raw=load_json(blind/"PAIRS_KNOTS_RAW.json")
    qualified=load_json(blind/"PAIRS_KNOTS_QUALIFIED.json")
    raw_target=next(p for p in raw if {p["case_a"],p["case_b"]}=={a,b})
    raw_rank=1+next(i for i,p in enumerate(raw) if {p["case_a"],p["case_b"]}=={a,b})
    q_idx=next((i for i,p in enumerate(qualified) if {p["case_a"],p["case_b"]}=={a,b}),None)
    by_top={mapping[r["case_id"]]:r for r in rows}
    per_top={}
    for top in ("5_2","6_1"):
        r=by_top[top]
        per_top[top]={f:{"qualified":bool(r.get(f+"_qualified",False)),
                         "resolution_rel_delta":r.get(f+"_resolution_rel_delta"),
                         "embedding_cv":r.get(f+"_cv")} for f in ["bend_energy","abs_neumann_energy","min_distance","abs_writhe"]}
    result={
        "u_candidate":"5_2","d_candidate":"6_1",
        "raw_knot_space":{"distance":raw_target["distance"],"rank":raw_rank,
                          "pair_count":len(raw),"rank_fraction":raw_rank/len(raw)},
        "qualification":per_top,
        "qualified_knot_space":None,
        "interpretation":"Raw rank is diagnostic. Scientific promotion requires both topologies to qualify in all preregistered knot-space features."
    }
    if q_idx is not None:
        qp=qualified[q_idx]
        result["qualified_knot_space"]={"status":"QUALIFIED","distance":qp["distance"],
                                        "rank":q_idx+1,"pair_count":len(qualified),
                                        "rank_fraction":(q_idx+1)/len(qualified)}
    else:
        result["qualified_knot_space"]={"status":"NOT_QUALIFIED","pair_count":len(qualified)}
    return result


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

    historical=_historical_check(rows,mapping,blind)
    write_json(rev/"HISTORICAL_5_2_6_1_CHECK.json",historical)

    cfg=load_json(blind/"config_frozen.json")
    masses=sm["masses"]
    positive_floor=float(cfg.get("ratio_positive_floor",1e-12))
    nnull=int(cfg.get("null_targets",10000))
    base_seed=int(cfg.get("null_seed",5501011))
    fit={}
    null_gz=rev/"SM_NULL_DISTRIBUTIONS.csv.gz"
    invalid_domain_count=0; valid_search_count=0
    group_family_nulls={}
    global_familywise=None
    with gzip.open(null_gz,"wt",newline="",encoding="utf-8") as gz:
        nw=csv.DictWriter(gz,fieldnames=["group","feature","pool","trial","t_log_position","best_log_rms"])
        nw.writeheader()
        for gi,(group,names) in enumerate(sm["groups"].items()):
            ms=[float(masses[n]) for n in names]
            rng=random.Random(base_seed+gi*100003)
            t_values=[rng.random() for _ in range(nnull)]
            t_sha=hashlib.sha256(canonical(t_values)).hexdigest()
            fit[group]={"particle_names":names,"masses_MeV":ms,"null_trials":nnull,
                        "null_t_sha256":t_sha,"features":{}}
            search_nulls={}; search_best={}
            for feat in PRIMARY_FEATURES:
                feat_out={}
                allowed=set(FEATURE_REGISTRY[feat]["ratio_pools"])
                for pool in ("knots","links","all"):
                    if pool not in allowed:
                        invalid_domain_count+=1
                        if pool == "knots":
                            reason=FEATURE_REGISTRY[feat].get("knot_forbidden_reason","pool not preregistered for this feature")
                        elif pool == "all":
                            reason=FEATURE_REGISTRY[feat].get("mixed_pool_forbidden_reason","pool not preregistered for this feature")
                        else:
                            reason="pool not preregistered for this feature"
                        feat_out[pool]={"status":"INVALID_FEATURE_DOMAIN","reason":reason}
                        continue
                    eligible=_eligible_rows(rows,feat,pool,positive_floor)
                    if len(eligible)<3:
                        feat_out[pool]={"status":"INSUFFICIENT_QUALIFIED_CASES","eligible_case_count":len(eligible)}
                        continue
                    cache=_build_triplet_cache(eligible,feat)
                    best=_best_triplet_cached(cache,ms)
                    null_vals,envmeta=_null_distribution(cache,ms,t_values)
                    p_single=(1+sum(x<=best["log_rms"] for x in null_vals))/(1+len(null_vals))
                    best["status"]="VALID"
                    best["eligible_case_count"]=len(eligible)
                    best["candidate_triplet_count"]=len(cache)
                    best["look_elsewhere_null_fraction_within_feature_pool"]=p_single
                    best["null_summary"]={"trials":len(null_vals),**_quantiles(null_vals),**envmeta}
                    best["topologies"]=[mapping[c] for c in best["case_ids"]]
                    feat_out[pool]=best; valid_search_count+=1
                    search_nulls[(feat,pool)]=null_vals
                    search_best[(feat,pool)]=best
                    for ti,(t,e) in enumerate(zip(t_values,null_vals)):
                        nw.writerow({"group":group,"feature":feat,"pool":pool,"trial":ti,
                                     "t_log_position":f"{t:.17g}","best_log_rms":f"{e:.17g}"})
                fit[group]["features"][feat]=feat_out

            def familywise(keys, label):
                keys=[k for k in keys if k in search_nulls]
                if not keys:
                    return {"status":"NO_VALID_SEARCHES"},None
                obs_key=min(keys,key=lambda k:search_best[k]["log_rms"])
                obs=search_best[obs_key]["log_rms"]
                vals=[min(search_nulls[k][i] for k in keys) for i in range(nnull)]
                pval=(1+sum(x<=obs for x in vals))/(1+len(vals))
                result={"status":"VALID","search_count":len(keys),"best_feature":obs_key[0],
                        "best_pool":obs_key[1],"best_topologies":search_best[obs_key]["topologies"],
                        "observed_best_log_rms":obs,"familywise_null_fraction":pval,
                        "null_summary":{"trials":len(vals),**_quantiles(vals)}}
                for ti,(t,e) in enumerate(zip(t_values,vals)):
                    nw.writerow({"group":group,"feature":label,"pool":"familywise","trial":ti,
                                 "t_log_position":f"{t:.17g}","best_log_rms":f"{e:.17g}"})
                return result,vals

            common_keys=[(f,"all") for f in PRIMARY_FEATURES]
            fam_common,common_vals=familywise(common_keys,"__FAMILYWISE_COMMON_ALL__")
            fam_all,all_vals=familywise(list(search_nulls.keys()),"__FAMILYWISE_ALL_VALID_DOMAINS__")
            fit[group]["familywise_common_all"]=fam_common
            fit[group]["familywise_all_valid_domains"]=fam_all
            if all_vals is not None:
                group_family_nulls[group]={"observed":fam_all["observed_best_log_rms"],"null":all_vals}

        # Global look-elsewhere layer across all preregistered SM triplet groups,
        # all valid feature domains and all topology triplets.
        if group_family_nulls:
            groups=list(group_family_nulls)
            observed=min(group_family_nulls[g]["observed"] for g in groups)
            global_null=[min(group_family_nulls[g]["null"][i] for g in groups) for i in range(nnull)]
            p_global=(1+sum(x<=observed for x in global_null))/(1+len(global_null))
            best_group=min(groups,key=lambda g:group_family_nulls[g]["observed"])
            global_familywise={"status":"VALID","group_count":len(groups),"best_group":best_group,
                               "observed_best_log_rms":observed,"global_null_fraction":p_global,
                               "null_summary":{"trials":len(global_null),**_quantiles(global_null)}}
            for i,e in enumerate(global_null):
                nw.writerow({"group":"__GLOBAL_SM_GROUPS__","feature":"__FAMILYWISE_ALL__",
                             "pool":"familywise","trial":i,"t_log_position":"",
                             "best_log_rms":f"{e:.17g}"})

    fit["_metadata"]={"null_distribution_file":null_gz.name,"null_trials_per_valid_search":nnull,
                      "invalid_feature_domain_entries":invalid_domain_count,"valid_searches":valid_search_count,
                      "ratio_positive_floor_is_exclusion_not_replacement":positive_floor,
                      "global_familywise":global_familywise}
    write_json(rev/"SM_RATIO_SEARCH.json",fit)

    bestlines=[]
    for group,g in fit.items():
        if group.startswith("_"): continue
        candidates=[]
        for feat,fd in g["features"].items():
            x=fd.get("all")
            if x and x.get("status")=="VALID": candidates.append((x["log_rms"],feat,x))
        if candidates:
            candidates.sort(key=lambda q:q[0]); e,feat,x=candidates[0]
            bestlines.append(f"- **{group}**: best valid common all-atlas proxy `{feat}` -> {x['topologies']}; log-RMS={e:.6g}; within-search null={x['look_elsewhere_null_fraction_within_feature_pool']:.6g}; familywise common-all={g['familywise_common_all'].get('familywise_null_fraction',float('nan')):.6g}; eligible cases={x['eligible_case_count']}.")
        else:
            bestlines.append(f"- **{group}**: no valid common all-atlas triplet survived feature qualification.")

    global_line=""
    gf=fit.get("_metadata",{}).get("global_familywise")
    if gf and gf.get("status")=="VALID":
        global_line=(f"\nAcross all preregistered SM groups, valid feature domains and topology triplets, "
                     f"the global look-elsewhere null fraction is **{gf['global_null_fraction']:.6g}** "
                     f"(best group: `{gf['best_group']}`).\n")

    qhist=historical["qualified_knot_space"]
    if qhist["status"]=="QUALIFIED":
        histline=(f"Qualified knot-space rank: **{qhist['rank']}/{qhist['pair_count']}** "
                  f"(fraction {qhist['rank_fraction']:.6f}), distance {qhist['distance']:.9g}.")
    else:
        histline="The historical pair did **not** jointly pass all v0.1.1 knot-space feature gates; no qualified rank is assigned."
    raw=historical["raw_knot_space"]
    report=f"""# A055 v0.1.1 — REVEALED report

Blind seal verified: `{seal}`.

## Historical VAM/SST quark check

Historical mapping: `u -> 5_2`, `d -> 6_1` (twist-knot pair).

- Raw diagnostic knot-space rank: **{raw['rank']}/{raw['pair_count']}** (fraction {raw['rank_fraction']:.6f}).
- Raw diagnostic distance: **{raw['distance']:.9g}**.
- {histline}

Unlike v0.1.0, the scientific rank is withheld if either topology fails the preregistered resolution/CV gates.

## Exploratory SM mass-pattern reveal

{chr(10).join(bestlines)}
{global_line}
Each valid search uses **{nnull}** null targets at the same total log-mass span.  The intermediate log-position is randomized and the complete eligible triplet search is repeated analytically through the exact lower envelope of candidate error quadratics.  Full null values are stored in `{null_gz.name}`.

## v0.1.1 domain corrections

- `linking_strength` is **links only**. Knot values are never replaced by `1e-6` or any other artificial floor.
- `abs_writhe` is not used in mixed knot/link fits.
- `contact_ratio` is diagnostic only because it scales explicitly with segment resolution.
- `min_distance` after common length normalization replaces it as the contact observable.
- Zero/non-positive values required by a logarithmic ratio fit are excluded, not shifted.

## Mandatory interpretation limits

1. v0.1.1 does **not** identify a knot/link with an SM particle.
2. PD-derived embeddings are presentation ensembles, not PKLSA ideal/relaxed vortex equilibria.
3. Higgs spin-0/scalar dynamics, gauge charge, color, chirality, weak isospin, lifetime and couplings are **not tested**.
4. Quark masses are scheme/scale dependent; their reveal remains diagnostic only.
5. Promotion to v0.2.0 requires PKLSA/finite-core dynamical observables under the same blind/domain/convergence protocol.
"""
    (rev/"REPORT_REVEALED.md").write_text(report,encoding="utf-8")
    write_json(rev/"REVEAL_STATUS.json",{
        "blind_seal_verified":True,"historical_quark_check":"COMPLETED_WITH_QUALIFICATION_GATE",
        "sm_mass_pattern_search":"COMPLETED_EXPLORATORY_WITH_DOMAIN_MASKS_AND_NULLS",
        "null_trials_per_valid_search":nnull,
        "feature_domain_masks_enforced":True,"contact_ratio_primary_use":"DISABLED",
        "higgs_identification":"NOT_TESTED","particle_identification":"NOT_ESTABLISHED"
    })
    return rev
