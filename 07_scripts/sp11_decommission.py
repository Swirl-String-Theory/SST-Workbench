"""SP11 decommission helpers: safe junction teardown and staging records.

Hard rules:
- Never unlink research trees.
- Remove junctions with ``os.rmdir`` on the reparse point only.
- Empty level-2 scaffolds may be removed with ``os.rmdir`` only when empty.
- Archive zip candidates are staged to ``DELETE/`` only when every member has a
  hash-matching extracted counterpart (see ``archive_zip_safe_to_stage``).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import junctions as jn  # noqa: E402

STUB_PATHS = (
    "to_be_processed",
    "falsifier_registry",
    "experiments/derive_constants",
    "experiments/trefoil",
)

REGISTRY_REL = Path("10_docs") / "migration" / "junction_registry.csv"
REGISTRY_SNAPSHOT_REL = (
    Path("10_docs") / "migration" / "junction_registry_pre_sp11.csv"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def archive_zip_safe_to_stage(
    zip_path: Path, extracted_root: Path
) -> tuple[bool, str]:
    """Return (ok, reason). Safe only if every zip member has a hash twin.

    Directories in the zip are ignored. Missing extracted files, size mismatches,
    or hash mismatches make the zip unsafe to stage for soft-retire.
    """
    if not zip_path.is_file():
        return False, "zip_missing"
    if not extracted_root.is_dir():
        return False, "extracted_root_missing"
    try:
        with zipfile.ZipFile(zip_path) as zf:
            members = [i for i in zf.infolist() if not i.is_dir()]
            if not members:
                return False, "zip_empty"
            for info in members:
                name = info.filename.replace("\\", "/")
                if name.endswith("/"):
                    continue
                target = extracted_root / name
                if not target.is_file():
                    # Also try basename-only layout used by some packs.
                    alt = extracted_root / Path(name).name
                    if not alt.is_file():
                        return False, f"missing_extracted:{name}"
                    target = alt
                if target.stat().st_size != info.file_size:
                    return False, f"size_mismatch:{name}"
                with zf.open(info) as src:
                    zhash = sha256_bytes(src.read())
                if sha256_file(target) != zhash:
                    return False, f"hash_mismatch:{name}"
    except zipfile.BadZipFile:
        return False, "bad_zip"
    return True, "all_members_hash_match"


def snapshot_registry(root: Path) -> Path:
    src = root / REGISTRY_REL
    dst = root / REGISTRY_SNAPSHOT_REL
    if not src.is_file():
        raise FileNotFoundError(src)
    shutil.copy2(src, dst)
    return dst


def _depth_key(rel: str) -> tuple[int, str]:
    parts = Path(rel.replace("\\", "/")).parts
    return (-len(parts), rel.replace("\\", "/"))


def remove_live_junctions(root: Path, *, dry_run: bool = False) -> dict[str, int]:
    """Remove every live junction recorded in the registry, deepest first.

    Keeps ``junction_registry.csv`` intact (provenance). Snapshots first if the
    pre-SP11 snapshot is missing. Strips matching ``.git/info/exclude`` lines.
    After junctions are gone, removes empty level-2 scaffold directories listed as
    REAL dirs in the registry (``os.rmdir`` only).
    """
    stats = {
        "junctions_removed": 0,
        "scaffolds_removed": 0,
        "already_gone": 0,
        "errors": 0,
        "skipped_nonempty_scaffold": 0,
    }
    if not (root / REGISTRY_SNAPSHOT_REL).is_file() and not dry_run:
        snapshot_registry(root)

    rows = jn.load_registry(root)
    # Pass 1: junctions (deepest first)
    for r in sorted(rows, key=lambda x: _depth_key(x.get("old_path") or "")):
        old_rel = (r.get("old_path") or "").strip()
        if not old_rel:
            continue
        link = root / old_rel.replace("\\", "/")
        if jn.is_junction(link):
            print(f"remove junction: {old_rel}{' (dry-run)' if dry_run else ''}")
            if dry_run:
                stats["junctions_removed"] += 1
                continue
            try:
                jn.remove_junction(link)
                jn.strip_git_exclude(root, old_rel)
                stats["junctions_removed"] += 1
            except jn.JunctionError as exc:
                print(f"ERROR: {exc}", file=sys.stderr)
                stats["errors"] += 1
        elif not link.exists():
            stats["already_gone"] += 1
            if not dry_run:
                jn.strip_git_exclude(root, old_rel)

    # Pass 2: empty scaffolds that were REAL dirs holding only child junctions
    for r in sorted(rows, key=lambda x: _depth_key(x.get("old_path") or "")):
        old_rel = (r.get("old_path") or "").strip()
        if not old_rel:
            continue
        path = root / old_rel.replace("\\", "/")
        if not path.exists() or jn.is_junction(path) or not path.is_dir():
            continue
        try:
            remaining = list(path.iterdir())
        except OSError as exc:
            print(f"ERROR: cannot list {old_rel}: {exc}", file=sys.stderr)
            stats["errors"] += 1
            continue
        if remaining:
            stats["skipped_nonempty_scaffold"] += 1
            continue
        print(f"remove empty scaffold: {old_rel}{' (dry-run)' if dry_run else ''}")
        if dry_run:
            stats["scaffolds_removed"] += 1
            continue
        try:
            os.rmdir(path)
            jn.strip_git_exclude(root, old_rel)
            stats["scaffolds_removed"] += 1
        except OSError as exc:
            print(f"ERROR: rmdir {old_rel}: {exc}", file=sys.stderr)
            stats["errors"] += 1

    return stats


def count_research_venvs(root: Path) -> int:
    research = root / "01_research"
    if not research.is_dir():
        return 0
    return sum(1 for _ in research.rglob(".venv") if _.is_dir())


def count_run_install(root: Path) -> int:
    research = root / "01_research"
    if not research.is_dir():
        return 0
    return sum(1 for _ in research.rglob("run_01_install.cmd") if _.is_file())


def stubs_absent(root: Path) -> list[str]:
    present = []
    for rel in STUB_PATHS:
        p = root / rel.replace("\\", "/")
        if p.exists() or jn.is_junction(p):
            present.append(rel)
    return present


def live_root_junctions(root: Path) -> list[str]:
    """Root-level reparse points (compat layer leftovers)."""
    out: list[str] = []
    for child in sorted(root.iterdir()):
        if jn.is_junction(child):
            out.append(child.name)
    return out


def write_decommission_report(root: Path, stats: dict[str, int]) -> Path:
    out = root / "10_docs" / "migration" / "sp11_decommission.md"
    venvs = count_research_venvs(root)
    installs = count_run_install(root)
    stubs = stubs_absent(root)
    live = live_root_junctions(root)
    tmp = root / ".tmp.driveupload"
    lines = [
        "# SP11 decommission",
        "",
        f"Generated: {utc_now()}",
        "",
        "## Stubs",
        "",
        (
            "Soft-retired via `git mv` to `DELETE/<original/relative/path>`."
            if not stubs
            else f"STILL PRESENT: {', '.join(stubs)}"
        ),
        "",
        "| original | DELETE path |",
        "|----------|-------------|",
    ]
    for rel in STUB_PATHS:
        lines.append(f"| `{rel}/` | `DELETE/{rel}/` |")
    lines.extend(
        [
            "",
            "## Caches / `.venv`",
            "",
            f"- `.venv` directories under `01_research/`: **{venvs}**",
            f"- `run_01_install.cmd` files under `01_research/`: **{installs}**",
            "- **Decision:** deferred. A `.venv` is disposable only when install can",
            "  recreate it; most families lack `run_01_install.cmd`. No mass staging.",
            "",
            "## Junctions",
            "",
            f"- junctions removed: **{stats.get('junctions_removed', 0)}**",
            f"- empty scaffolds removed: **{stats.get('scaffolds_removed', 0)}**",
            f"- already gone: **{stats.get('already_gone', 0)}**",
            f"- nonempty scaffolds skipped: **{stats.get('skipped_nonempty_scaffold', 0)}**",
            f"- errors: **{stats.get('errors', 0)}**",
            f"- live root junctions remaining: **{len(live)}**"
            + (f" (`{', '.join(live)}`)" if live else ""),
            "- Provenance retained: `10_docs/migration/junction_registry.csv` and",
            "  `junction_registry_pre_sp11.csv` (snapshot before teardown).",
            "- Restore: `07_scripts/bootstrap_junctions.cmd` (rebuilds from path_map).",
            "",
            "## Archive deduplication",
            "",
            "- **Decision:** zero zips staged to `DELETE/`.",
            "- Reason: `INVENTORY_ARCHIVES.md` still lists scripts that exist only",
            "  inside archives; SP11 only stages a zip when every member has a",
            "  hash-matching extracted counterpart (`archive_zip_safe_to_stage`).",
            "- No zip cleared that bar in this pass; archives stay under",
            "  `09_archive/restore/` (junction target).",
            "",
            "## `.tmp.driveupload/`",
            "",
            (
                "- **Absent** on disk — no action. Outside migration scope."
                if not tmp.exists()
                else "- Present — left untouched (separate Google Drive decision)."
            ),
            "",
            "## Provenance (kept forever)",
            "",
            "- `10_docs/migration/path_map.csv`",
            "- `10_docs/migration/checksums.sha256`",
            "- `10_docs/migration/junction_registry.csv`",
            "- `10_docs/migration/junction_registry_pre_sp11.csv`",
            "- `10_docs/migration/reproducibility_gate.md`",
            "",
        ]
    )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=None)
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("remove-junctions", help="Safely remove live junctions")
    r.add_argument("--dry-run", action="store_true")
    sub.add_parser("report", help="Write sp11_decommission.md from current state")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve() if args.root else jn.find_workbench_root()
    if args.command == "remove-junctions":
        stats = remove_live_junctions(root, dry_run=args.dry_run)
        write_decommission_report(root, stats)
        print(stats)
        return 1 if stats["errors"] else 0
    if args.command == "report":
        write_decommission_report(root, {})
        return 0
    raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
