from __future__ import annotations
import argparse, json, time
from pathlib import Path
import numpy as np
from .config import load_config
from .geometry import resample_closed, normalize_curve, ds_cv
from .physics import candidate_metrics, require_native
from .util import read_json, write_json, sha256_file


def run_blind(config_path: str, outdir: str):
    require_native()
    cfg=load_config(config_path); out=Path(outdir)
    manifest=read_json(out/"BLIND_MANIFEST.json")
    results=[]
    started=time.time()
    resolutions=[int(n) for n in cfg.get("resolutions",[96])]
    cores=[float(a) for a in cfg.get("core_fractions",[0.04])]
    for pair in manifest["pairs"]:
        for lab in ("A","B"):
            info=pair["variants"][lab]
            p=out/"blind_inputs"/info["file"]
            if sha256_file(p)!=info["sha256"]:
                raise RuntimeError(f"blind input hash mismatch: {p}")
            base=np.load(p,allow_pickle=False)
            for n in resolutions:
                x=resample_closed(base,n)
                x,_=normalize_curve(x)
                if ds_cv(x)>float(cfg.get("max_ds_cv",0.20)):
                    raise RuntimeError(f"ds_CV > gate for {pair['pair_id']} {lab} N={n}")
                for core in cores:
                    local=dict(cfg)
                    local["core_fraction"]=core
                    t0=time.time()
                    m=candidate_metrics(x,local)
                    results.append({
                        "pair_id":pair["pair_id"],"variant":lab,"resolution":n,"core_fraction":core,
                        "backend":"cpp-pybind11","source_identity_read":False,"mirror_identity_read":False,
                        "private_manifest_read":False,"carrier_identity_read":False,"condition_identity_read":False,
                        "runtime_s":time.time()-t0,**m
                    })
                    print(f"[blind] {pair['pair_id']} {lab} N={n} a/L={core:.5g} Pi={m['transport_pi']:+.6g} XiH={m['xi_helicity_tube']:+.6g}")
    payload={
        "format":"SST-CHIRALITY-BLIND-RESULTS-1.0",
        "backend":"cpp-pybind11",
        "source_identity_read":False,"mirror_identity_read":False,"private_manifest_read":False,
        "carrier_identity_read":False,"condition_identity_read":False,
        "runtime_s":time.time()-started,
        "results":results
    }
    write_json(out/"BLIND_RESULTS.json",payload)
    print(json.dumps({k:payload[k] for k in ["format","backend","source_identity_read","mirror_identity_read","private_manifest_read","runtime_s"]},indent=2))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("config"); ap.add_argument("outdir")
    a=ap.parse_args(); run_blind(a.config,a.outdir)
if __name__=="__main__": main()
