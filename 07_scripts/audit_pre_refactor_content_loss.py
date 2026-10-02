"""Compare a pre-refactor git tree to HEAD and the freeze disk manifest.

Reports true content loss: old paths that do not land on a HEAD path after
path_map remapping, and whose blob is also absent from HEAD.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import dataset_integrity as di  # noqa: E402
from seed_path_map import load_path_map  # noqa: E402

FREEZE_COMMIT = "816505699e62f84cce2d4cc67ecb52c6e39c9d3c"
SEPT4_COMMIT = "e06410b84"
PATH_MAP = WB / "10_docs" / "migration" / "path_map.csv"
MANIFEST = WB / "10_docs" / "migration" / "file_manifest.csv"
REPORT_MD = WB / "10_docs" / "migration" / "pre_refactor_content_audit_20260913.md"
REPORT_JSON = WB / "10_docs" / "migration" / "pre_refactor_content_audit_20260913.json"
LOST_CSV = WB / "10_docs" / "migration" / "pre_refactor_lost_blobs.csv"

EXPECTED_MISSING = re.compile(
    r"(^|/)(outputs|outputs_|__pycache__|\.pytest_cache|node_modules|"
    r"build|dist|\.tmp\.driveupload|DELETE)(/|$)",
    re.I,
)
EXPECTED_SUFFIXES = {".pyd", ".obj", ".pyc", ".pyo", ".log", ".bak", ".tmp"}


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "core.longpaths=true", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )


def ls_tree_blobs(root: Path, commit: str) -> dict[str, str]:
    """Return posix path -> blob SHA for files in commit."""
    raw = git(root, "ls-tree", "-r", "-z", commit).stdout
    mapping: dict[str, str] = {}
    for entry in raw.split("\0"):
        if not entry:
            continue
        meta, path = entry.split("\t", 1)
        parts = meta.split()
        if len(parts) < 3 or parts[1] != "blob":
            continue
        mapping[path.replace("\\", "/")] = parts[2]
    return mapping


def path_map_moves(path_map: Path = PATH_MAP) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for row in load_path_map(path_map):
        if (row.get("status") or "").strip().lower() not in {"moved", "verified"}:
            continue
        old = (row.get("old_path") or "").replace("\\", "/").strip()
        new = (row.get("new_path") or "").replace("\\", "/").strip()
        if not old or not new or "*" in old:
            continue
        rows.append((old, new))
    return rows


def mapped_path(old_file: str, moves: list[tuple[str, str]]) -> str:
    mapped = di.remap_old_to_new(old_file, moves)
    return mapped if mapped else old_file


def is_expected_loss(rel: str) -> bool:
    if Path(rel).suffix.lower() in EXPECTED_SUFFIXES:
        return True
    return bool(EXPECTED_MISSING.search(rel.replace("\\", "/")))


def classify_git_paths(
    old_tree: dict[str, str],
    new_tree: dict[str, str],
    moves: list[tuple[str, str]],
) -> dict[str, object]:
    new_blobs = set(new_tree.values())
    present = 0
    relocated = 0
    lost: list[dict[str, str]] = []
    expected: list[dict[str, str]] = []
    for old_path, blob in old_tree.items():
        dest = mapped_path(old_path, moves)
        if dest in new_tree:
            present += 1
            continue
        if blob in new_blobs:
            relocated += 1
            continue
        row = {"old_path": old_path, "mapped": dest, "blob": blob}
        if is_expected_loss(old_path) or is_expected_loss(dest):
            expected.append(row)
        else:
            lost.append(row)
    return {
        "old_files": len(old_tree),
        "new_files": len(new_tree),
        "present_after_remap": present,
        "relocated_by_blob": relocated,
        "lost": lost,
        "expected_loss": expected,
    }


def classify_ignored_manifest(
    root: Path,
    moves: list[tuple[str, str]],
    *,
    manifest_path: Path = MANIFEST,
    limit_samples: int = 80,
) -> dict[str, object]:
    if not manifest_path.is_file():
        return {"skipped": True, "reason": "file_manifest.csv missing"}
    present = 0
    missing: list[dict[str, str]] = []
    expected = 0
    unexpected = 0
    ignored_rows = 0
    with manifest_path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if (row.get("tracked") or "").strip().lower() == "yes":
                continue
            ignored_rows += 1
            old = (row.get("path") or "").replace("\\", "/").strip()
            if not old:
                continue
            dest = mapped_path(old, moves)
            if is_expected_loss(old) or is_expected_loss(dest):
                expected += 1
                continue
            if (root / dest).is_file() or (root / old).is_file():
                present += 1
                continue
            unexpected += 1
            if len(missing) < limit_samples:
                missing.append({"old_path": old, "mapped": dest})
    return {
        "ignored_rows": ignored_rows,
        "present_on_disk": present,
        "expected_missing": expected,
        "unexpected_missing": unexpected,
        "unexpected_missing_sample": missing,
        "sample_truncated": unexpected > limit_samples,
    }


def write_lost_csv(path: Path, label: str, lost: list[dict[str, str]]) -> None:
    new_file = not path.is_file()
    with path.open("a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["source", "old_path", "mapped", "blob"])
        if new_file:
            w.writeheader()
        for row in lost:
            w.writerow({"source": label, **row})


def render_md(payload: dict[str, object]) -> str:
    lines = [
        "# Pre-refactor content audit — 2026-09-13",
        "",
        "True content loss only: an old path has no HEAD destination after "
        "`path_map.csv` remapping, and its blob is not in HEAD either.",
        "",
    ]
    for label in ("main-sept-4", "sp00-freeze"):
        block = payload.get(label)
        if not isinstance(block, dict):
            continue
        lost = block.get("lost") or []
        expected = block.get("expected_loss") or []
        lines += [
            f"## {label}",
            "",
            f"- old files: `{block.get('old_files')}`",
            f"- HEAD files: `{block.get('new_files')}`",
            f"- present after remap: `{block.get('present_after_remap')}`",
            f"- same blob at another HEAD path: `{block.get('relocated_by_blob')}`",
            f"- expected loss (outputs/build/binaries): `{len(expected)}`",
            f"- unexpected lost blobs: `{len(lost)}`",
            "",
        ]
        if lost:
            lines.append("Sample unexpected losses:")
            lines.append("")
            for row in lost[:25]:
                lines.append(f"- `{row['old_path']}` → `{row['mapped']}`")
            lines.append("")
    disk = payload.get("ignored_disk")
    if isinstance(disk, dict) and not disk.get("skipped"):
        sample = disk.get("unexpected_missing_sample") or []
        lines += [
            "## Ignored freeze-manifest files on disk",
            "",
            f"- ignored rows: `{disk.get('ignored_rows')}`",
            f"- present at old or remapped path: `{disk.get('present_on_disk')}`",
            f"- expected missing: `{disk.get('expected_missing')}`",
            f"- unexpected missing: `{disk.get('unexpected_missing')}`"
            + (" (sample truncated)" if disk.get("sample_truncated") else ""),
            "",
        ]
        for row in sample[:25]:
            lines.append(f"- `{row['old_path']}` → `{row['mapped']}`")
        lines.append("")
    drive = payload.get("drive_cleanup")
    if isinstance(drive, dict):
        counts = drive.get("counts") or {}
        lines += [
            "## Google Drive conflict copies",
            "",
            f"- delete_duplicate: `{counts.get('delete_duplicate', 0)}`",
            f"- quarantine_unique: `{counts.get('quarantine_unique', 0)}`",
            f"- skip_tracked: `{counts.get('skip_tracked', 0)}`",
            "",
        ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=WB)
    p.add_argument("--new", default="HEAD")
    p.add_argument("--skip-disk", action="store_true")
    args = p.parse_args(argv)
    root = args.root.resolve()
    moves = path_map_moves()
    new_tree = ls_tree_blobs(root, args.new)
    payload: dict[str, object] = {
        "new": args.new,
        "moves": len(moves),
    }
    if LOST_CSV.is_file():
        LOST_CSV.unlink()
    for label, commit in (("main-sept-4", SEPT4_COMMIT), ("sp00-freeze", FREEZE_COMMIT)):
        old_tree = ls_tree_blobs(root, commit)
        result = classify_git_paths(old_tree, new_tree, moves)
        payload[label] = {
            "commit": commit,
            "old_files": result["old_files"],
            "new_files": result["new_files"],
            "present_after_remap": result["present_after_remap"],
            "relocated_by_blob": result["relocated_by_blob"],
            "lost_count": len(result["lost"]),  # type: ignore[arg-type]
            "expected_loss_count": len(result["expected_loss"]),  # type: ignore[arg-type]
            "lost": result["lost"][:200],
            "expected_loss": result["expected_loss"][:50],
        }
        write_lost_csv(LOST_CSV, label, result["lost"])  # type: ignore[arg-type]
    if args.skip_disk:
        payload["ignored_disk"] = {"skipped": True}
    else:
        payload["ignored_disk"] = classify_ignored_manifest(root, moves)
    REPORT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(payload), encoding="utf-8")
    print(f"wrote {REPORT_MD}")
    print(f"wrote {REPORT_JSON}")
    print(f"wrote {LOST_CSV}")
    sept = payload["main-sept-4"]
    freeze = payload["sp00-freeze"]
    print(
        f"sept4 lost={sept['lost_count']} expected={sept['expected_loss_count']} "
        f"freeze lost={freeze['lost_count']} expected={freeze['expected_loss_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
