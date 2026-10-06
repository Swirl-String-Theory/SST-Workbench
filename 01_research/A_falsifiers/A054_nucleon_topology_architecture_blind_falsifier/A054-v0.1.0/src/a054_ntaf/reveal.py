from __future__ import annotations
from pathlib import Path
import json,statistics
from .seal import sha256_file

CONTRASTS=[
 ("TG_unknot_vs_unlinked_unknot","P_B","C0"),
 ("TG_link_effect_fixed_twist_content","P_C","P_A"),
 ("TG_component_knotting_effect","P_C","P_B"),
 ("BOR_unknot_vs_unlinked_unknot","N_B","C0"),
 ("BOR_link_effect_fixed_twist_content","N_C","N_A"),
 ("BOR_component_knotting_effect","N_C","N_B"),
]
METRICS=["median_rel_eq","median_cross_stabilization","median_farfield_anisotropy_r6","median_shape_drift"]

def _sid(m):
    p=m.get("provider_stratum")
    return None if not p else p.get("stratum_id")

def _delta(sa,sb):
    return {k:(None if sa.get(k) is None or sb.get(k) is None else sa[k]-sb[k]) for k in METRICS}

def _envelope(rows):
    env={}
    for k in METRICS:
        vals=[r["delta_A_minus_B"].get(k) for r in rows if r.get("delta_A_minus_B",{}).get(k) is not None]
        if vals:
            env[k]={"min":min(vals),"max":max(vals),"median":statistics.median(vals),
                    "sign_consistent":(min(vals)>=0 or max(vals)<=0)}
    return env

def reveal(campaign:Path):
    seal=json.loads((campaign/"BLIND_SEAL.json").read_text(encoding='utf-8'))
    checks={"manifest_sha256":campaign/"BLIND_MANIFEST.json","results_sha256":campaign/"BLIND_RESULTS.json",
            "analysis_sha256":campaign/"ANALYSIS_BLIND.json","report_sha256":campaign/"REPORT_BLIND.md"}
    for key,p in checks.items():
        if sha256_file(p)!=seal[key]: raise RuntimeError(f"blind seal mismatch: {p.name}")
    pp=campaign/"_private/PRIVATE_MAPPING.json"
    if sha256_file(pp)!=seal["private_mapping_commitment"]: raise RuntimeError("private mapping commitment mismatch")
    priv=json.loads(pp.read_text(encoding='utf-8')); ana=json.loads((campaign/"ANALYSIS_BLIND.json").read_text(encoding='utf-8'))

    revealed=[]; bybase={}
    for aid,s in ana["summaries"].items():
        m=priv["mapping"][aid]
        rec={"anonymous_id":aid,**m,"blind_summary":s}; revealed.append(rec)
        bybase.setdefault(m["semantic_id"],[]).append((aid,m,s))

    contrasts=[]
    for name,A,B in CONTRASTS:
        aa=bybase.get(A,[]); bb=bybase.get(B,[])
        if not aa or not bb:
            contrasts.append({"name":name,"status":"NOT_EVALUABLE_MISSING_GENERATED_OR_PKLSA_CASE","strata":[]}); continue
        mapA={_sid(m):(aid,m,s) for aid,m,s in aa}; mapB={_sid(m):(aid,m,s) for aid,m,s in bb}
        # Common generated control may be compared against every provider stratum on the other side.
        if set(mapA)=={None} and set(mapB)=={None}: strata=[None]
        elif set(mapA)=={None}: strata=sorted(k for k in mapB if k is not None)
        elif set(mapB)=={None}: strata=sorted(k for k in mapA if k is not None)
        else: strata=sorted((set(mapA)&set(mapB))-{None})
        rows=[]
        for st in strata:
            ra=mapA.get(st) or mapA.get(None); rb=mapB.get(st) or mapB.get(None)
            if ra is None or rb is None: continue
            sa,sb=ra[2],rb[2]
            if sa["status"]=="INCONCLUSIVE_NUMERICAL" or sb["status"]=="INCONCLUSIVE_NUMERICAL":
                rows.append({"provider_stratum":st,"status":"INCONCLUSIVE_NUMERICAL","A_status":sa["status"],"B_status":sb["status"]}); continue
            rows.append({"provider_stratum":st,"status":"EVALUATED","A_status":sa["status"],"B_status":sb["status"],
                         "delta_A_minus_B":_delta(sa,sb)})
        good=[r for r in rows if r["status"]=="EVALUATED"]
        if not rows: status="NOT_EVALUABLE_NO_MATCHED_PROVIDER_STRATUM"
        elif not good: status="INCONCLUSIVE_NUMERICAL"
        elif len(good)<len(rows): status="EVALUATED_WITH_INCONCLUSIVE_STRATA"
        else: status="EVALUATED"
        contrasts.append({"name":name,"status":status,"A":A,"B":B,"strata":rows,"provider_envelope":_envelope(good)})

    out={"schema":"A054-REVEAL-1.0","scientific_ready":ana["scientific_ready"],"cases":revealed,"contrasts":contrasts,
         "provider_policy":"Every E011 provider anchor participates through the Cartesian anchor envelope; 6_1-sensitive conclusions remain provider-conditional unless they survive that envelope.",
         "interpretation_guard":"Contrasts test architecture/component effects under this filament operator; they do not assign nucleon identity or fit masses."}
    (campaign/"REVEALED_RESULTS.json").write_text(json.dumps(out,indent=2),encoding='utf-8')
    lines=["# A054 v0.1.0 — REVEALED report","","Blind observables were sealed before identity attachment.",""]
    for c in contrasts:
        lines.append(f"- **{c['name']}**: {c['status']}")
        if c.get("provider_envelope"): lines.append(f"  - provider envelope: `{c['provider_envelope']}`")
    (campaign/"REPORT_REVEALED.md").write_text("\n".join(lines)+"\n",encoding='utf-8')
    return out
