from __future__ import annotations
from pathlib import Path
import json, os, sys, hashlib

class PKLSAError(RuntimeError): pass


def find_e011_output(root: Path) -> Path:
    hits=list(root.glob("01_research/E_pipelines/**/E011-v0.3.0/E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs"))
    if not hits: hits=list(root.glob("**/E011-v0.3.0/E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs"))
    if len(hits)!=1: raise PKLSAError(f"expected exactly one E011-v0.3.0 output, found {len(hits)}")
    return hits[0]


def find_e010_version(root: Path) -> Path:
    hits=list(root.glob("01_research/E_pipelines/**/E010-v0.3.1"))
    if not hits: hits=list(root.glob("**/E010-v0.3.1"))
    hits=[p for p in hits if (p/'pklsa_builder').is_dir()]
    if len(hits)!=1: raise PKLSAError(f"expected exactly one E010-v0.3.1 source tree, found {len(hits)}")
    return hits[0]


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip(): yield json.loads(line)


def seed_contract(root: Path, topology: str) -> dict:
    out=find_e011_output(root)
    idx=json.loads((out/"STATIC_READY_INDEX.json").read_text(encoding="utf-8"))
    row=next((x for x in idx if x.get("topology_id")==topology),None)
    if row is None: raise PKLSAError(f"topology absent from E011 index: {topology}")
    anchors=[x for x in read_jsonl(out/"STATIC_READY_PROVIDER_ANCHORS.jsonl") if x.get("topology_id")==topology]
    return {"index":row,"anchors":anchors,"e011_output":str(out)}


def audit_required_topologies(root: Path) -> dict:
    return {top:seed_contract(root,top) for top in ("5_2","6_1","L6a4")}


def _remap_source_path(path_text: str, workbench: Path) -> Path:
    p=Path(path_text)
    if p.exists(): return p
    norm=path_text.replace('/','\\')
    marker='SST-Workbench\\'
    idx=norm.lower().find(marker.lower())
    if idx>=0:
        rel=norm[idx+len(marker):].replace('\\',os.sep)
        q=workbench/rel
        if q.exists(): return q
    raise PKLSAError(f"source path missing and could not remap under Workbench: {path_text}")


def _sha256_file(path: Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()


def materialize_anchor_geometry(anchor: dict, workbench: Path, n: int=192):
    """Resolve one E011 provider anchor through the exact local E010-v0.3.1 loaders.

    No hand-written format guess is allowed. Raw and E010 geometry hashes are checked before
    A054 resampling/normalization.
    """
    import numpy as np
    from .geometry import resample_closed_curve
    e010=find_e010_version(workbench)
    if str(e010) not in sys.path: sys.path.insert(0,str(e010))
    try:
        from pklsa_builder.io_geometry import load_geometry
        from pklsa_builder.gilbert import find_gilbert_record, sample_gilbert_components
        from pklsa_builder.hashing import geometry_sha256 as e010_geometry_sha256
    except Exception as e:
        raise PKLSAError(f"cannot import exact E010-v0.3.1 loaders: {e}") from e

    loc=anchor.get("source_locator",{}); src=_remap_source_path(loc.get("source_path",""),workbench)
    expected_raw=loc.get('raw_sha256')
    if expected_raw and _sha256_file(src)!=expected_raw:
        raise PKLSAError(f"raw source SHA-256 mismatch for {anchor.get('static_seed_id')}")
    rep=loc.get('representation')
    if rep=='gilbert_ab_record':
        rec=find_gilbert_record(src,anchor.get('topology_id'))
        raw_comps=sample_gilbert_components(rec,n=int(anchor.get('finest_resolution') or 4096))
    else:
        raw_comps=load_geometry(src,representation=rep,fseries_n=int(anchor.get('finest_resolution') or 4096))
    expected_geo=loc.get('geometry_sha256')
    got_geo=e010_geometry_sha256(raw_comps)
    if expected_geo and got_geo!=expected_geo:
        raise PKLSAError(f"PKLSA geometry SHA-256 mismatch for {anchor.get('static_seed_id')}: {got_geo} != {expected_geo}")
    if len(raw_comps)!=1:
        raise PKLSAError(f"component seed {anchor.get('topology_id')} unexpectedly has {len(raw_comps)} components")
    return resample_closed_curve(np.asarray(raw_comps[0],float),n)


def write_upstream_plan(root: Path|None, output: Path):
    payload={"runtime_authority":"local E010-v0.3.1 + E011-v0.3.0; bundled snapshot is documentation only"}
    if root is None or not root.exists():
        payload.update({"status":"PLAN_ONLY_NO_WORKBENCH","required":["5_2 provider anchors","6_1 provider anchors"],
                        "borromean":"L6a4 must NOT be treated as source-native in current snapshot; use analytic generated skeleton stratum"})
    else:
        try:
            aud=audit_required_topologies(root)
            payload["status"]="AUDITED"
            payload["topologies"]={k:{"static_ready":v["index"].get("static_ready"),"static_status":v["index"].get("static_status"),
                "provider_agreement_reasons":v["index"].get("provider_agreement_reasons"),"provider_anchor_seed_ids":v["index"].get("provider_anchor_seed_ids"),
                "anchor_count":len(v["anchors"])} for k,v in aud.items()}
        except Exception as e: payload.update({"status":"INDETERMINATE_PKLSA_AUDIT","error":str(e)})
    output.write_text(json.dumps(payload,indent=2),encoding="utf-8"); return payload
