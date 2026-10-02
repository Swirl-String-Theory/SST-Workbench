from __future__ import annotations
import hashlib
import json
import shutil
from pathlib import Path
import numpy as np
from .io import discover_curves, sha256_file, curve_metadata


def canonical_hash(obj)->str:
    raw=json.dumps(obj,sort_keys=True,separators=(",",":"),default=str).encode()
    return hashlib.sha256(raw).hexdigest()


def prepare(dataset: str|Path, out: str|Path, config: dict) -> dict:
    root=Path(dataset).expanduser().resolve(); out=Path(out).resolve(); blind_dir=out/"blinded_inputs"
    out.mkdir(parents=True,exist_ok=True); blind_dir.mkdir(parents=True,exist_ok=True)
    curves,skipped=discover_curves(root)
    if not curves: raise RuntimeError(f"no usable curve files found under {root}")
    private=[]; public=[]
    used=set()
    for path,p in curves:
        file_sha=sha256_file(path); sid="sample_"+hashlib.sha256((file_sha+str(len(p))).encode()).hexdigest()[:12]
        k=1; base=sid
        while sid in used: k+=1; sid=f"{base}_{k}"
        used.add(sid); np.save(blind_dir/f"{sid}.npy",p)
        meta=curve_metadata(p); public.append({"sample_id":sid,"sha256":file_sha,**meta})
        private.append({"sample_id":sid,"source_rel":str(path.relative_to(root)),"source_abs":str(path),"sha256":file_sha})
    frozen={"protocol_version":"KJ-SST-v0.1.0","config":config,"config_sha256":canonical_hash(config),"n_samples":len(public)}
    (out/"frozen_protocol.json").write_text(json.dumps(frozen,indent=2),encoding="utf-8")
    (out/"blind_manifest.public.json").write_text(json.dumps(public,indent=2),encoding="utf-8")
    (out/"blind_manifest.private.json").write_text(json.dumps(private,indent=2),encoding="utf-8")
    (out/"skipped_files.json").write_text(json.dumps(skipped,indent=2),encoding="utf-8")
    return frozen
