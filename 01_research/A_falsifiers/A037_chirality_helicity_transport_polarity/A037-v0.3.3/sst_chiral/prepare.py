from __future__ import annotations
import argparse, json, re, secrets
from pathlib import Path
from .config import load_config
from .geometry import (
    discover_curves, load_geometry, normalize_geometry, resample_geometry,
    parity_mirror_physical, ds_cv_geometry, save_geometry_npz,
)
from .util import write_json, canonical_json, sha256_bytes, sha256_file, random_token, private_key_path


def _priority_paths(paths:list[Path],patterns:list[str])->list[Path]:
    rng=secrets.SystemRandom(); remaining=list(paths); out=[]
    for pat in patterns:
        rx=re.compile(pat,re.I); matches=[p for p in remaining if rx.search(p.name)]; rng.shuffle(matches)
        if matches:
            chosen=matches[0]; out.append(chosen); remaining=[p for p in remaining if p!=chosen]
    rng.shuffle(remaining); out.extend(remaining); return out


def prepare(config_path:str,outdir:str):
    cfg=load_config(config_path); out=Path(outdir); blind_dir=out/"blind_inputs"; blind_dir.mkdir(parents=True,exist_ok=True)
    dataset=Path(cfg.get("dataset",r"..\..\KnotPlot\knots\final")); paths=discover_curves(dataset)
    if not paths: raise RuntimeError(f"No supported coordinate files under {dataset}")
    paths=_priority_paths(paths,list(cfg.get("target_name_patterns",[])))
    max_pairs=int(cfg.get("max_pairs",8)); target_n=int(max(cfg.get("resolutions",[96]))); min_per=int(cfg.get("min_points_per_component",24))
    key_id=random_token(12)
    private={"format":"SST-CHIRALITY-PRIVATE-2.0","key_id":key_id,"nonce":random_token(32),"dataset":str(dataset.resolve()),"pairs":[],"parse_errors":[]}
    public_pairs=[]; valid=0
    for p in paths:
        if max_pairs>0 and valid>=max_pairs: break
        try:
            comps,pmeta=load_geometry(p,gap_factor=float(cfg.get("component_gap_factor",6.0)),
                                      allow_equal_torus_split=bool(cfg.get("allow_equal_torus_split",True)),
                                      reject_ambiguous_links=bool(cfg.get("reject_ambiguous_links",True)))
            comps,nmeta=normalize_geometry(comps); comps=resample_geometry(comps,target_n,min_per); comps,_=normalize_geometry(comps)
            mirror=parity_mirror_physical(comps,axis=int(cfg.get("mirror_axis",0))); mirror,_=normalize_geometry(mirror)
            if ds_cv_geometry(comps)>float(cfg.get("max_ds_cv_prepare",0.35)) or ds_cv_geometry(mirror)>float(cfg.get("max_ds_cv_prepare",0.35)):
                raise ValueError("ds_CV prepare gate failed")
        except Exception as e:
            private["parse_errors"].append({"source_path":str(p),"error":repr(e)}); continue
        valid+=1; pair_id=f"P{valid:04d}"; roleA="original" if secrets.randbelow(2)==0 else "mirror"; roleB="mirror" if roleA=="original" else "original"
        tokenA=random_token(10); tokenB=random_token(10); fileA=f"{pair_id}_{tokenA}.npz"; fileB=f"{pair_id}_{tokenB}.npz"
        geomA=comps if roleA=="original" else mirror; geomB=mirror if roleB=="mirror" else comps
        save_geometry_npz(blind_dir/fileA,geomA); save_geometry_npz(blind_dir/fileB,geomB)
        public_pairs.append({"pair_id":pair_id,"variants":{"A":{"file":fileA,"sha256":sha256_file(blind_dir/fileA)},"B":{"file":fileB,"sha256":sha256_file(blind_dir/fileB)}}})
        private["pairs"].append({"pair_id":pair_id,"source_name":p.name,"source_path":str(p.resolve()),"component_parse":pmeta,
                                 "normalization":nmeta,"n_components":len(comps),"component_points":[len(c) for c in comps],"role":{"A":roleA,"B":roleB}})
    if valid==0: raise RuntimeError("No valid geometries after parsing/component gates")
    commitment=sha256_bytes(canonical_json(private)); keyfile=private_key_path(key_id); keyfile.parent.mkdir(parents=True,exist_ok=True); write_json(keyfile,private)
    public={"format":"SST-CHIRALITY-BLIND-MANIFEST-2.0","n_pairs":valid,"n_candidates":2*valid,"private_mapping_commitment_sha256":commitment,
            "private_key_id":key_id,"private_mapping_present_in_output":False,
            "blind_fields_hidden":["source_name","source_path","knot_family","original_vs_parity_mirror","component_parse_provenance"],"pairs":public_pairs}
    write_json(out/"BLIND_MANIFEST.json",public)
    print(json.dumps({"format":public["format"],"n_pairs":valid,"n_candidates":2*valid,"private_mapping_commitment_sha256":commitment,
                      "private_key_id":key_id,"private_mapping_present_in_output":False,"blind_fields_hidden":public["blind_fields_hidden"]},indent=2))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("config"); ap.add_argument("outdir"); a=ap.parse_args(); prepare(a.config,a.outdir)
if __name__=="__main__": main()
