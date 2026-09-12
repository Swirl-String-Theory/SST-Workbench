from __future__ import annotations
import argparse, json, math
from collections import defaultdict
from pathlib import Path
import numpy as np
from .config import load_config
from .util import read_json, write_json, sha256_file


def _odd(a,b): return abs(a+b)/max(abs(a)+abs(b),1e-15)
def _even(a,b): return abs(a-b)/max(abs(a)+abs(b),1e-15)
def _mag(a,b): return abs(abs(a)-abs(b))/max(abs(a)+abs(b),1e-15)
def _corr(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float)
    if len(a)<3 or np.std(a)<1e-15 or np.std(b)<1e-15: return float("nan")
    return float(np.corrcoef(a,b)[0,1])
def _rank(x):
    x=np.asarray(x,float); order=np.argsort(x); r=np.empty(len(x),float); r[order]=np.arange(len(x),dtype=float); return r


def _excitation_parity(A:dict,B:dict,min_signal:float)->dict:
    """Pair A launch (component,c,mode) with B launch (component,-c mod 1,mode)."""
    bd={}
    for e in B.get("excitations",[]):
        key=(int(e["component"]),round(float(e["center"])%1.0,12),int(e["mode"]))
        bd[key]=e
    rows=[]
    for ea in A.get("excitations",[]):
        target=(-float(ea["center"]))%1.0
        # Normalize 1.0 back to 0.0 before rounding.
        if abs(target-1.0)<1e-12: target=0.0
        key=(int(ea["component"]),round(target,12),int(ea["mode"]))
        eb=bd.get(key)
        if eb is None:
            continue
        pa=float(ea["transport_pi"]); pb=float(eb["transport_pi"]); sig=0.5*(abs(pa)+abs(pb))
        ca=float(ea.get("local_chirality_at_center",float("nan"))); cb=float(eb.get("local_chirality_at_center",float("nan")))
        rows.append({"component":key[0],"A_center":float(ea["center"]),"B_center":float(eb["center"]),"mode":key[2],
                     "A_pi":pa,"B_pi":pb,"signal":sig,"transport_odd_residual":_odd(pa,pb),
                     "local_chirality_odd_residual":_odd(ca,cb) if math.isfinite(ca) and math.isfinite(cb) else None})
    significant=[r for r in rows if r["signal"]>=min_signal]
    return {"n_expected":len(A.get("excitations",[])),"n_matched":len(rows),"n_significant":len(significant),
            "transport_odd_residual_max_significant":max((r["transport_odd_residual"] for r in significant),default=0.0),
            "transport_odd_residual_median_significant":float(np.median([r["transport_odd_residual"] for r in significant])) if significant else 0.0,
            "local_chirality_odd_residual_max":max((r["local_chirality_odd_residual"] for r in rows if r["local_chirality_odd_residual"] is not None),default=0.0),
            "rows":rows}

def _spectral_hausdorff(sa,sb):
    if not sa.get("enabled") or not sb.get("enabled"): return None
    a=np.array([complex(r,i) for r,i in sa["eigenvalues"]],complex); b=np.array([complex(r,i) for r,i in sb["eigenvalues"]],complex)
    if len(a)==0 or len(b)==0: return float("inf")
    scale=max(float(np.max(np.abs(a))),float(np.max(np.abs(b))),1e-15)
    da=max(float(np.min(np.abs(z-b))) for z in a); db=max(float(np.min(np.abs(z-a))) for z in b); return max(da,db)/scale


def analyze(config_path:str,outdir:str):
    cfg=load_config(config_path); out=Path(outdir); data=read_json(out/"BLIND_RESULTS.json"); rows=data["results"]
    minsignal=float(cfg.get("min_transport_signal",0.01))
    grouped=defaultdict(dict)
    for r in rows: grouped[(r["pair_id"],r["resolution_requested"],r["core_fraction"])][r["variant"]]=r
    pairs=[]
    for key,ab in sorted(grouped.items()):
        if set(ab)!={"A","B"}: continue
        A,B=ab["A"],ab["B"]; signal=0.5*(abs(A["transport_pi"])+abs(B["transport_pi"])); denom=A["xi_helicity_centerline"]-B["xi_helicity_centerline"]
        excitation_parity=_excitation_parity(A,B,minsignal)
        p={"pair_id":key[0],"resolution_requested":key[1],"resolution_actual_A":A["resolution_actual"],"resolution_actual_B":B["resolution_actual"],"core_fraction":key[2],
           "n_components":A["n_components"],"helicity_odd_residual":_odd(A["xi_helicity_centerline"],B["xi_helicity_centerline"]),
           "gauss_odd_residual":_odd(A["xi_gauss"],B["xi_gauss"]),"transport_odd_residual":_odd(A["transport_pi"],B["transport_pi"]),
           "transport_magnitude_mismatch":_mag(A["transport_pi"],B["transport_pi"]),"transport_signal_abs_mean":signal,
           "centroid_velocity_odd_residual":_odd(A["centroid_velocity"],B["centroid_velocity"]),
           "relative_equilibrium_max":max(A["relative_equilibrium_initial"]["relative_residual"],B["relative_equilibrium_initial"]["relative_residual"]),
           "relative_equilibrium_parity_residual":_even(A["relative_equilibrium_initial"]["relative_residual"],B["relative_equilibrium_initial"]["relative_residual"]),
           "shape_drift_max":max(A["trajectory"]["rigid_shape_residual"],B["trajectory"]["rigid_shape_residual"]),
           "shape_drift_parity_residual":_even(A["trajectory"]["rigid_shape_residual"],B["trajectory"]["rigid_shape_residual"]),
           "trajectory_underresolved":bool(A["trajectory"]["underresolved"] or B["trajectory"]["underresolved"]),
           "trajectory_achieved_cfl_max":max(A["trajectory"]["achieved_cfl"],B["trajectory"]["achieved_cfl"]),
           "trajectory_max_ds_cv":max(A["trajectory"]["max_ds_cv"],B["trajectory"]["max_ds_cv"]),
           "trajectory_max_abs_length_change":max(abs(A["trajectory"]["relative_length_change"]),abs(B["trajectory"]["relative_length_change"])),
           "max_log_norm_growth":max(A["log_norm_growth_max"],B["log_norm_growth_max"]),
           "tangent_fraction_max":max(A["tangent_fraction_mean"],B["tangent_fraction_mean"]),"rigid_fraction_max":max(A["rigid_fraction_mean"],B["rigid_fraction_mean"]),
           "excitation_relative_std":0.5*(A["transport_pi_std_over_excitations"]+B["transport_pi_std_over_excitations"])/max(signal,1e-15),
           "racemic_pair_mean":0.5*(A["transport_pi"]+B["transport_pi"]),"beta_pair_invariant":float((A["transport_pi"]-B["transport_pi"])/denom) if abs(denom)>1e-15 else float("nan"),
           "A_pi":A["transport_pi"],"B_pi":B["transport_pi"],"A_xiH":A["xi_helicity_centerline"],"B_xiH":B["xi_helicity_centerline"],
           "A_gauss":A["xi_gauss"],"B_gauss":B["xi_gauss"],"A_local_corr":A["local_chirality_transport_corr"],"B_local_corr":B["local_chirality_transport_corr"],
           "spectral_hausdorff_relative":_spectral_hausdorff(A["spectrum"],B["spectrum"]),"excitation_parity":excitation_parity}
        pairs.append(p)

    htol=float(cfg.get("helicity_odd_tolerance",0.08)); gtol=float(cfg.get("gauss_odd_tolerance",0.08)); retol=float(cfg.get("relative_equilibrium_tolerance",0.30))
    repar=float(cfg.get("relative_equilibrium_parity_tolerance",0.05)); ptol=float(cfg.get("transport_odd_tolerance",0.20)); mtol=float(cfg.get("transport_magnitude_tolerance",0.20))
    extol=float(cfg.get("max_excitation_relative_std",0.80)); maxcv=float(cfg.get("max_trajectory_ds_cv",0.35)); maxcfl=float(cfg.get("max_achieved_cfl",0.30))
    maxlen=float(cfg.get("max_trajectory_relative_length_change",0.20)); maxshape=float(cfg.get("max_rigid_shape_residual",0.30)); maxlog=float(cfg.get("max_log_norm_growth",2.5))
    maxtan=float(cfg.get("max_tangent_fraction",0.50)); maxrig=float(cfg.get("max_rigid_fraction",0.50)); spectol=float(cfg.get("spectral_parity_tolerance",0.04)); expar=float(cfg.get("excitation_transport_odd_tolerance",0.25))
    statuses=[]
    for p in pairs:
        if p["helicity_odd_residual"]>htol or p["gauss_odd_residual"]>gtol: s="INVALID_PARITY_HELICITY"
        elif p["relative_equilibrium_parity_residual"]>repar: s="INVALID_PARITY_RELATIVE_EQUILIBRIUM"
        elif p["excitation_parity"]["n_matched"]<p["excitation_parity"]["n_expected"] or p["excitation_parity"]["transport_odd_residual_max_significant"]>expar: s="INVALID_EXCITATION_PARITY"
        elif p["spectral_hausdorff_relative"] is not None and p["spectral_hausdorff_relative"]>spectol: s="INVALID_PARITY_SPECTRUM"
        elif p["trajectory_underresolved"] or p["trajectory_achieved_cfl_max"]>maxcfl: s="INVALID_TRAJECTORY_TIMESTEP"
        elif p["trajectory_max_ds_cv"]>maxcv or p["trajectory_max_abs_length_change"]>maxlen: s="INVALID_TRAJECTORY_MESH"
        elif p["relative_equilibrium_max"]>retol: s="INDETERMINATE_NOT_RELATIVE_EQUILIBRIUM"
        elif p["shape_drift_max"]>maxshape: s="INDETERMINATE_SHAPE_DRIFT"
        elif p["tangent_fraction_max"]>maxtan or p["rigid_fraction_max"]>maxrig: s="INDETERMINATE_GAUGE_CONTAMINATION"
        elif p["max_log_norm_growth"]>maxlog: s="INDETERMINATE_AMPLIFICATION_DOMINATED"
        elif p["transport_signal_abs_mean"]<minsignal: s="NULL_NO_DIRECTIONAL_SIGNAL"
        elif p["excitation_relative_std"]>extol: s="INDETERMINATE_LOCALIZATION_SENSITIVE"
        elif p["transport_odd_residual"]<=ptol and p["transport_magnitude_mismatch"]<=mtol: s="PASS_SINGLE_COMPONENT_MIRROR_ODD_TRANSPORT" if p["n_components"]==1 else "PASS_MULTICOMPONENT_MIRROR_ODD_TRANSPORT"
        else: s="FAIL_MIRROR_ODD_TRANSPORT"
        p["status"]=s; statuses.append(s)

    # Independent statistical unit = one source mirror-pair.  Multiple N/core conditions
    # for the same pair are aggregated and are never counted as independent samples.
    src_groups=defaultdict(list)
    for p in pairs: src_groups[p["pair_id"]].append(p)
    source_stats=[]
    for pid,v in sorted(src_groups.items()):
        ax=float(np.median([0.5*(abs(q["A_xiH"])+abs(q["B_xiH"])) for q in v]))
        ap=float(np.median([q["transport_signal_abs_mean"] for q in v]))
        bb=[q["beta_pair_invariant"] for q in v if math.isfinite(q["beta_pair_invariant"])]
        source_stats.append({"pair_id":pid,"median_abs_xiH":ax,"median_abs_transport":ap,"median_beta":float(np.median(bb)) if bb else float("nan"),"n_conditions":len(v)})
    pair_abs_xi=[q["median_abs_xiH"] for q in source_stats]; pair_abs_pi=[q["median_abs_transport"] for q in source_stats]
    pear_mag=_corr(pair_abs_xi,pair_abs_pi); spear_mag=_corr(_rank(pair_abs_xi),_rank(pair_abs_pi))
    betas=[q["median_beta"] for q in source_stats if math.isfinite(q["median_beta"])]

    # Resolution convergence at fixed pair/core.
    resolution_conv=[]; pc=defaultdict(list)
    for p in pairs: pc[(p["pair_id"],p["core_fraction"])].append(p)
    for key,v in pc.items():
        v=sorted(v,key=lambda q:q["resolution_requested"])
        for lo,hi in zip(v[:-1],v[1:]):
            scale=max(0.5*(abs(lo["A_pi"])+abs(hi["A_pi"])),minsignal,1e-15)
            resolution_conv.append({"pair_id":key[0],"core_fraction":key[1],"N_low":lo["resolution_requested"],"N_high":hi["resolution_requested"],
                                    "relative_delta_A_pi":abs(hi["A_pi"]-lo["A_pi"])/scale,"sign_stable_A":bool(np.sign(lo["A_pi"])==np.sign(hi["A_pi"]) or min(abs(lo["A_pi"]),abs(hi["A_pi"]))<minsignal)})
    core_conv=[]; pr=defaultdict(list)
    for p in pairs: pr[(p["pair_id"],p["resolution_requested"])].append(p)
    for key,v in pr.items():
        v=sorted(v,key=lambda q:q["core_fraction"])
        for lo,hi in zip(v[:-1],v[1:]):
            scale=max(0.5*(abs(lo["A_pi"])+abs(hi["A_pi"])),minsignal,1e-15)
            core_conv.append({"pair_id":key[0],"resolution_requested":key[1],"core_low":lo["core_fraction"],"core_high":hi["core_fraction"],
                              "relative_delta_A_pi":abs(hi["A_pi"]-lo["A_pi"])/scale,"sign_stable_A":bool(np.sign(lo["A_pi"])==np.sign(hi["A_pi"]) or min(abs(lo["A_pi"]),abs(hi["A_pi"]))<minsignal)})
    counts={s:statuses.count(s) for s in sorted(set(statuses))}
    report={"format":"SST-CHIRALITY-ANALYSIS-2.0","blindness":{"source_identity_read":False,"mirror_identity_read":False,"private_manifest_read":False,"private_mapping_present_in_output":False},
            "thresholds":{"helicity_odd_tolerance":htol,"gauss_odd_tolerance":gtol,"relative_equilibrium_tolerance":retol,"relative_equilibrium_parity_tolerance":repar,
                          "transport_odd_tolerance":ptol,"transport_magnitude_tolerance":mtol,"min_transport_signal":minsignal,"max_excitation_relative_std":extol,
                          "max_trajectory_ds_cv":maxcv,"max_achieved_cfl":maxcfl,"max_trajectory_relative_length_change":maxlen,"max_rigid_shape_residual":maxshape,"max_log_norm_growth":maxlog,
                          "max_tangent_fraction":maxtan,"max_rigid_fraction":maxrig,"spectral_parity_tolerance":spectol,"excitation_transport_odd_tolerance":expar},
            "status_counts":counts,"pair_independent_statistics":{"n_source_pairs":len(source_stats),"abs_xiH_vs_abs_transport_pearson":pear_mag,"abs_xiH_vs_abs_transport_spearman":spear_mag,
                                                                   "beta_negative":sum(b<0 for b in betas),"beta_positive":sum(b>0 for b in betas),"beta_finite_n":len(betas),"source_pair_aggregates":source_stats},
            "pairs":pairs,"resolution_convergence":resolution_conv,"core_convergence":core_conv}
    write_json(out/"ANALYSIS_BLIND.json",report)
    md=["# SST Chirality–Helicity Transport Polarity Falsifier v0.2.0 — Blind Analysis","",
        "**Blindness:** source name/path, family, original/mirror role and parse provenance were not read. The reveal mapping is not present in this output directory.","",
        "## Gate counts","","```json",json.dumps(counts,indent=2),"```","","## Independent pair statistics","",
        f"- Independent source mirror pairs: {len(source_stats)}",f"- corr(|Xi_H|, |Pi|): Pearson = {pear_mag:.6g}" if math.isfinite(pear_mag) else "- corr(|Xi_H|, |Pi|): Pearson = n/a",
        f"- corr ranks: Spearman = {spear_mag:.6g}" if math.isfinite(spear_mag) else "- corr ranks: Spearman = n/a",
        f"- pair-invariant beta signs: negative={sum(b<0 for b in betas)}, positive={sum(b>0 for b in betas)}, finite n={len(betas)}","",
        "## Pair gates","",
        "| pair | C | N | a/L | Xi odd | RE max | RE parity | |Pi| | Pi odd | launch Pi odd max | exc rel.std | log amp | shape drift | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for p in pairs:
        md.append(f"| {p['pair_id']} | {p['n_components']} | {p['resolution_requested']} | {p['core_fraction']:.5g} | {p['helicity_odd_residual']:.3g} | {p['relative_equilibrium_max']:.3g} | {p['relative_equilibrium_parity_residual']:.3g} | {p['transport_signal_abs_mean']:.3g} | {p['transport_odd_residual']:.3g} | {p['excitation_parity']['transport_odd_residual_max_significant']:.3g} | {p['excitation_relative_std']:.3g} | {p['max_log_norm_growth']:.3g} | {p['shape_drift_max']:.3g} | {p['status']} |")
    md += ["","## Interpretation order","","A `PASS_*` is only reachable after parity, timestep/mesh, relative-equilibrium, shape-drift, gauge and amplification gates. Mirror symmetry alone is therefore not counted as a physical detection."]
    (out/"REPORT_BLIND.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    manifest=read_json(out/"BLIND_MANIFEST.json")
    seal={"format":"SST-CHIRALITY-BLIND-SEAL-2.0","private_mapping_commitment_sha256":manifest["private_mapping_commitment_sha256"],"private_key_id":manifest["private_key_id"],
          "files":{"BLIND_MANIFEST.json":sha256_file(out/"BLIND_MANIFEST.json"),"BLIND_RESULTS.json":sha256_file(out/"BLIND_RESULTS.json"),
                   "ANALYSIS_BLIND.json":sha256_file(out/"ANALYSIS_BLIND.json"),"REPORT_BLIND.md":sha256_file(out/"REPORT_BLIND.md")}}
    write_json(out/"BLIND_SEAL.json",seal)
    print(json.dumps({"status_counts":counts,"pair_independent_statistics":report["pair_independent_statistics"],"blind_seal_sha256":sha256_file(out/"BLIND_SEAL.json")},indent=2))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("config"); ap.add_argument("outdir"); a=ap.parse_args(); analyze(a.config,a.outdir)
if __name__=="__main__": main()
