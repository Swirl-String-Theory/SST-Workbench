from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import itertools, os
import numpy as np
from .geometry import (
    SUPPORTED_EXTENSIONS, track_trefoil, classic_trefoil, load_points,
    resample_closed, descriptors
)

@dataclass
class Candidate:
    real_id: str
    source_family: str
    source_path: str
    topology_hint: str
    constructor: str
    constructor_parameters: dict
    points: np.ndarray
    descriptor: dict

def _resolve_env_or_config(env_name: str, configured: str | None) -> Path | None:
    raw=os.environ.get(env_name) or configured
    if not raw:
        return None
    return Path(raw).expanduser().resolve()

def generate_shader_family(cfg: dict) -> list[Candidate]:
    s=cfg["dataset"]["shader_derived"]
    n_raw=int(s.get("n_raw",512))
    n_resample=int(cfg["dataset"].get("resample_n",512))
    out=[]
    for i,(R,a,b) in enumerate(itertools.product(s["baseR"], s["bulge_R"], s["z_weave"])):
        pts=track_trefoil(n=n_raw, baseR=float(R), bulge_R=float(a), z_weave=float(b))
        pts=resample_closed(pts,n_resample)
        params={"baseR":float(R),"bulge_R":float(a),"z_weave":float(b),"p":2,"q":3}
        out.append(Candidate(
            real_id=f"shader_builtin_{i:04d}",
            source_family="shader_derived",
            source_path="builtin:track_trefoil_compatibility_sweep",
            topology_hint="3_1_trefoil",
            constructor="track_trefoil",
            constructor_parameters=params,
            points=pts,
            descriptor=descriptors(pts),
        ))
    return out

def _looks_like_metadata(path: Path) -> bool:
    name=path.name.lower()
    metadata_tokens=(
        ".metrics.json","manifest","inventory","summary","report","config",
        "validation","results","readme","metadata","provenance"
    )
    return any(tok in name for tok in metadata_tokens)

def _discover_files(root: Path, max_files: int) -> tuple[list[Path], int]:
    files=[]
    skipped_metadata=0
    if not root or not root.exists():
        return files,skipped_metadata
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if _looks_like_metadata(p):
            skipped_metadata += 1
            continue
        files.append(p)
        if len(files)>=max_files:
            break
    return files,skipped_metadata

def import_centerlines(root: Path | None, source_family: str, max_files: int, resample_n: int) -> tuple[list[Candidate], list[dict], dict]:
    out=[]; errors=[]
    if root is None or not root.exists():
        return out, errors, {
            "files_discovered":0,
            "files_accepted":0,
            "files_rejected":0,
            "files_skipped_metadata":0,
        }
    discovered,skipped_metadata=_discover_files(root,max_files)
    for i,p in enumerate(discovered):
        try:
            pts=resample_closed(load_points(p),resample_n)
            out.append(Candidate(
                real_id=f"{source_family}_{i:04d}",
                source_family=source_family,
                source_path=str(p),
                topology_hint="unknown_from_filename",
                constructor="imported_centerline",
                constructor_parameters={},
                points=pts,
                descriptor=descriptors(pts),
            ))
        except Exception as exc:
            errors.append({"path":str(p),"error":f"{type(exc).__name__}: {exc}"})
    stats={
        "files_discovered":len(discovered),
        "files_accepted":len(out),
        "files_rejected":len(errors),
        "files_skipped_metadata":skipped_metadata,
    }
    return out,errors,stats

def collect_candidates(cfg: dict) -> tuple[list[Candidate], dict]:
    ds=cfg["dataset"]
    resample_n=int(ds.get("resample_n",512))
    candidates=generate_shader_family(cfg)
    audit={
        "builtin_shader_candidates":len(candidates),
        "external_shader_candidates":0,
        "relaxed_candidates":0,
        "load_errors":[],
    }

    external_shader=_resolve_env_or_config(
        "SST_SHADER_DERIVED_ROOT",
        ds.get("external_shader_root")
    )
    if external_shader:
        ext,err,stats=import_centerlines(
            external_shader,"shader_derived_external",
            int(ds.get("max_external_shader_files",256)),resample_n
        )
        candidates.extend(ext)
        audit["external_shader_candidates"]=len(ext)
        audit["external_shader_root"]=str(external_shader)
        audit["external_shader_ingest"]=stats
        audit["load_errors"].extend(err)

    relaxed=_resolve_env_or_config(
        "SST_RELAXED_KNOT_ROOT",
        ds.get("relaxed_root")
    )
    if relaxed:
        rel,err,stats=import_centerlines(
            relaxed,"relaxed",
            int(ds.get("max_relaxed_files",256)),resample_n
        )
        candidates.extend(rel)
        audit["relaxed_candidates"]=len(rel)
        audit["relaxed_root"]=str(relaxed)
        audit["relaxed_root_exists"]=relaxed.exists()
        audit["relaxed_ingest"]=stats
        audit["load_errors"].extend(err)
    else:
        audit["relaxed_root_exists"]=False

    if bool(ds.get("include_classic_control",True)):
        pts=resample_closed(classic_trefoil(512),resample_n)
        candidates.append(Candidate(
            real_id="control_classic_trefoil",
            source_family="control",
            source_path="builtin:classic_trefoil",
            topology_hint="3_1_trefoil_control",
            constructor="classic_trefoil",
            constructor_parameters={},
            points=pts,
            descriptor=descriptors(pts),
        ))
    audit["total_candidates"]=len(candidates)
    return candidates,audit
