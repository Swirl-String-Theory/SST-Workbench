from __future__ import annotations
import json
import platform
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from native_ext import load_backend
from sst6.blind import canonical_hash, select_blind
from sst6.constants import CANONICAL_CONSTANTS
from sst6.io import discover_datasets, write_csv, write_json
from sst6.gates import source1_uosukainen as s1
from sst6.gates import source2_abe_okuyama as s2
from sst6.gates import source3_rossby as s3
from sst6.gates import source4_kleckner as s4
from sst6.gates import source5_hopfion as s5
from sst6.gates import source6_helmholtz as s6

ITEM_GATES: dict[str, Callable] = {
    "U1_CROSS_SELF_SCALING": s1.cross_self_scaling,
    "U2_TRANSPORT_MULTIPOLE": s1.multipole_no_monopole,
    "AO1_MODAL_ADDITIVITY": s2.modal_additivity,
    "AO6_PHASE_ERASURE": s2.phase_erasure,
    "AO3_BOLTZMANN_GEOMETRY_PROXY": s2.boltzmann_geometry_proxy,
    "R3_GRADIENT_LOCK_PROXY": s3.gradient_lock_proxy,
    "K4_ANTIPARALLEL_CONTACT": s4.contact_precursor,
    "K4_PERTURBATION_ROBUSTNESS": s4.perturbation_robustness,
    "H5_INTRINSIC_SCALE": s5.scale_energy,
    "H5_CALUGAREANU_RIBBON": s5.calugareanu_ribbon,
}
GLOBAL_GATES: dict[str, Callable] = {
    "H6_CLASSICAL_NULL_CALIBRATION": s6.classical_null_calibration,
    "H6_NONLINEAR_MIXING_CALIBRATION": s6.nonlinear_mixing_calibration,
}


def load_config(path: Path) -> dict:
    cfg=json.loads(path.read_text(encoding="utf-8"))
    cfg["_config_path"]=str(path.resolve())
    return cfg


def _flatten_result(item_id, r):
    row={"item_id":item_id,"source":r.get("source"),"gate_id":r.get("gate_id"),"tier":r.get("tier"),"verdict":r.get("verdict")}
    vals=r.get("values",{})
    for k,v in vals.items():
        if isinstance(v,(str,int,float,bool)) or v is None: row[k]=v
    return row


def run_campaign(config: dict, dataset_dir: Path, out_dir: Path, *, force_python=False, require_native=False) -> dict:
    out_dir.mkdir(parents=True,exist_ok=True)
    datasets=discover_datasets(dataset_dir,config.get("pattern","*_final.txt"))
    if not datasets: raise RuntimeError(f"No datasets found in {dataset_dir}")
    public_cfg={k:v for k,v in config.items() if not k.startswith("_")}
    blind_selection_sha256=canonical_hash({"config":public_cfg,"file_hashes":sorted(d.sha256 for d in datasets)})
    prereg={
        "campaign_name":config.get("campaign_name","SST six-source blind falsifier"),
        "version":config.get("version","0.1.0"),
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "dataset_dir":str(dataset_dir.resolve()),
        "dataset_files":[{"item_id":d.item_id,"sha256":d.sha256,"path":str(d.path)} for d in datasets],
        "config":public_cfg,
        "config_sha256":canonical_hash(public_cfg),
        "canonical_constants":CANONICAL_CONSTANTS,
        "blind_selection_sha256":blind_selection_sha256,
        "blind_policy":{
            "selection":"SHA256(config + sorted file-content hashes); filenames/topology labels do not affect subset selection",
            "seeds":"SHA256(file content + gate id)",
            "particle_targets_used":False,
            "empirical_mass_targets_used":False,
        },
    }
    prereg["campaign_sha256"]=canonical_hash(prereg)
    write_json(out_dir/"00_preregistration_manifest.json",prereg)

    backend,bname=load_backend(force_python=force_python,force_build=False,build_verbose=False)
    if require_native and bname!="cpp": raise RuntimeError("Native backend required but C++ extension did not load.")
    runtime={"python":sys.version,"platform":platform.platform(),"backend":bname}
    write_json(out_dir/"01_runtime.json",runtime)

    results=[]; errors=[]; gates=config.get("gates",{})
    # Global calibration gates.
    for gid,fn in GLOBAL_GATES.items():
        gc=gates.get(gid,{})
        if not gc.get("enabled",False): continue
        try:
            r=fn(blind_selection_sha256,gc); r["item_id"]="__GLOBAL__"; results.append(r)
            write_json(out_dir/"global"/f"{gid}.json",r)
        except Exception as exc:
            errors.append({"item_id":"__GLOBAL__","gate_id":gid,"error":str(exc),"traceback":traceback.format_exc()})

    for gid,fn in ITEM_GATES.items():
        gc=dict(gates.get(gid,{"enabled":False}))
        if not gc.get("enabled",False): continue
        gc["force_python"]=force_python
        selected=select_blind(datasets,gc.get("max_items"),blind_selection_sha256+":"+gid)
        sel_ids={d.item_id for d in selected}
        write_json(out_dir/f"selection_{gid}.json",{"gate_id":gid,"selected":[{"item_id":d.item_id,"sha256":d.sha256} for d in selected],"max_items":gc.get("max_items")})
        for d in datasets:
            if d.item_id not in sel_ids: continue
            try:
                r=fn(d,gc); r["item_id"]=d.item_id; r["dataset_sha256"]=d.sha256; results.append(r)
                write_json(out_dir/"items"/d.item_id/f"{gid}.json",r)
            except Exception as exc:
                errors.append({"item_id":d.item_id,"gate_id":gid,"error":str(exc),"traceback":traceback.format_exc()})

    for e in errors: write_json(out_dir/"errors"/f"{e['item_id']}__{e['gate_id']}.json",e)
    write_json(out_dir/"all_results.json",results)
    write_csv(out_dir/"all_results_flat.csv",[_flatten_result(r.get("item_id"),r) for r in results])

    calibration=[r for r in results if r.get("tier")=="CALIBRATION"]
    identities=[r for r in results if "IDENTITY" in str(r.get("tier")) or r.get("tier")=="PRIMARY_GEOMETRIC_IDENTITY"]
    hypotheses=[r for r in results if r.get("tier") in {"MODEL_CONDITIONAL","PRIMARY_RESEARCH_HYPOTHESIS","PRIMARY_STATIC_FIELD"}]
    diagnostics=[r for r in results if r.get("tier") in {"DIAGNOSTIC","PROXY_DIAGNOSTIC"}]
    pipeline_ok=(not errors and all(r.get("verdict")=="PASS" for r in calibration+identities))
    summary={
        "campaign_name":prereg["campaign_name"],"campaign_sha256":prereg["campaign_sha256"],"backend":bname,
        "dataset_count":len(datasets),"result_count":len(results),"error_count":len(errors),"pipeline_ok":pipeline_ok,
        "calibration":{"pass":sum(r["verdict"]=="PASS" for r in calibration),"fail":sum(r["verdict"]=="FAIL" for r in calibration)},
        "identity":{"pass":sum(r["verdict"]=="PASS" for r in identities),"fail":sum(r["verdict"]=="FAIL" for r in identities)},
        "research_hypotheses":{"pass":sum(r["verdict"]=="PASS" for r in hypotheses),"fail":sum(r["verdict"]=="FAIL" for r in hypotheses),"count":len(hypotheses)},
        "diagnostics_count":len(diagnostics),
        "important":"Physical/model FAIL verdicts are scientific outcomes and do not make the campaign process exit non-zero. Only pipeline/calibration/errors do.",
    }
    write_json(out_dir/"SUMMARY.json",summary)
    return summary
