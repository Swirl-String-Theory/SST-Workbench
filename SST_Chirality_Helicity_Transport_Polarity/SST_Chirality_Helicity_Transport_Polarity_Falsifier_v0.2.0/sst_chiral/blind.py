from __future__ import annotations
import argparse, json, time
from pathlib import Path
from .config import load_config
from .geometry import load_geometry_npz, resample_geometry, normalize_geometry, ds_cv_geometry
from .physics import candidate_metrics, require_native
from .util import read_json, write_json, sha256_file


def run_blind(config_path:str,outdir:str):
    require_native(); cfg=load_config(config_path); out=Path(outdir); manifest=read_json(out/"BLIND_MANIFEST.json")
    results=[]; started=time.time(); resolutions=[int(n) for n in cfg.get("resolutions",[96])]; cores=[float(a) for a in cfg.get("core_fractions",[0.025])]
    min_per=int(cfg.get("min_points_per_component",24)); max_cv=float(cfg.get("max_ds_cv",0.25))
    for pair in manifest["pairs"]:
        for lab in ("A","B"):
            info=pair["variants"][lab]; p=out/"blind_inputs"/info["file"]
            if sha256_file(p)!=info["sha256"]: raise RuntimeError(f"blind input hash mismatch: {p}")
            base=load_geometry_npz(p)
            for n in resolutions:
                comps=resample_geometry(base,n,min_per); comps,_=normalize_geometry(comps); cv=ds_cv_geometry(comps)
                if cv>max_cv: raise RuntimeError(f"ds_CV={cv:.4g} > {max_cv} for {pair['pair_id']} {lab} N={n}")
                for core in cores:
                    local=dict(cfg); local["core_fraction"]=core; t0=time.time(); m=candidate_metrics(comps,local)
                    row={"pair_id":pair["pair_id"],"variant":lab,"resolution_requested":n,"resolution_actual":m["n_points_total"],"core_fraction":core,
                         "backend":"cpp-pybind11-multicomponent-jvp","source_identity_read":False,"mirror_identity_read":False,"private_manifest_read":False,
                         "runtime_s":time.time()-t0,"ds_cv_initial":cv,**m}
                    results.append(row)
                    print(f"[blind] {pair['pair_id']} {lab} N={m['n_points_total']} C={m['n_components']} a/L={core:.5g} "
                          f"RE={m['relative_equilibrium_initial']['relative_residual']:.4g} Pi={m['transport_pi']:+.6g} Xi={m['xi_helicity_centerline']:+.6g}")
    payload={"format":"SST-CHIRALITY-BLIND-RESULTS-2.0","backend":"cpp-pybind11-multicomponent-jvp","source_identity_read":False,
             "mirror_identity_read":False,"private_manifest_read":False,"private_mapping_present_in_output":False,
             "config_sha256":sha256_file(config_path),"runtime_s":time.time()-started,"results":results}
    write_json(out/"BLIND_RESULTS.json",payload)
    print(json.dumps({"format":payload["format"],"n_rows":len(results),"runtime_s":payload["runtime_s"],"private_manifest_read":False},indent=2))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("config"); ap.add_argument("outdir"); a=ap.parse_args(); run_blind(a.config,a.outdir)
if __name__=="__main__": main()
