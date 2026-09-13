"""Copy-on-write modal-phase version trees and hash parent artefacts (P0)."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
EXCLUDE_DIR_NAMES = {".venv", "outputs", "private_reveal_keys", "__pycache__", ".pytest_cache"}
COPIES = [
    {
        "id": "A034",
        "parent": WB / "01_research/A_falsifiers/A034_qhp_stability_landscape/A034-v0.2.1",
        "dest": WB / "01_research/A_falsifiers/A034_qhp_stability_landscape/A034-v0.2.2",
        "parent_version": "v0.2.1",
        "new_version": "v0.2.2",
        "cert": WB / "01_research/A_falsifiers/A034_qhp_stability_landscape/A034-v0.2.1/outputs/basic/paper_upgrade/certificate.json",
    },
    {
        "id": "A037",
        "parent": WB / "01_research/A_falsifiers/A037_chirality_helicity_transport_polarity/A037-v0.3.1",
        "dest": WB / "01_research/A_falsifiers/A037_chirality_helicity_transport_polarity/A037-v0.3.2",
        "parent_version": "v0.3.1",
        "new_version": "v0.3.2",
        "cert": WB / "01_research/A_falsifiers/A037_chirality_helicity_transport_polarity/A037-v0.3.1/outputs/basic/paper_upgrade/certificate.json",
    },
    {
        "id": "A038",
        "parent": WB / "01_research/A_falsifiers/A038_trefoil_dynamic_seed_qualification/A038-v0.4.0",
        "dest": WB / "01_research/A_falsifiers/A038_trefoil_dynamic_seed_qualification/A038-v0.5.0",
        "parent_version": "v0.4.0",
        "new_version": "v0.5.0",
        "cert": WB / "01_research/A_falsifiers/A038_trefoil_dynamic_seed_qualification/A038-v0.4.0/outputs/basic/paper_upgrade/upstream_certs.json",
    },
    {
        "id": "A029",
        "parent": WB / "01_research/A_falsifiers/A029_finite_core_axial_toroidal_phase_delay/A029-v0.2.0",
        "dest": WB / "01_research/A_falsifiers/A029_finite_core_axial_toroidal_phase_delay/A029-v0.3.0",
        "parent_version": "v0.2.0",
        "new_version": "v0.3.0",
        "cert": None,
    },
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_tree(root: Path) -> dict:
    files = []
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        parts = set(Path(rel).parts)
        if parts & EXCLUDE_DIR_NAMES:
            continue
        if "(1)" in p.name:
            continue
        digest = sha256_file(p)
        files.append({"path": rel, "sha256": digest, "bytes": p.stat().st_size})
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(digest.encode("ascii"))
    return {"tree_sha256": h.hexdigest(), "n_files": len(files), "files": files}


def should_skip(src_root: Path, path: Path) -> bool:
    rel_parts = set(path.relative_to(src_root).parts)
    if rel_parts & EXCLUDE_DIR_NAMES:
        return True
    if "(1)" in path.name:
        return True
    return False


def copy_tree(src: Path, dest: Path) -> int:
    n = 0
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for item in src.rglob("*"):
        if should_skip(src, item):
            continue
        rel = item.relative_to(src)
        target = dest / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            n += 1
    return n


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def provenance_stubs(dest: Path, spec: dict, parent_hashes: dict) -> None:
    write_json(
        dest / "MANIFEST_PRE.json",
        {
            "schema": "SST-MANIFEST-PRE-1.0",
            "family": spec["id"],
            "version": spec["new_version"],
            "parent_version": spec["parent_version"],
            "copied_from": spec["parent"].relative_to(WB).as_posix(),
            "parent_tree_sha256": parent_hashes["tree_sha256"],
            "parent_certificate_sha256": parent_hashes.get("cert_sha256"),
            "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "programme": "modal_phase_first_release",
        },
    )
    ledger = dest / "PATCH_LEDGER.jsonl"
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "family": spec["id"],
        "from": spec["parent_version"],
        "to": spec["new_version"],
        "kind": "copy_on_write",
        "rationale": "Modal-phase P0–P2 additive adapters; parent scientific gates frozen.",
        "parent_tree_sha256": parent_hashes["tree_sha256"],
    }
    ledger.write_text(json.dumps(entry, sort_keys=True) + "\n", encoding="utf-8")
    write_json(
        dest / "THRESHOLDS_FROZEN.json",
        {
            "schema": "SST-THRESHOLDS-FROZEN-1.0",
            "family": spec["id"],
            "version": spec["new_version"],
            "parent_scientific_thresholds": "frozen",
            "not_applicable": spec["id"] != "A029",
            "note": "A029 residual thresholds live here after P2 freeze; other packs have no new scientific thresholds.",
        },
    )
    write_json(
        dest / "BLIND_SPLIT.json",
        {
            "schema": "SST-BLIND-SPLIT-1.0",
            "family": spec["id"],
            "version": spec["new_version"],
            "not_applicable": spec["id"] != "A029",
            "status": "pending_p2" if spec["id"] == "A029" else "not_applicable",
        },
    )
    write_json(
        dest / "rollback" / "PARENT_VERSION.json",
        {
            "family": spec["id"],
            "parent_version": spec["parent_version"],
            "parent_directory": spec["parent"].relative_to(WB).as_posix(),
            "parent_tree_sha256": parent_hashes["tree_sha256"],
            "parent_certificate_path": None
            if spec["cert"] is None
            else spec["cert"].relative_to(WB).as_posix(),
            "parent_certificate_sha256": parent_hashes.get("cert_sha256"),
        },
    )


def main() -> int:
    hashes = {}
    overnight = WB / "10_docs/migration/paper_upgrade_run_log_20260911_225901.md"
    hashes["overnight_log_sha256"] = sha256_file(overnight) if overnight.is_file() else None
    for spec in COPIES:
        tree = sha256_tree(spec["parent"])
        rec = {"tree_sha256": tree["tree_sha256"], "n_files": tree["n_files"]}
        if spec["cert"] is not None and spec["cert"].is_file():
            rec["cert_sha256"] = sha256_file(spec["cert"])
            rec["cert_path"] = spec["cert"].relative_to(WB).as_posix()
        else:
            rec["cert_sha256"] = None
        hashes[spec["id"]] = rec
        n = copy_tree(spec["parent"], spec["dest"])
        provenance_stubs(spec["dest"], spec, rec)
        print(f"copied {spec['id']} {spec['parent_version']} -> {spec['new_version']} files={n}")
    write_json(WB / "10_docs/migration/PARENT_HASHES_modal_phase_20260913.json", hashes)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(main())
