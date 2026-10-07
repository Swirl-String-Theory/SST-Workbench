from __future__ import annotations
from pathlib import Path
import json,statistics
from .reveal import run_reveal
from .blind import verify_seal
from .util import load_json,write_json

def _mean_bool(xs,key):
    vals=[bool(x.get(key)) for x in xs]
    return None if not vals else sum(vals)/len(vals)
def _median(xs):
    ys=[float(x) for x in xs if isinstance(x,(int,float))]
    return None if not ys else statistics.median(ys)

def _single_counterpair_by_topology(out:Path):
    mapping=load_json(out/"PRIVATE_REVEAL_DO_NOT_INCLUDE_IN_BLIND"/"mapping.json")
    d=out/"BLIND"/"dynamics"; ans={}
    for p in d.glob("*.json"):
        obj=load_json(p); cid=obj["case"]["case_id"]; top=mapping[cid]
        dyn=obj.get("dynamic",{})
        providers=dyn.get("providers",[])
        cells=[]
        for pr in providers:
            for mr in pr.get("mode_reports",[]):
                cells += [{"provider_group":pr.get("provider_group"),"mode_m":mr.get("mode_m"),
                           "N":lv.get("N"),"available":lv.get("status")=="OSCILLATORY_PAIR_AVAILABLE"}
                          for lv in mr.get("levels",[])]
                cells += [{"provider_group":pr.get("provider_group"),"mode_m":x.get("mode_m"),
                           "N":x.get("N"),"available":False,"status":x.get("status")}
                          for x in pr.get("mode_cell_failures",[])]
        ans[top]={"cells":cells,"any_counterpropagating_pair":any(x.get("available") for x in cells),
                  "available_count":sum(bool(x.get("available")) for x in cells),"cell_count":len(cells),
                  "particle_promotion_qualified":bool(dyn.get("particle_promotion_qualified",False))}
    return ans

def run_reveal_v3(root:Path,out:Path):
    ok,seal=verify_seal(out)
    if not ok: raise RuntimeError(f"A055 blind seal failed: {seal}")
    # Existing single-knot reveal (including historical 5_2/6_1 + SM pattern boundary).
    run_reveal(root,out)
    comp=load_json(out/"BLIND"/"COMPOUND_A054"/"COMPOUND_FEATURES_BLIND.json")
    priv=load_json(out/"PRIVATE_REVEAL_DO_NOT_INCLUDE_IN_BLIND"/"COMPOUND_A054"/"PRIVATE_MAPPING.json")
    by={(r["anonymous_id"],r["sector"]):r for r in comp["rows"]}
    cases=[]
    for aid,m in priv["mapping"].items():
        if aid not in {x["anonymous_id"] for x in comp["candidate_summaries"]}: continue
        labels=m.get("components") or []
        sectors=[]
        for sec in ("Q0","Q1","Q2","Q3"):
            r=dict(by.get((aid,sec),{}))
            if not r: continue
            if sec=="Q0":
                r["opposed_slot"]=None; r["opposed_knot"]=None
            else:
                j=int(sec[1])-1
                r["opposed_slot"]=j
                r["opposed_knot"]=labels[j] if j<len(labels) else None
            sectors.append(r)
        cases.append({
          "anonymous_id":aid,"architecture_code":m.get("architecture_code"),
          "architecture":m.get("architecture"),"twist_bits":m.get("twist_bits"),
          "components":labels,"n_5_2":m.get("n_5_2"),"n_6_1":m.get("n_6_1"),
          "historical_composition_class":m.get("historical_composition_class"),
          "provider_stratum":m.get("provider_stratum"),"sectors":sectors})

    arch={}
    for code in ("U","G","B"):
        rr=[s for c in cases if c["architecture_code"]==code for s in c["sectors"]]
        q0=[x for x in rr if x["sector"]=="Q0"]; opp=[x for x in rr if x["sector"] in ("Q1","Q2","Q3")]
        arch[code]={
          "sector_rows":len(rr),
          "q0_counterpropagating_symmetric_fraction":_mean_bool(q0,"counterpropagating_pair_symmetric"),
          "opposed_counterpropagating_symmetric_fraction":_mean_bool(opp,"counterpropagating_pair_symmetric"),
          "q0_kelvin_counterpropagating_symmetric_fraction":_mean_bool(q0,"kelvin_counterpropagating_pair_symmetric"),
          "opposed_kelvin_counterpropagating_symmetric_fraction":_mean_bool(opp,"kelvin_counterpropagating_pair_symmetric"),
          "opposed_certified_fraction":None if not opp else sum(str(x.get("status","")).startswith("CERTIFIED_") for x in opp)/len(opp),
          "opposed_rpo_fraction":_mean_bool(opp,"rpo_accepted"),
          "opposed_floquet_evaluated_fraction":_mean_bool(opp,"floquet_evaluated"),
          "median_opposed_normalized_growth":_median([x.get("normalized_growth") for x in opp]),
        }

    # Identity of the opposed component, separated by architecture.
    identity={}
    for code in ("G","B","U"):
        rows=[s for c in cases if c["architecture_code"]==code for s in c["sectors"] if s.get("opposed_knot") in ("5_2","6_1")]
        identity[code]={}
        for knot in ("5_2","6_1"):
            q=[x for x in rows if x.get("opposed_knot")==knot]
            identity[code][knot]={
              "n":len(q),
              "counterpropagating_symmetric_fraction":_mean_bool(q,"counterpropagating_pair_symmetric"),
              "kelvin_counterpropagating_symmetric_fraction":_mean_bool(q,"kelvin_counterpropagating_pair_symmetric"),
              "certified_fraction":None if not q else sum(str(x.get("status","")).startswith("CERTIFIED_") for x in q)/len(q),
              "median_normalized_growth":_median([x.get("normalized_growth") for x in q]),
              "rpo_fraction":_mean_bool(q,"rpo_accepted"),
            }

    # Reveal-only working baryon hypotheses. They are reports, never BLIND selection rules.
    proton=[(c,s) for c in cases if c["architecture_code"]=="G" and c.get("n_6_1")==1
            for s in c["sectors"] if s.get("opposed_knot")=="6_1"]
    neutron=[(c,s) for c in cases if c["architecture_code"]=="B" and c.get("n_6_1")==2
             for s in c["sectors"] if s.get("opposed_knot")=="6_1"]
    def hyp(rows):
        ss=[s for _,s in rows]
        return {"n":len(ss),
          "counterpropagating_symmetric_fraction":_mean_bool(ss,"counterpropagating_pair_symmetric"),
          "kelvin_counterpropagating_symmetric_fraction":_mean_bool(ss,"kelvin_counterpropagating_pair_symmetric"),
          "certified_fraction":None if not ss else sum(str(x.get("status","")).startswith("CERTIFIED_") for x in ss)/len(ss),
          "rpo_fraction":_mean_bool(ss,"rpo_accepted"),
          "floquet_evaluated_fraction":_mean_bool(ss,"floquet_evaluated"),
          "median_normalized_growth":_median([x.get("normalized_growth") for x in ss])}

    single=_single_counterpair_by_topology(out)
    emergence={
      "5_2_single_control":single.get("5_2"),
      "6_1_single_control":single.get("6_1"),
      "proton_like_compound":hyp(proton),
      "neutron_like_compound":hyp(neutron),
      "interpretation":"Descriptive bridge only. A compound oscillatory pair is not a proton/neutron identification."
    }
    result={
      "schema":"A055-COMPOUND-REVEAL-3.0","a055_blind_seal_verified":True,
      "a054_source_campaign":comp["source_campaign"],
      "architecture_contrasts":arch,"opposed_knot_identity":identity,
      "working_hypotheses":{
        "proton_like":"Triple-Gear G with composition 5_2+5_2+6_1 and the 6_1 component opposed",
        "neutron_like":"Borromean B with composition 5_2+6_1+6_1 and a 6_1 component opposed",
        "status":"REVEAL_ONLY_NOT_A_SELECTION_RULE",
        "proton_like_metrics":hyp(proton),"neutron_like_metrics":hyp(neutron)},
      "single_vs_compound_emergence":emergence,
      "interpretation_guard":"A054 owns multi-component dynamics. A055 v0.3.0 tests whether linked compound architecture creates categorical oscillatory/RPO/Floquet structure absent from single-knot controls; raw spectra from different projected bases are not pooled."}
    rev=out/"REVEALED"; write_json(rev/"COMPOUND_BRIDGE_REVEALED.json",result)
    lines=["# A055 v0.3.0 — compound bridge reveal","",
      "A054 v0.2.x provides the authoritative three-component finite-core dynamics.",
      "A055 supplies the single-knot control branch and blind/reveal bridge.","",
      "## Architecture contrasts"]
    for code,x in arch.items():
        lines.append(f"- {code}: Q0 CP={x['q0_counterpropagating_symmetric_fraction']}, "
                     f"2+1 CP={x['opposed_counterpropagating_symmetric_fraction']}, "
                     f"2+1 Kelvin-CP={x['opposed_kelvin_counterpropagating_symmetric_fraction']}, "
                     f"RPO={x['opposed_rpo_fraction']}")
    lines += ["","## Working historical hypotheses (reveal-only)",
              f"- proton-like G(5_2,5_2,6_1), 6_1 opposed: {hyp(proton)}",
              f"- neutron-like B(5_2,6_1,6_1), 6_1 opposed: {hyp(neutron)}",
              "","No particle identity is established by this bridge alone."]
    (rev/"REPORT_COMPOUND_BRIDGE_REVEALED.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return result
