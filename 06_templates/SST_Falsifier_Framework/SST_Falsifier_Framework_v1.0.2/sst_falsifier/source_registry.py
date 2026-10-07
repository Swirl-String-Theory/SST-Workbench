from __future__ import annotations
from pathlib import Path
import json, os
from typing import Any
from .util import sha256_file, canonical_json_sha256, write_json
from .provenance import inventory


def workbench_root(explicit: str|Path|None=None) -> Path:
    if explicit: return Path(explicit)
    return Path(os.environ.get("SST_WORKBENCH_ROOT",r"C:\workspace\projects\SST-Workbench"))


def _walk_json_for_catalog(obj: Any, catalog_id: str, path=()):
    hits=[]
    if isinstance(obj,dict):
        scalar=" ".join(str(v) for v in obj.values() if isinstance(v,(str,int,float)))
        if catalog_id.casefold() in scalar.casefold(): hits.append((path,obj))
        for k,v in obj.items(): hits.extend(_walk_json_for_catalog(v,catalog_id,path+(str(k),)))
    elif isinstance(obj,list):
        for i,v in enumerate(obj): hits.extend(_walk_json_for_catalog(v,catalog_id,path+(str(i),)))
    return hits


PLACEHOLDERS=("REPLACE_BEFORE_FREEZE","TODO_SCIENCE","<<FILL")
class SourceContractError(RuntimeError): pass

def validate_source_contract(contract: dict[str,Any]) -> list[str]:
    errors=[]; text=json.dumps(contract,ensure_ascii=False)
    for token in PLACEHOLDERS:
        if token in text: errors.append(f"source contract placeholder remains: {token}")
    if contract.get("schema")!="SST-SOURCE-CONTRACT-2": errors.append("source contract schema must be SST-SOURCE-CONTRACT-2")
    if not contract.get("independent_unit"): errors.append("independent_unit is required")
    sources=contract.get("sources",[])
    if not sources and not contract.get("allow_no_external_sources",False): errors.append("at least one source is required unless allow_no_external_sources=true")
    seen=set()
    for i,src in enumerate(sources):
        for field in ("source_id","role","independence_family","version"):
            if not src.get(field): errors.append(f"sources[{i}] missing/empty {field}")
        if not (src.get("relative_path") or src.get("override_path")): errors.append(f"sources[{i}] requires relative_path or override_path")
        sid=src.get("source_id")
        if sid in seen: errors.append(f"duplicate source_id: {sid}")
        seen.add(sid)
    return errors

def assert_source_contract(path: str|Path) -> dict[str,Any]:
    c=json.loads(Path(path).read_text(encoding="utf-8")); errors=validate_source_contract(c)
    if errors: raise SourceContractError("source contract incomplete:\n- "+"\n- ".join(errors))
    return c

def resolve_catalog_hint(root: str|Path, catalog_id: str) -> dict[str,Any]:
    root=Path(root); candidates=[root/"catalog_index.json",root/"family_hierarchy.json"]
    hits=[]
    for p in candidates:
        if not p.exists(): continue
        try:
            obj=json.loads(p.read_text(encoding="utf-8"))
            for path,node in _walk_json_for_catalog(obj,catalog_id):
                hits.append({"registry":str(p),"json_path":"/".join(path),"node":node})
        except Exception as e:
            hits.append({"registry":str(p),"error":f"{type(e).__name__}: {e}"})
    return {"catalog_id":catalog_id,"hits":hits}


def resolve_source_contract(contract_path: str|Path, *, root: str|Path|None=None, out_path: str|Path|None=None):
    contract=json.loads(Path(contract_path).read_text(encoding="utf-8")); wb=workbench_root(root); rows=[]
    for src in contract.get("sources",[]):
        rel=src.get("relative_path"); path=Path(src["override_path"]) if src.get("override_path") else (wb/rel if rel else None)
        row={k:src.get(k) for k in ("source_id","catalog_id","role","independence_family","version")}
        row.update({"path":str(path) if path else None,"exists":bool(path and path.exists())})
        if path and path.is_file(): row["sha256"]=sha256_file(path)
        elif path and path.is_dir():
            inv=inventory(path); row["file_count"]=len(inv); row["directory_manifest_sha256"]=canonical_json_sha256({"files":inv})
        if src.get("catalog_id"): row["registry_hint"]=resolve_catalog_hint(wb,src["catalog_id"])
        rows.append(row)
    payload={"schema":"SST-SOURCE-MANIFEST-2","workbench_root":str(wb),"sources":rows}
    payload["manifest_sha256"]=canonical_json_sha256({"sources":rows})
    if out_path: write_json(out_path,payload)
    return payload
