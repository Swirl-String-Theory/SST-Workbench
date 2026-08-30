from __future__ import annotations
import argparse, json, math
from collections import defaultdict
from pathlib import Path
import numpy as np
from .config import load_config
from .util import read_json, write_json, sha256_file


def _rank(x):
    x=np.asarray(x,float); order=np.argsort(x); r=np.empty(len(x),float); r[order]=np.arange(len(x),dtype=float)
    return r

def _corr(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float)
    if len(a)<3 or np.std(a)<1e-15 or np.std(b)<1e-15: return float("nan")
    return float(np.corrcoef(a,b)[0,1])
def _residual_odd(a,b):
    return abs(a+b)/max(abs(a)+abs(b),1e-15)
def _mag_mismatch(a,b):
    return abs(abs(a)-abs(b))/max(abs(a)+abs(b),1e-15)

def _spectral_hausdorff(sa,sb):
    a=np.array([complex(r,i) for r,i in sa["eigenvalues"]],dtype=np.complex128)
    b=np.array([complex(r,i) for r,i in sb["eigenvalues"]],dtype=np.complex128)
    if len(a)==0 or len(b)==0: return float("inf")
    scale=max(float(np.max(np.abs(a))),float(np.max(np.abs(b))),1e-15)
    # Symmetric nearest-neighbour Hausdorff distance; eigenvalue ordering is irrelevant.
    da=max(float(np.min(np.abs(z-b))) for z in a)
    db=max(float(np.min(np.abs(z-a))) for z in b)
    return max(da,db)/scale


def analyze(config_path: str, outdir: str):
    cfg=load_config(config_path); out=Path(outdir)
    data=read_json(out/"BLIND_RESULTS.json")
    rows=data["results"]
    grouped=defaultdict(dict)
    for r in rows:
        grouped[(r["pair_id"],r["resolution"],r["core_fraction"])][r["variant"]]=r
    pair_rows=[]
    for key,ab in sorted(grouped.items()):
        if set(ab)!={"A","B"}: continue
        A,B=ab["A"],ab["B"]
        hres=_residual_odd(A["xi_helicity_tube"],B["xi_helicity_tube"])
        wres=_residual_odd(A["writhe"],B["writhe"])
        pres=_residual_odd(A["transport_pi"],B["transport_pi"])
        pmag=_mag_mismatch(A["transport_pi"],B["transport_pi"])
        signal=0.5*(abs(A["transport_pi"])+abs(B["transport_pi"]))
        specres=_spectral_hausdorff(A["spectrum"],B["spectrum"])
        exrel=0.5*(A["transport_pi_std_over_excitations"]+B["transport_pi_std_over_excitations"])/max(signal,1e-15)
        pair_rows.append({
            "pair_id":key[0],"resolution":key[1],"core_fraction":key[2],
            "helicity_odd_residual":hres,"writhe_odd_residual":wres,
            "transport_odd_residual":pres,"transport_magnitude_mismatch":pmag,
            "transport_signal_abs_mean":signal,
            "spectral_hausdorff_relative":specres,
            "excitation_relative_std":exrel,
            "racemic_pair_mean":0.5*(A["transport_pi"]+B["transport_pi"]),
            "A_pi":A["transport_pi"],"B_pi":B["transport_pi"],
            "A_xiH":A["xi_helicity_tube"],"B_xiH":B["xi_helicity_tube"]
        })

    htol=float(cfg.get("helicity_odd_tolerance",0.20))
    ptol=float(cfg.get("transport_odd_tolerance",0.30))
    mtol=float(cfg.get("transport_magnitude_tolerance",0.30))
    minsignal=float(cfg.get("min_transport_signal",0.01))
    spectol=float(cfg.get("spectral_parity_tolerance",0.05))
    extol=float(cfg.get("max_excitation_relative_std",1.0))
    statuses=[]
    for p in pair_rows:
        if p["helicity_odd_residual"]>htol:
            s="INVALID_PARITY_HELICITY"
        elif p["spectral_hausdorff_relative"]>spectol:
            s="INVALID_PARITY_SPECTRUM"
        elif p["transport_signal_abs_mean"]<minsignal:
            s="NULL_NO_DIRECTIONAL_SIGNAL"
        elif p["excitation_relative_std"]>extol:
            s="INDETERMINATE_EXCITATION_SENSITIVE"
        elif p["transport_odd_residual"]<=ptol and p["transport_magnitude_mismatch"]<=mtol:
            s="PASS_MIRROR_ODD_TRANSPORT"
        else:
            s="FAIL_MIRROR_ODD_TRANSPORT"
        p["status"]=s; statuses.append(s)

    # Anonymous candidate-level Xi_H <-> Pi association.
    xi=np.array([r["xi_helicity_tube"] for r in rows],float)
    pi=np.array([r["transport_pi"] for r in rows],float)
    pear=_corr(xi,pi); spear=_corr(_rank(xi),_rank(pi))

    # Resolution convergence of pair transport signal for same pair/core.
    conv=[]
    pc=defaultdict(list)
    for p in pair_rows: pc[(p["pair_id"],p["core_fraction"])].append(p)
    for key,v in pc.items():
        v=sorted(v,key=lambda q:q["resolution"])
        if len(v)>=2:
            last=v[-2:]
            A0,A1=last[0]["A_pi"],last[1]["A_pi"]
            B0,B1=last[0]["B_pi"],last[1]["B_pi"]
            conv.append({"pair_id":key[0],"core_fraction":key[1],
                         "N_low":last[0]["resolution"],"N_high":last[1]["resolution"],
                         "delta_A":abs(A1-A0),"delta_B":abs(B1-B0),
                         "sign_stable_A":bool(np.sign(A0)==np.sign(A1) or min(abs(A0),abs(A1))<minsignal),
                         "sign_stable_B":bool(np.sign(B0)==np.sign(B1) or min(abs(B0),abs(B1))<minsignal)})

    counts={s:statuses.count(s) for s in sorted(set(statuses))}
    report={
        "format":"SST-CHIRALITY-ANALYSIS-1.0",
        "blindness":{"source_identity_read":False,"mirror_identity_read":False,"private_manifest_read":False},
        "thresholds":{"helicity_odd_tolerance":htol,"spectral_parity_tolerance":spectol,
                      "transport_odd_tolerance":ptol,"transport_magnitude_tolerance":mtol,
                      "min_transport_signal":minsignal,"max_excitation_relative_std":extol},
        "status_counts":counts,
        "anonymous_xiH_transport":{"pearson":pear,"spearman":spear,"n":len(rows)},
        "pairs":pair_rows,"convergence":conv
    }
    write_json(out/"ANALYSIS_BLIND.json",report)

    md=[]
    md += ["# SST Chirality–Helicity Transport Polarity Falsifier — Blind Analysis","",
           "**Identity status:** source identity, knot family and original/mirror assignment were not read.","",
           "## Gate counts","", "```json",json.dumps(counts,indent=2),"```","",
           "## Anonymous helicity/transport association","",
           f"- Pearson $r$ = {pear:.6g}" if math.isfinite(pear) else "- Pearson r = n/a",
           f"- Spearman $\\rho$ = {spear:.6g}" if math.isfinite(spear) else "- Spearman rho = n/a","",
           "## Pair gates","",
           "| pair | N | a/L | XiH odd | spectrum parity | Pi odd | |Pi| | excitation rel.std | status |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for p in pair_rows:
        md.append(f"| {p['pair_id']} | {p['resolution']} | {p['core_fraction']:.5g} | {p['helicity_odd_residual']:.3g} | {p['spectral_hausdorff_relative']:.3g} | {p['transport_odd_residual']:.3g} | {p['transport_signal_abs_mean']:.3g} | {p['excitation_relative_std']:.3g} | {p['status']} |")
    (out/"REPORT_BLIND.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    manifest=read_json(out/"BLIND_MANIFEST.json")
    seal={
        "format":"SST-CHIRALITY-BLIND-SEAL-1.0",
        "private_mapping_commitment_sha256":manifest["private_mapping_commitment_sha256"],
        "files":{
            "BLIND_MANIFEST.json":sha256_file(out/"BLIND_MANIFEST.json"),
            "BLIND_RESULTS.json":sha256_file(out/"BLIND_RESULTS.json"),
            "ANALYSIS_BLIND.json":sha256_file(out/"ANALYSIS_BLIND.json"),
            "REPORT_BLIND.md":sha256_file(out/"REPORT_BLIND.md")
        }
    }
    write_json(out/"BLIND_SEAL.json",seal)
    print(json.dumps({"status_counts":counts,"anonymous_xiH_transport":report["anonymous_xiH_transport"],
                      "blind_seal_sha256":sha256_file(out/"BLIND_SEAL.json")},indent=2))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("config"); ap.add_argument("outdir")
    a=ap.parse_args(); analyze(a.config,a.outdir)
if __name__=="__main__": main()
