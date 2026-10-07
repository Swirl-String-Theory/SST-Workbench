from __future__ import annotations
import json, hashlib, shutil, subprocess, os, sys
from pathlib import Path
from .util import sha256_file, write_json

_REQUIRED = (
    "BLIND_MANIFEST.json","CERT_CONFIG.json","BACKEND_QUALIFICATION.json",
    "CERT_RESULTS_BLIND.json","CERT_ANALYSIS_BLIND.json","CERT_REPORT_BLIND.md",
    "CERT_BLIND_SEAL.json"
)

def find_a054_roots(workbench: Path):
    root=Path(workbench)/"01_research"/"A_falsifiers"/"A054_nucleon_topology_architecture_blind_falsifier"
    if not root.is_dir():
        hits=[p for p in (Path(workbench)/"01_research").rglob("A054_nucleon_topology_architecture_blind_falsifier") if p.is_dir()]
        if len(hits)!=1: raise FileNotFoundError(f"A054 root ambiguous/missing: {hits}")
        root=hits[0]
    return root

def _campaign_is_certified(p: Path, preset: str|None=None):
    if not p.is_dir() or not all((p/f).is_file() for f in _REQUIRED): return False
    try:
        m=json.loads((p/"BLIND_MANIFEST.json").read_text(encoding="utf-8"))
        if preset and m.get("preset")!=preset: return False
        verify_a054_seal(p)
        return True
    except Exception:
        return False

def find_certified_campaign(workbench: Path, preset="full"):
    root=find_a054_roots(workbench)
    candidates=[p for p in root.rglob("*") if _campaign_is_certified(p,preset)]
    if not candidates: return None
    # Prefer timestamped campaign directories lexically, then modification time.
    candidates.sort(key=lambda p:(p.name, p.stat().st_mtime), reverse=True)
    return candidates[0]

def find_a054_source(workbench: Path):
    root=find_a054_roots(workbench)
    candidates=[]
    for p in root.iterdir():
        if p.is_dir() and (p/"run_all_full.cmd").is_file() and (p/"src"/"a054_ntaf"/"certify_v020.py").is_file():
            candidates.append(p)
    if not candidates:
        candidates=[p for p in root.rglob("run_all_full.cmd")
                    if (p.parent/"src"/"a054_ntaf"/"certify_v020.py").is_file()]
        candidates=[p.parent for p in candidates]
    if not candidates: raise FileNotFoundError("No unpacked A054 v0.2.x source with run_all_full.cmd found")
    def score(p):
        name=p.name.lower()
        rev=3 if "r3" in name else 2 if "r2" in name else 1 if "r1" in name else 0
        return (rev,p.stat().st_mtime)
    return sorted(candidates,key=score,reverse=True)[0]

def ensure_certified_campaign(workbench: Path, preset="full", auto_run=False):
    found=find_certified_campaign(workbench,preset)
    if found is not None: return found
    if not auto_run:
        raise FileNotFoundError(
            f"No sealed A054 v0.2.x {preset} certification campaign found. "
            f"Run the authoritative A054 campaign first.")
    src=find_a054_source(workbench)
    script={"full":"run_all_full.cmd","extended":"run_all_extended.cmd","basic":"run_all.cmd"}[preset]
    if os.name!="nt":
        raise RuntimeError("Automatic A054 .cmd execution is Windows-only")
    cp=subprocess.run(["cmd.exe","/c",str(src/script),str(workbench)],cwd=str(src))
    if cp.returncode:
        raise RuntimeError(f"A054 {preset} campaign failed with exit code {cp.returncode}")
    found=find_certified_campaign(workbench,preset)
    if found is None:
        raise RuntimeError("A054 command returned success but no sealed certified campaign was found")
    return found

def verify_a054_seal(campaign: Path):
    c=Path(campaign); s=json.loads((c/"CERT_BLIND_SEAL.json").read_text(encoding="utf-8"))
    checks={
      "manifest_sha256":"BLIND_MANIFEST.json",
      "results_sha256":"CERT_RESULTS_BLIND.json",
      "analysis_sha256":"CERT_ANALYSIS_BLIND.json",
      "report_sha256":"CERT_REPORT_BLIND.md",
      "config_sha256":"CERT_CONFIG.json",
      "backend_qualification_sha256":"BACKEND_QUALIFICATION.json",
    }
    for k,f in checks.items():
        if sha256_file(c/f)!=s[k]:
            raise RuntimeError(f"A054 blind seal mismatch: {f}")
    private=c/"_private"/"PRIVATE_MAPPING.json"
    if private.is_file() and sha256_file(private)!=s["private_mapping_commitment"]:
        raise RuntimeError("A054 private mapping commitment mismatch")
    return s

def _pair_metric(eigs, rel_imag_floor=1e-7):
    zs=[complex(float(z["re"]),float(z["im"])) for z in (eigs or [])]
    scale=max([abs(z) for z in zs]+[1e-30])
    pos=[z.imag for z in zs if z.imag>rel_imag_floor*scale]
    neg=[-z.imag for z in zs if z.imag<-rel_imag_floor*scale]
    if not pos or not neg:
        return {"pair_available":False,"best_relative_frequency_asymmetry":None}
    best=min(abs(a-b)/max(0.5*(a+b),1e-30) for a in pos for b in neg)
    return {"pair_available":True,"best_relative_frequency_asymmetry":float(best)}

def derive_blind_compound_features(campaign: Path, symmetry_max=0.25, rel_imag_floor=1e-7):
    c=Path(campaign); verify_a054_seal(c)
    cfg=json.loads((c/"CERT_CONFIG.json").read_text(encoding="utf-8"))
    res=json.loads((c/"CERT_RESULTS_BLIND.json").read_text(encoding="utf-8"))
    ana=json.loads((c/"CERT_ANALYSIS_BLIND.json").read_text(encoding="utf-8"))
    fine=max(int(x) for x in cfg["n_ladder"])
    fine_by={(r["anonymous_id"],r["sector"]):r for r in res["results"] if r.get("N")==fine}
    rows=[]
    for aid,summary in ana["summaries"].items():
        for sec,bs in summary["sectors"].items():
            r=fine_by.get((aid,sec),{})
            spec=r.get("spectrum") or {}
            cp=_pair_metric(spec.get("eigenvalues"),rel_imag_floor)
            kspec=spec.get("kelvin_restricted") or {}
            kcp=_pair_metric(kspec.get("eigenvalues"),rel_imag_floor)
            rpo=r.get("rpo") or {}; floq=r.get("floquet") or {}
            row={
              "anonymous_id":aid,"sector":sec,"fine_resolution":fine,
              "status":bs.get("status"),"spatial_converged":bs.get("spatial_converged"),
              "counterpropagating_pair":cp["pair_available"],
              "counterpropagating_pair_symmetric":bool(cp["pair_available"] and cp["best_relative_frequency_asymmetry"]<=symmetry_max),
              "counterpropagating_asymmetry":cp["best_relative_frequency_asymmetry"],
              "kelvin_counterpropagating_pair":kcp["pair_available"],
              "kelvin_counterpropagating_pair_symmetric":bool(kcp["pair_available"] and kcp["best_relative_frequency_asymmetry"]<=symmetry_max),
              "kelvin_counterpropagating_asymmetry":kcp["best_relative_frequency_asymmetry"],
              "oscillatory_fraction":spec.get("oscillatory_fraction"),
              "normalized_growth":spec.get("normalized_max_real"),
              "kelvin_growth":kspec.get("normalized_max_real"),
              "ringdown_max_over_initial":(r.get("ringdown") or {}).get("max_over_initial"),
              "rpo_accepted":bool(rpo.get("accepted",False)),
              "floquet_evaluated":bool(floq.get("evaluated",False)),
              "floquet_max_nontrivial_abs":floq.get("max_nontrivial_abs"),
            }
            rows.append(row)
    summary=[]
    for aid in sorted({r["anonymous_id"] for r in rows}):
        rr=[r for r in rows if r["anonymous_id"]==aid]
        q0=next((r for r in rr if r["sector"]=="Q0"),{})
        opp=[r for r in rr if r["sector"] in ("Q1","Q2","Q3")]
        summary.append({
          "anonymous_id":aid,
          "q0_counterpropagating_pair_symmetric":bool(q0.get("counterpropagating_pair_symmetric",False)),
          "q0_kelvin_counterpropagating_pair_symmetric":bool(q0.get("kelvin_counterpropagating_pair_symmetric",False)),
          "opposed_counterpropagating_count":sum(bool(x.get("counterpropagating_pair_symmetric")) for x in opp),
          "opposed_kelvin_counterpropagating_count":sum(bool(x.get("kelvin_counterpropagating_pair_symmetric")) for x in opp),
          "opposed_certified_count":sum(str(x.get("status","")).startswith("CERTIFIED_") for x in opp),
          "opposed_rpo_count":sum(bool(x.get("rpo_accepted")) for x in opp),
          "opposed_floquet_count":sum(bool(x.get("floquet_evaluated")) for x in opp),
          "all_same_status":q0.get("status"),
        })
    return {"schema":"A055-A054-COMPOUND-BLIND-BRIDGE-3.0",
            "source_campaign":str(c),"source_seal":json.loads((c/"CERT_BLIND_SEAL.json").read_text()),
            "fine_resolution":fine,"rows":rows,"candidate_summaries":summary}

def attach_compound_blind(a055_out: Path, workbench: Path, bridge_cfg: dict):
    if not bridge_cfg.get("enabled",True):
        return {"status":"DISABLED"}
    preset=bridge_cfg.get("a054_preset","full")
    campaign=ensure_certified_campaign(workbench,preset,bool(bridge_cfg.get("auto_run_if_missing",False)))
    bridge=derive_blind_compound_features(
        campaign,float(bridge_cfg.get("counterpropagating_symmetry_max",0.25)),
        float(bridge_cfg.get("relative_imag_floor",1e-7)))
    target=Path(a055_out)/"BLIND"/"COMPOUND_A054"
    target.mkdir(parents=True,exist_ok=True)
    write_json(target/"COMPOUND_FEATURES_BLIND.json",bridge)
    # Copy only already-blind/sealed upstream evidence.
    for name in _REQUIRED:
        shutil.copy2(campaign/name,target/name)
    priv_src=campaign/"_private"/"PRIVATE_MAPPING.json"
    if not priv_src.is_file():
        raise FileNotFoundError("A054 private mapping unavailable for later reveal")
    priv_dst=Path(a055_out)/"PRIVATE_REVEAL_DO_NOT_INCLUDE_IN_BLIND"/"COMPOUND_A054"
    priv_dst.mkdir(parents=True,exist_ok=True)
    shutil.copy2(priv_src,priv_dst/"PRIVATE_MAPPING.json")
    write_json(priv_dst/"SOURCE_CAMPAIGN.json",{"campaign":str(campaign),"preset":preset})
    return {"status":"ATTACHED","campaign":str(campaign),
            "candidate_count":len(bridge["candidate_summaries"]),"row_count":len(bridge["rows"])}

def preflight(workbench: Path, preset="full"):
    c=find_certified_campaign(workbench,preset)
    return {"status":"PASS","campaign":str(c),"seal":verify_a054_seal(c)} if c else {
        "status":"MISSING_CERTIFIED_CAMPAIGN","a054_source":str(find_a054_source(workbench))}
