from __future__ import annotations
from pathlib import Path
import math, itertools, random, csv
from .util import *
from .blind import verify_seal

OBSERVABLES=["ropelength_hat","omega_m1_hat","omega_m2_hat","omega_m3_hat"]

def _positive(r,f):
    v=r.get(f)
    return isinstance(v,(int,float)) and math.isfinite(v) and v>0
def _triplet_error(xs,ms):
    lx=sorted(math.log(x) for x in xs); lm=sorted(math.log(m) for m in ms)
    shift=sum(m-x for m,x in zip(lm,lx))/3
    res=[x+shift-m for x,m in zip(lx,lm)]
    return math.sqrt(sum(x*x for x in res)/3),math.exp(shift)
def _best(rows,feat,masses):
    xs=[r for r in rows if r["kind"]=="knot" and r.get("particle_promotion_qualified") and _positive(r,feat)]
    best=None
    for t in itertools.combinations(xs,3):
        e,s=_triplet_error([r[feat] for r in t],masses)
        if best is None or e<best["log_rms"]:
            best={"log_rms":e,"scale":s,"case_ids":[r["case_id"] for r in t],"feature_values":[r[feat] for r in t]}
    return best
def _empirical_p(obs,null):
    return (1+sum(x<=obs for x in null))/(len(null)+1)

def run_reveal(root:Path,out:Path):
    ok,seal=verify_seal(out)
    if not ok: raise RuntimeError(f"Blind seal failed: {seal}")
    blind=out/"BLIND"; priv=out/"PRIVATE_REVEAL_DO_NOT_INCLUDE_IN_BLIND"; rev=out/"REVEALED"; rev.mkdir(exist_ok=True)
    mapping=load_json(priv/"mapping.json"); rows=load_json(blind/"FEATURES.json")
    for r in rows:r["topology_id"]=mapping[r["case_id"]]
    write_json(rev/"FEATURES_REVEALED.json",rows)
    hist=load_json(root/"reveal"/"historical_hypotheses.json"); sm=load_json(root/"reveal"/"sm_reference_2026.json")
    write_json(rev/"HISTORICAL_HYPOTHESES_SNAPSHOT.json",hist); write_json(rev/"SM_REFERENCE_SNAPSHOT.json",sm)
    by={r["topology_id"]:r for r in rows}
    a,b=by.get("5_2"),by.get("6_1")
    histres={"mapping":{"u":"5_2","d":"6_1"}}
    if a and b and a.get("particle_promotion_qualified") and b.get("particle_promotion_qualified"):
        feats=[f for f in ["ropelength_hat","omega_m1_hat","omega_m2_hat","omega_m3_hat"] if _positive(a,f) and _positive(b,f)]
        if len(feats)>=2:
            q=[r for r in rows if r["kind"]=="knot" and r.get("particle_promotion_qualified") and all(_positive(r,f) for f in feats)]
            z={}
            for f in feats:
                vals=[math.log(r[f]) for r in q]; m=sum(vals)/len(vals)
                s=(sum((x-m)**2 for x in vals)/max(1,len(vals)-1))**.5
                z[f]={r["case_id"]:(math.log(r[f])-m)/(s or 1) for r in q}
            pairs=[]
            for x,y in itertools.combinations(q,2):
                d=math.sqrt(sum((z[f][x["case_id"]]-z[f][y["case_id"]])**2 for f in feats))
                pairs.append((d,{x["topology_id"],y["topology_id"]}))
            pairs.sort(key=lambda x:x[0])
            target=next((x for x in pairs if x[1]=={"5_2","6_1"}),None)
            histres.update({"status":"DYNAMIC_PAIR_RANKED","features":feats,
                            "rank":1+next(i for i,x in enumerate(pairs) if x[1]=={"5_2","6_1"}),
                            "pair_count":len(pairs),"distance":target[0] if target else None})
        else: histres["status"]="INSUFFICIENT_COMMON_DYNAMIC_FEATURES"
    else:
        histres["status"]="UNRESOLVED_DYNAMIC_QUALIFICATION"
        histres["5_2_status"]=a.get("dynamic_status") if a else None
        histres["6_1_status"]=b.get("dynamic_status") if b else None
    write_json(rev/"HISTORICAL_5_2_6_1_DYNAMIC_CHECK.json",histres)

    cfg=load_json(blind/"config_frozen.json"); rng=random.Random(int(cfg["null_seed"])); nnull=int(cfg["null_targets"])
    masses=sm["masses"]; groups=sm["groups"]; results={}
    group_p=[]
    for g,names in groups.items():
        ms=[masses[n] for n in names]; lo=min(ms); hi=max(ms)
        gres={"particle_names":names,"masses_MeV":ms,"observables":{}}
        pvals=[]
        for feat in OBSERVABLES:
            best=_best(rows,feat,ms)
            if best is None:
                gres["observables"][feat]={"status":"NO_QUALIFIED_TRIPLET"}; continue
            null=[]
            for _ in range(nnull):
                mid=lo*math.exp(rng.random()*math.log(hi/lo))
                nb=_best(rows,feat,[lo,mid,hi])
                if nb is not None:null.append(nb["log_rms"])
            p=_empirical_p(best["log_rms"],null) if null else 1.0
            best["topologies"]=[mapping[c] for c in best["case_ids"]]
            best["empirical_p"]=p; best["effect_size_pass"]=best["log_rms"]<=float(cfg["mass_fit_log_rms_max"])
            gres["observables"][feat]=best; pvals.append(p)
        # within-group Bonferroni over preregistered observables (conservative).
        gp=min(1.0,(min(pvals) if pvals else 1.0)*max(1,len(pvals)))
        gres["familywise_p_bonferroni"]=gp; results[g]=gres; group_p.append(gp)
    global_p=min(1.0,(min(group_p) if group_p else 1.0)*max(1,len(group_p)))
    write_json(rev/"SM_DYNAMIC_MASS_PATTERN_SEARCH.json",results)
    write_json(rev/"GLOBAL_LOOK_ELSEWHERE.json",{"method":"hierarchical Bonferroni over preregistered observables then SM groups",
        "global_p":global_p,"group_familywise_p":{g:results[g]["familywise_p_bonferroni"] for g in results}})
    (rev/"REPORT_REVEALED.md").write_text(f"""# A055 v0.2.1 — REVEALED report

Blind seal: `{seal}`

## Historical quark hypothesis
Status: **{histres['status']}**

## SM/Higgs mass-pattern layer
Global look-elsewhere corrected p-value: **{global_p:.6g}**.

Only particle-promotion-qualified **knots** enter the v0.2.1 dynamic mass-pattern search.
Links are excluded because the authoritative C006/E012 contract is not a multi-component-link dynamics solver.
A W/Z/H mass-ratio match is therefore only a mass-pattern diagnostic and does not establish a scalar Higgs identity.

## Interpretation boundary
A055 v0.2.1 can promote a knot only if source/provider qualification, Kelvin branch convergence, RPO conditioning, cross-provider agreement, and the preregistered true-Floquet gate all pass. It does not infer electric charge, color, weak isospin, or Standard-Model identity from a mass ratio alone.
""",encoding="utf-8")
    return rev
