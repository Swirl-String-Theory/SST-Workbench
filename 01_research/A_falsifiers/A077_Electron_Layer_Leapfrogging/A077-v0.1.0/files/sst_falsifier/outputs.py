from __future__ import annotations
from pathlib import Path
import json
import zipfile
from .util import sha256_file, write_json, canonical_json_sha256, canonical_json_bytes
from .blind import assert_blind_tree
from .provenance import inventory

DEFAULT_EXCLUDE_PARTS={"private","revealed","reveal_private","__pycache__",".pytest_cache",".venv","build"}
_OUTPUT_MANIFEST_EXCLUDES={"private","revealed","reveal_private"}


_SCIENCE_INVENTORY_EXCLUDE = {"report", "revealed", "private", "reveal_private"}
_SCIENCE_TOPLEVEL_EXCLUDE = {
    "OUTPUT_MANIFEST.json", "SCIENCE_EVIDENCE_MANIFEST.json", "REVEAL_DECISION.json",
    "REVEAL_VERIFICATION.json", "GATE_LEDGER_REVEALED.json", "RUN_SUMMARY_REVEALED.json",
    "REPORT_RENDER_BLIND.json", "REPORT_RENDER_REVEALED.json",
}


def _science_evidence_inventory(root: str | Path) -> list[dict]:
    """Stable blind evidence before TeX, PDF and reveal-derived artifacts.

    A dedicated digest avoids circular dependencies between AUTO_RESULTS.tex and
    OUTPUT_MANIFEST.json; it never replaces the final full-tree output manifest.
    """
    rows = inventory(root, exclude_parts=_SCIENCE_INVENTORY_EXCLUDE)
    return [r for r in rows if r["relpath"] not in _SCIENCE_TOPLEVEL_EXCLUDE]


def make_science_evidence_manifest(root: str | Path, path: str | Path) -> dict:
    """Create once, before generating report artifacts. Never mutate this ledger."""
    rows = _science_evidence_inventory(root)
    payload = {"schema": "SST-SCIENCE-EVIDENCE-MANIFEST-1", "files": rows,
               "manifest_sha256": canonical_json_sha256({"files": rows})}
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as fh:
        fh.write(canonical_json_bytes(payload))
    return payload


def verify_science_evidence_manifest(root: str | Path, path: str | Path) -> tuple[bool, dict]:
    target = Path(path)
    if not target.is_file():
        return False, {"reason": "missing immutable science evidence manifest"}
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, {"reason": "unreadable science evidence manifest", "error": str(exc)}
    expected = payload.get("files")
    if payload.get("schema") != "SST-SCIENCE-EVIDENCE-MANIFEST-1" or not isinstance(expected, list):
        return False, {"reason": "invalid science evidence manifest schema"}
    computed = canonical_json_sha256({"files": expected})
    if computed != payload.get("manifest_sha256"):
        return False, {"reason": "science evidence manifest self-hash mismatch"}
    actual = _science_evidence_inventory(root)
    if actual != expected:
        return False, {"reason": "science evidence changed since blind run", "actual": actual, "expected": expected}
    return True, {"reason": "immutable science evidence verified", "manifest_sha256": computed}


def output_root(project_dir: str|Path,name: str,version: str) -> Path:
    return Path(project_dir)/f"{name}_{version}-outputs"


def _output_inventory(root: str|Path):
    return [
        r for r in inventory(root,exclude_parts=_OUTPUT_MANIFEST_EXCLUDES)
        if r["relpath"]!="OUTPUT_MANIFEST.json"
    ]


def make_output_manifest(root: str|Path, out_path: str|Path):
    rows=_output_inventory(root)
    payload={"schema":"SST-OUTPUT-MANIFEST-2","files":rows}
    payload["manifest_sha256"]=canonical_json_sha256({"files":rows})
    write_json(out_path,payload); return payload


def verify_output_manifest(root: str|Path, manifest_path: str|Path):
    """Verify the blind output tree against its frozen-at-run manifest.

    This is intentionally strict: the manifest's own digest must match and the current
    non-private/non-revealed inventory must be byte-for-byte equivalent to the listed
    relpath/size/SHA-256 rows.  Reveal preflight uses this before trusting gate state.
    """
    root=Path(root); path=Path(manifest_path)
    detail={"schema":"SST-OUTPUT-MANIFEST-VERIFY-1","ok":False,"manifest":str(path)}
    if not path.is_file():
        detail["reason"]="OUTPUT_MANIFEST.json is missing"
        return False,detail
    try:
        payload=json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        detail["reason"]=f"OUTPUT_MANIFEST.json is unreadable: {type(exc).__name__}: {exc}"
        return False,detail
    if payload.get("schema")!="SST-OUTPUT-MANIFEST-2":
        detail["reason"]=f"unexpected output manifest schema: {payload.get('schema')!r}"
        return False,detail
    rows=payload.get("files")
    if not isinstance(rows,list):
        detail["reason"]="output manifest files is not a list"
        return False,detail
    computed_manifest=canonical_json_sha256({"files":rows})
    stored_manifest=payload.get("manifest_sha256")
    detail.update({"stored_manifest_sha256":stored_manifest,"computed_manifest_sha256":computed_manifest})
    if stored_manifest!=computed_manifest:
        detail["reason"]="output manifest self-hash mismatch"
        return False,detail
    current=_output_inventory(root)
    if current!=rows:
        expected={r.get("relpath"):r for r in rows if isinstance(r,dict)}
        actual={r.get("relpath"):r for r in current if isinstance(r,dict)}
        detail["missing"]=sorted(set(expected)-set(actual))
        detail["unexpected"]=sorted(set(actual)-set(expected))
        detail["changed"]=sorted(
            p for p in set(expected)&set(actual) if expected[p]!=actual[p]
        )
        detail["reason"]="output tree does not match OUTPUT_MANIFEST.json"
        return False,detail
    detail["ok"]=True; detail["reason"]="output manifest and current output tree match"
    return True,detail


def deterministic_zip(root: str|Path, zip_path: str|Path, *, exclude_parts=DEFAULT_EXCLUDE_PARTS):
    root=Path(root); zpath=Path(zip_path); zpath.parent.mkdir(parents=True,exist_ok=True)
    excluded_cf={x.casefold() for x in exclude_parts}
    with zipfile.ZipFile(zpath,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(root.rglob("*")):
            if not p.is_file(): continue
            rel=p.relative_to(root)
            if any(part.casefold() in excluded_cf for part in rel.parts): continue
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
