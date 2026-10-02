from __future__ import annotations
from pathlib import Path
import csv, hashlib, hmac, json, secrets
import numpy as np

def _dump_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")

def prepare_blind(candidates, blind_dir: Path, private_dir: Path, dataset_audit: dict) -> dict:
    blind_dir=Path(blind_dir); private_dir=Path(private_dir)
    geom_dir=blind_dir/"geometries"
    geom_dir.mkdir(parents=True,exist_ok=True)
    private_dir.mkdir(parents=True,exist_ok=True)

    secret=secrets.token_bytes(32)
    commitment=hashlib.sha256(secret).hexdigest()
    public=[]
    private=[]
    stratum_tokens={}

    for c in candidates:
        bid="QG-"+hmac.new(secret,c.real_id.encode(),hashlib.sha256).hexdigest()[:16].upper()
        if c.source_family not in stratum_tokens:
            stratum_tokens[c.source_family]="S-"+hmac.new(
                secret,("stratum:"+c.source_family).encode(),hashlib.sha256
            ).hexdigest()[:10].upper()
        np.save(geom_dir/f"{bid}.npy",c.points)
        public.append({
            "candidate_id":bid,
            "stratum_token":stratum_tokens[c.source_family],
            "geometry_sha256":c.descriptor["geometry_sha256"],
            "n_points":c.descriptor["n_points"],
        })
        private.append({
            "candidate_id":bid,
            "real_id":c.real_id,
            "source_family":c.source_family,
            "source_path":c.source_path,
            "topology_hint":c.topology_hint,
            "constructor":c.constructor,
            "constructor_parameters":c.constructor_parameters,
        })

    manifest={
        "format":"SST-QGI-BLIND-1.0",
        "private_key_commitment_sha256":commitment,
        "source_identity_hidden":True,
        "topology_identity_hidden":True,
        "constructor_parameters_hidden":True,
        "n_candidates":len(public),
        "n_blind_strata":len(stratum_tokens),
        "candidates":public,
    }
    _dump_json(blind_dir/"public_manifest.json",manifest)
    _dump_json(blind_dir/"prepare_public_summary.json",{
        "format":"SST-QGI-PREPARE-1.0",
        "n_candidates":len(public),
        "n_blind_strata":len(stratum_tokens),
        "private_key_commitment_sha256":commitment,
        "source_identity_read":False,
        "topology_identity_read":False,
        "private_mapping_in_blind_output":False,
    })
    # Sanitized audit: counts only, no source paths or names beyond the preregistered built-in count.
    rel_stats=dataset_audit.get("relaxed_ingest",{})
    ext_stats=dataset_audit.get("external_shader_ingest",{})
    _dump_json(blind_dir/"dataset_ingest_audit_public.json",{
        "total_candidates":dataset_audit.get("total_candidates"),
        "files_discovered":int(rel_stats.get("files_discovered",0))+int(ext_stats.get("files_discovered",0)),
        "files_accepted":int(rel_stats.get("files_accepted",0))+int(ext_stats.get("files_accepted",0)),
        "files_rejected":int(rel_stats.get("files_rejected",0))+int(ext_stats.get("files_rejected",0)),
        "files_skipped_metadata":int(rel_stats.get("files_skipped_metadata",0))+int(ext_stats.get("files_skipped_metadata",0)),
        "rejection_reason_counts":{
            "parse_or_geometry_error":len(dataset_audit.get("load_errors",[]))
        },
        "configured_relaxed_root_exists":dataset_audit.get("relaxed_root_exists",False),
    })
    _dump_json(private_dir/"reveal_key.json",{
        "format":"SST-QGI-REVEAL-KEY-1.0",
        "secret_hex":secret.hex(),
        "commitment_sha256":commitment,
        "mapping":private,
        "dataset_audit":dataset_audit,
    })
    return manifest

def verify_private_key(blind_manifest: dict, private_obj: dict) -> bool:
    secret=bytes.fromhex(private_obj["secret_hex"])
    return hashlib.sha256(secret).hexdigest()==blind_manifest["private_key_commitment_sha256"]
