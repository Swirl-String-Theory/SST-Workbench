from __future__ import annotations
import json, os, shutil, sys, traceback, zipfile
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from . import __version__, native
from .blinding import audit_forbidden_targets, make_manifest, sha256_file
from .geometry import discover_external_curves
from .simulation import scale_from_config
from .gates import run_e3, run_e4, run_e5, run_e2, run_e1

ORDER=[("E3",run_e3),("E4",run_e4),("E5",run_e5),("E2",run_e2),("E1",run_e1)]

def clean(x):
    if isinstance(x,dict): return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [clean(v) for v in x]
    if isinstance(x,np.ndarray): return clean(x.tolist())
    if isinstance(x,np.generic): return x.item()
    if isinstance(x,complex): return {"re":x.real,"im":x.imag}
    if isinstance(x,float) and not np.isfinite(x): return None
    return x

def write_json(path: Path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(clean(obj),indent=2,sort_keys=True)+"\n",encoding="utf-8")

def resolve_external_root(cfg:dict, override:str|None)->Path|None:
    if override: return Path(override)
    for s in cfg.get("external_input_roots",[]):
        p=Path(s)
        if p.exists(): return p
    return None

def zip_output(outdir:Path)->Path:
    z=outdir.with_suffix(".zip")
    if z.exists(): z.unlink()
    with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED) as zz:
        for p in outdir.rglob("*"):
            if p.is_file(): zz.write(p,p.relative_to(outdir.parent))
    return z

def run_campaign(config_path:str|Path,outdir:str|Path,*,require_native:bool=True,input_root:str|None=None,zip_results:bool=True)->dict:
    config_path=Path(config_path).resolve(); cfg=json.loads(config_path.read_text(encoding="utf-8")); audit_forbidden_targets(cfg)
    outdir=Path(outdir).resolve(); outdir.mkdir(parents=True,exist_ok=True)
    if require_native: native.require_native()
    threads=native.set_threads(None)
    ext_root=resolve_external_root(cfg,input_root); external=[]; input_hashes={}
    if ext_root:
        external=discover_external_curves(ext_root,int(cfg.get("max_external_curves",8)))
        # Hash source files by unique visible name when possible; research calculations never depend on filenames semantically.
        for name,curve in external:
            import hashlib
            input_hashes[name]=hashlib.sha256(np.ascontiguousarray(curve,dtype=np.float64).tobytes()).hexdigest()
    manifest=make_manifest(cfg,config_path,input_hashes,__version__)
    manifest.update({"backend":native.backend_name(),"native_threads":threads,"external_input_root":str(ext_root) if ext_root else None,"external_curve_count":len(external)})
    write_json(outdir/"blind_manifest.json",manifest)
    shutil.copy2(config_path,outdir/"frozen_config.json")
    scale=scale_from_config(cfg)
    write_json(outdir/"physical_scale.json",{
        "L0_m":scale.L0_m,"core_dimless":scale.core_dimless,"gamma_m2_s":scale.gamma_m2_s,"rho_kg_m3":scale.rho_kg_m3,
        "time_scale_s":scale.time_s,"velocity_scale_m_s":scale.velocity_m_s,"energy_scale_J":scale.energy_J,"impulse_scale_kg_m_s":scale.impulse_kg_m_s,
        "note":"These are simulation inputs/scales, not blind benchmark targets."
    })
    rng=np.random.default_rng(int(cfg["blind_protocol"]["seed"]))
    gates={}; stopped=False
    for gate,func in ORDER:
        print(f"[blind] {gate} starting...")
        try:
            res=func(cfg,scale,outdir/gate,rng=rng,external_curves=external)
        except Exception as exc:
            res={"gate":gate,"verdict":"ERROR","error":repr(exc),"traceback":traceback.format_exc()}
        gates[gate]=res; write_json(outdir/gate/"result.json",res)
        print(f"[blind] {gate}: {res.get('verdict')}")
        if res.get("verdict")=="ERROR" and cfg.get("stop_on_error",True): stopped=True; break
    verdict_counts={k:sum(1 for r in gates.values() if r.get("verdict")==k) for k in ["PASS","FAIL","INCONCLUSIVE","ERROR"]}
    summary={
        "package":"Einstein_SST_Blind_Falsifier","version":__version__,"protocol_hash_sha256":manifest["protocol_hash_sha256"],
        "backend":native.backend_name(),"native_threads":threads,"gate_order":[x[0] for x in ORDER],"gates":{k:v.get("verdict") for k,v in gates.items()},
        "verdict_counts":verdict_counts,"stopped_on_error":stopped,
        "interpretation":"PASS/FAIL applies only to the preregistered closure tested by each gate. INCONCLUSIVE is not converted to PASS. No external target constants are consulted."
    }
    write_json(outdir/"run_summary.json",summary)
    if zip_results:
        z=zip_output(outdir); summary["results_zip"]=str(z); write_json(outdir/"run_summary.json",summary)
    return summary
