from __future__ import annotations
from pathlib import Path
import zipfile
from .util import sha256_file, write_json, canonical_json_sha256
from .blind import assert_blind_tree
from .provenance import inventory

DEFAULT_EXCLUDE_PARTS={"private","revealed","reveal_private","__pycache__",".pytest_cache",".venv","build"}


def output_root(project_dir: str|Path,name: str,version: str) -> Path:
    return Path(project_dir)/f"{name}_{version}-outputs"


def make_output_manifest(root: str|Path, out_path: str|Path):
    rows=[r for r in inventory(root,exclude_parts={"private","revealed","reveal_private"}) if r["relpath"]!="OUTPUT_MANIFEST.json"]
    payload={"schema":"SST-OUTPUT-MANIFEST-2","files":rows}
    payload["manifest_sha256"]=canonical_json_sha256({"files":rows})
    write_json(out_path,payload); return payload


def deterministic_zip(root: str|Path, zip_path: str|Path, *, exclude_parts=DEFAULT_EXCLUDE_PARTS):
    root=Path(root); zpath=Path(zip_path); zpath.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(zpath,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(root.rglob("*")):
            if not p.is_file(): continue
            rel=p.relative_to(root)
            if any(part.casefold() in {x.casefold() for x in exclude_parts} for part in rel.parts): continue
            zi=zipfile.ZipInfo(rel.as_posix(),date_time=(1980,1,1,0,0,0))
            zi.compress_type=zipfile.ZIP_DEFLATED; zi.external_attr=(0o100644 & 0xFFFF)<<16
            z.writestr(zi,p.read_bytes())
    return {"zip":str(zpath),"sha256":sha256_file(zpath),"size":zpath.stat().st_size}


def pack_blind(instance_root: str|Path, output_root_path: str|Path, zip_path: str|Path):
    root=Path(instance_root)
    assert_blind_tree(root)
    make_output_manifest(output_root_path,Path(output_root_path)/"OUTPUT_MANIFEST.json")
    return deterministic_zip(output_root_path,zip_path)


def pack_revealed(output_root_path: str|Path, zip_path: str|Path):
    make_output_manifest(output_root_path,Path(output_root_path)/"OUTPUT_MANIFEST.json")
    return deterministic_zip(output_root_path,zip_path,exclude_parts={"__pycache__",".pytest_cache",".venv","build"})
