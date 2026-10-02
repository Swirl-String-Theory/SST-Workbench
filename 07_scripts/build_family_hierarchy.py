"""Build 10_docs/registry/family_hierarchy.json for catalog naming + references.

Merges FAMILY.yaml metadata with on-disk version directories and output artifacts
so new falsifiers can copy the correct path / version / zip naming patterns.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WB = Path(__file__).resolve().parents[1]
OUT = WB / "10_docs" / "registry" / "family_hierarchy.json"

# Reuse the flat FAMILY.yaml parser from the catalog index builder.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_catalog_index as bci  # noqa: E402

VERSION_DIR_RE = re.compile(r"^[A-Z]\d{3}-v", re.I)
OUTPUT_ZIP_RE = re.compile(r"(?i).+_outputs\.zip(?:\.sha256)?$")
OUTPUT_DIR_RE = re.compile(r"(?i)^(.+_outputs|outputs(_.*)?|.*-outputs.*)$")

NAMING = {
    "family_dir": "{catalog_id}_{slug}",
    "version_dir": "{catalog_id}-{version_id}",
    "version_id": "vMAJOR.MINOR.PATCH  (dots preferred; legacy underscore forms exist)",
    "outputs_zip": "{output_prefix}_{version_id}_outputs.zip",
    "outputs_sha256": "{output_prefix}_{version_id}_outputs.zip.sha256",
    "family_yaml": "FAMILY.yaml  (required at family root)",
    "project_json": "project.json  (required inside each version dir)",
    "examples": {
        "family_dir": "A011_maxwell_1_kinetic_energy",
        "version_dir": "A011-v0.3.1",
        "outputs_zip": "1_Maxwell_SST_Kinetic_Falsifier_v0.3.1_outputs.zip",
        "resolve": "sst_workbench_paths.resolve_family('A011')",
    },
    "notes": [
        "Version directories use catalog-id short names (A011-v0.3.1), not legacy pack folder names.",
        "output_prefix is stable across versions; only the version token changes in zip names.",
        "Do not recreate root-level legacy folders (SST_Maxwell/, …); use catalog paths.",
        "Regenerate this file with: python 07_scripts/build_family_hierarchy.py",
    ],
}


def _is_reparse_point(path: Path) -> bool:
    """True for Windows junctions/symlinks — do not descend into them."""
    try:
        if path.is_symlink():
            return True
    except OSError:
        return True
    try:
        import os

        attrs = getattr(os.lstat(path), "st_file_attributes", 0)
        return bool(attrs & 0x400)  # FILE_ATTRIBUTE_REPARSE_POINT
    except OSError:
        return False


def _safe_iterdir(path: Path) -> list[Path]:
    try:
        return sorted(path.iterdir(), key=lambda p: p.name.lower())
    except OSError:
        return []


def expected_outputs_zip(output_prefix: str, version_id: str) -> str | None:
    prefix = (output_prefix or "").strip()
    ver = (version_id or "").strip()
    if not prefix or not ver:
        return None
    return f"{prefix}_{ver}_outputs.zip"


def collect_version_artifacts(version_dir: Path) -> dict[str, Any]:
    outputs_zips: list[str] = []
    outputs_sha256: list[str] = []
    output_dirs: list[str] = []
    has_project_json = False
    top_files: list[str] = []

    for child in _safe_iterdir(version_dir):
        if child.is_file():
            name = child.name
            if name == "project.json":
                has_project_json = True
            if OUTPUT_ZIP_RE.match(name):
                if name.lower().endswith(".sha256"):
                    outputs_sha256.append(name)
                else:
                    outputs_zips.append(name)
            if name.endswith((".zip", ".sha256", ".json", ".md", ".yaml", ".yml", ".cmd", ".ps1")):
                top_files.append(name)
            continue
        if child.is_dir() and not _is_reparse_point(child) and OUTPUT_DIR_RE.match(child.name):
            output_dirs.append(child.name)

    return {
        "has_project_json": has_project_json,
        "outputs_zips": sorted(outputs_zips),
        "outputs_sha256": sorted(outputs_sha256),
        "output_dirs": sorted(output_dirs),
        "top_level_meta_files": sorted(set(top_files)),
    }


def scan_family_disk(
    family_path: Path,
    meta: dict[str, Any],
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root = root or WB
    declared = {v.get("id", ""): v for v in meta.get("versions") or []}
    versions_out: dict[str, Any] = {}
    undeclared: list[str] = []

    declared_dirs = {
        str(row.get("directory") or "")
        for row in declared.values()
        if isinstance(row, dict)
    }
    for child in _safe_iterdir(family_path):
        if not child.is_dir() or _is_reparse_point(child):
            continue
        name = child.name
        if not (VERSION_DIR_RE.match(name) or name in declared_dirs):
            continue

        version_id = None
        for vid, row in declared.items():
            if row.get("directory") == name:
                version_id = vid
                break
        if version_id is None:
            # Infer from A011-v0.3.1
            version_id = name.split("-", 1)[1] if "-" in name else name
            undeclared.append(name)

        arts = collect_version_artifacts(child)
        prefix = meta.get("output_prefix") or ""
        expected = expected_outputs_zip(prefix, version_id or "")
        try:
            rel = child.relative_to(root).as_posix()
        except ValueError:
            rel = child.as_posix()
        versions_out[version_id or name] = {
            "directory": name,
            "path": rel,
            "declared": version_id in declared,
            "expected_outputs_zip": expected,
            "expected_zip_present": bool(expected and expected in arts["outputs_zips"]),
            **arts,
        }

    # Declared but missing on disk
    missing: list[dict[str, str]] = []
    for vid, row in declared.items():
        if vid not in versions_out:
            missing.append(
                {
                    "id": vid,
                    "directory": str(row.get("directory") or ""),
                }
            )

    other_dirs = [
        p.name
        for p in _safe_iterdir(family_path)
        if p.is_dir()
        and not _is_reparse_point(p)
        and p.name not in {v["directory"] for v in versions_out.values()}
    ]

    return {
        "versions_on_disk": dict(
            sorted(
                versions_out.items(),
                key=lambda kv: kv[0],
            )
        ),
        "missing_declared_versions": missing,
        "undeclared_version_dirs": sorted(undeclared),
        "other_dirs": sorted(other_dirs),
    }


def next_catalog_ids(by_letter: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Suggest the next free catalog id per letter bucket (A/B/C/…)."""
    out: dict[str, str] = {}
    for letter, families in by_letter.items():
        nums = []
        for cid in families:
            m = re.match(r"^([A-Z])(\d+)$", cid)
            if m:
                nums.append(int(m.group(2)))
        if not nums:
            prefix = letter[0].upper() if letter else "A"
            out[letter] = f"{prefix}001"
            continue
        first = next(iter(families))
        m = re.match(r"^([A-Z])", first)
        prefix = m.group(1) if m else letter[:1].upper() or "A"
        out[letter] = f"{prefix}{max(nums) + 1:03d}"
    return out


def build(root: Path | None = None) -> dict[str, Any]:
    root = root or WB
    # Temporarily point bci at the chosen root for tests.
    old_wb = bci.WB
    bci.WB = root
    try:
        entries = [bci.parse_family(p) for p in bci.family_files()]
    finally:
        bci.WB = old_wb

    hierarchy: dict[str, Any] = {}
    flat: dict[str, Any] = {}

    for meta in entries:
        domain = meta.get("domain") or "unknown"
        letter = meta.get("letter") or "unknown"
        cid = meta.get("catalog_id") or "UNKNOWN"
        family_path = root / meta["path"]
        disk = (
            scan_family_disk(family_path, meta, root=root)
            if family_path.is_dir()
            else {
                "versions_on_disk": {},
                "missing_declared_versions": [
                    {
                        "id": v.get("id", ""),
                        "directory": str(v.get("directory") or ""),
                    }
                    for v in meta.get("versions") or []
                ],
                "undeclared_version_dirs": [],
                "other_dirs": [],
            }
        )

        node = {
            "catalog_id": cid,
            "slug": meta.get("slug", ""),
            "name": meta.get("name", ""),
            "kind": meta.get("kind", ""),
            "status": meta.get("status", ""),
            "domain": domain,
            "letter": letter,
            "path": meta.get("path", ""),
            "latest": meta.get("latest", ""),
            "output_prefix": meta.get("output_prefix", ""),
            "legacy_paths": meta.get("legacy_paths") or [],
            "declared_versions": meta.get("versions") or [],
            **disk,
        }
        hierarchy.setdefault(domain, {}).setdefault(letter, {})[cid] = node
        flat[cid] = {
            "path": node["path"],
            "domain": domain,
            "letter": letter,
            "output_prefix": node["output_prefix"],
            "latest": node["latest"],
            "version_dirs": [
                v["directory"] for v in node["versions_on_disk"].values()
            ],
            "outputs_zips": [
                z
                for v in node["versions_on_disk"].values()
                for z in v.get("outputs_zips") or []
            ],
        }

    by_letter_counts = {
        letter: families
        for domain in hierarchy.values()
        for letter, families in domain.items()
    }

    return {
        "schema": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "root": str(root.resolve()),
        "family_count": len(entries),
        "version_count_declared": sum(len(e.get("versions") or []) for e in entries),
        "version_count_on_disk": sum(
            len(n.get("versions_on_disk") or {})
            for domain in hierarchy.values()
            for letter in domain.values()
            for n in letter.values()
        ),
        "naming": NAMING,
        "next_catalog_ids": next_catalog_ids(by_letter_counts),
        "hierarchy": hierarchy,
        "by_catalog_id": flat,
        "note": (
            "Use naming + by_catalog_id for quick references; hierarchy mirrors "
            "domain/letter/family/version on disk including outputs zip names."
        ),
    }


def write(payload: dict[str, Any], out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write family_hierarchy.json")
    parser.add_argument("--root", type=Path, default=WB)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)
    payload = build(args.root)
    written = write(payload, args.out)
    try:
        shown = written.relative_to(WB)
    except ValueError:
        shown = written
    print(
        f"Wrote {shown} "
        f"({payload['family_count']} families, "
        f"{payload['version_count_on_disk']} version dirs on disk)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
