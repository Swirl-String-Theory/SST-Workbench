from __future__ import annotations
import argparse, json, secrets
from pathlib import Path
import numpy as np
from .config import load_config
from .geometry import discover_curves, load_curve, normalize_curve, resample_closed, parity_mirror_physical, ds_cv
from .util import write_json, canonical_json, sha256_bytes, sha256_file, random_token


def prepare(config_path: str, outdir: str):
    cfg = load_config(config_path)
    out = Path(outdir)
    blind_dir = out / "blind_inputs"
    priv_dir = out / "_private"
    blind_dir.mkdir(parents=True, exist_ok=True)
    priv_dir.mkdir(parents=True, exist_ok=True)

    dataset = Path(cfg.get("dataset", r"..\..\KnotPlot\knots\final"))
    max_pairs = int(cfg.get("max_pairs", 6))
    source_paths = discover_curves(dataset)
    if not source_paths:
        raise RuntimeError(f"No supported coordinate files under {dataset}")
    # Secretly randomize source order so anonymous pair IDs do not encode filename order.
    secrets.SystemRandom().shuffle(source_paths)

    target_n = int(max(cfg.get("resolutions", [96])))
    private = {
        "format":"SST-CHIRALITY-PRIVATE-1.0",
        "nonce": random_token(32),
        "dataset": str(dataset.resolve()),
        "pairs": []
    }
    public_pairs=[]
    errors=[]
    valid=0
    for p in source_paths:
        if max_pairs > 0 and valid >= max_pairs:
            break
        try:
            raw=load_curve(p)
            x,nmeta=normalize_curve(raw)
            x=resample_closed(x,target_n)
            # re-normalize after interpolation to make L exactly one to numerical tolerance
            x,_=normalize_curve(x)
            y=parity_mirror_physical(x,axis=int(cfg.get("mirror_axis",0)))
            y,_=normalize_curve(y)
            if ds_cv(x)>float(cfg.get("max_ds_cv",0.20)) or ds_cv(y)>float(cfg.get("max_ds_cv",0.20)):
                raise ValueError("ds_CV gate failed after resampling")
        except Exception as e:
            errors.append({"path":str(p),"error":repr(e)})
            continue

        valid += 1
        pair_id=f"P{valid:04d}"
        original_first=bool(secrets.randbits(1))
        variants = {"A": x if original_first else y, "B": y if original_first else x}
        role = {"A":"original" if original_first else "parity_mirror",
                "B":"parity_mirror" if original_first else "original"}
        pubvars={}
        for lab,arr in variants.items():
            fn=f"{pair_id}_{lab}.npy"
            np.save(blind_dir/fn, np.ascontiguousarray(arr,dtype=np.float64), allow_pickle=False)
            pubvars[lab]={
                "file":fn,
                "sha256":sha256_file(blind_dir/fn),
                "n":int(len(arr)),
                "length_normalized":1.0,
                "ds_cv":ds_cv(arr)
            }
        public_pairs.append({"pair_id":pair_id,"variants":pubvars})
        private["pairs"].append({
            "pair_id":pair_id,
            "source_path":str(p.resolve()),
            "source_name":p.name,
            "source_sha256":sha256_file(p),
            "role":role,
            "normalization":nmeta
        })

    if valid == 0:
        raise RuntimeError("No parseable/qualified curves. See prepare_errors.json")

    write_json(out/"prepare_errors.json", errors)
    private_bytes=canonical_json(private)
    commitment=sha256_bytes(private_bytes)
    write_json(priv_dir/"PRIVATE_MAPPING.json", private)
    public={
        "format":"SST-CHIRALITY-BLIND-1.0",
        "n_pairs":valid,
        "n_candidates":2*valid,
        "target_prepare_resolution":target_n,
        "private_mapping_commitment_sha256":commitment,
        "source_identity_exposed":False,
        "mirror_identity_exposed":False,
        "source_order_randomized":True,
        "blind_fields_hidden":["source_path","source_name","knot_family","original_vs_parity_mirror"],
        "pairs":public_pairs
    }
    write_json(out/"BLIND_MANIFEST.json",public)
    print(json.dumps({
        "format":public["format"],"n_pairs":valid,"n_candidates":2*valid,
        "private_key_commitment_sha256":commitment,
        "blind_fields_hidden":public["blind_fields_hidden"]
    },indent=2))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("outdir")
    a=ap.parse_args(); prepare(a.config,a.outdir)
if __name__=="__main__": main()
