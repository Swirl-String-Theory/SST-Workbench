"""Classify and clean Google Drive Desktop ``name (N)`` conflict copies.

Default is dry-run. ``--apply`` deletes hash-identical duplicates and moves
unique conflict files to ``09_archive/drive_conflicts/<original/relative/path>``.

Tracked git paths are never touched, including historical names like
``Infographic(1).png`` (no space before the parenthesis).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
QUARANTINE = Path("09_archive") / "drive_conflicts"
LEDGER_DEFAULT = WB / "10_docs" / "migration" / "drive_conflict_cleanup_20260913.jsonl"

# Drive Desktop: space + (N) at end of a path component or of the file stem.
DRIVE_COMPONENT = re.compile(r"^(.*) \((\d+)\)$")
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".tmp.driveupload"}


@dataclass(frozen=True)
class DriveAction:
    rel: str
    action: str  # skip_tracked | delete_duplicate | quarantine_unique | skip_unreadable
    canonical: str | None
    sha256: str | None
    canonical_sha256: str | None
    note: str = ""


def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def drive_canonical_component(name: str) -> str | None:
    """Return the Drive-stripped component, or None if it is not a `` (N)`` name."""
    matched = DRIVE_COMPONENT.match(name)
    if matched:
        return matched.group(1)
    stem_match = DRIVE_COMPONENT.match(Path(name).stem)
    suffix = Path(name).suffix
    if stem_match and suffix:
        return f"{stem_match.group(1)}{suffix}"
    return None


def has_drive_conflict_component(rel: str) -> bool:
    return any(drive_canonical_component(part) is not None for part in Path(rel).parts)


def canonical_rel(rel: str) -> str:
    """Strip Drive `` (N)`` markers from every path component."""
    parts: list[str] = []
    for part in Path(rel).parts:
        stripped = drive_canonical_component(part)
        parts.append(stripped if stripped is not None else part)
    return "/".join(parts).replace("\\", "/")


def posix_rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def tracked_paths(root: Path) -> set[str]:
    r = subprocess.run(
        ["git", "-c", "core.longpaths=true", "ls-files", "-z"],
        cwd=root,
        capture_output=True,
        check=True,
    )
    out = r.stdout.split(b"\0")
    return {p.decode("utf-8", "surrogateescape").replace("\\", "/") for p in out if p}


def iter_untracked_others(root: Path) -> list[str]:
    """Untracked, non-ignored paths (same set as ``git status -u``)."""
    r = subprocess.run(
        [
            "git",
            "-c",
            "core.longpaths=true",
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        cwd=root,
        capture_output=True,
        check=True,
    )
    out = r.stdout.split(b"\0")
    rels = []
    for raw in out:
        if not raw:
            continue
        rel = raw.decode("utf-8", "surrogateescape").replace("\\", "/")
        if any(part in SKIP_DIRS for part in Path(rel).parts):
            continue
        if rel.replace("\\", "/").startswith(QUARANTINE.as_posix() + "/"):
            continue
        rels.append(rel)
    return rels


def classify_conflict(
    root: Path,
    rel: str,
    *,
    tracked: set[str],
) -> DriveAction:
    rel_n = rel.replace("\\", "/")
    if rel_n in tracked:
        return DriveAction(rel_n, "skip_tracked", None, None, None, "git ls-files")
    if not has_drive_conflict_component(rel_n):
        return DriveAction(rel_n, "skip_unreadable", None, None, None, "not a Drive (N) name")
    src = root / rel_n
    if not src.is_file():
        return DriveAction(rel_n, "skip_unreadable", None, None, None, "not a file")
    canonical = canonical_rel(rel_n)
    try:
        digest = sha256_file(src)
    except OSError as exc:
        return DriveAction(rel_n, "skip_unreadable", canonical, None, None, str(exc))
    sibling = root / canonical
    if canonical != rel_n and sibling.is_file():
        try:
            sib_digest = sha256_file(sibling)
        except OSError as exc:
            return DriveAction(rel_n, "quarantine_unique", canonical, digest, None, str(exc))
        if sib_digest == digest:
            return DriveAction(
                rel_n, "delete_duplicate", canonical, digest, sib_digest, "hash matches sibling"
            )
        return DriveAction(
            rel_n,
            "quarantine_unique",
            canonical,
            digest,
            sib_digest,
            "sibling exists with different hash",
        )
    return DriveAction(
        rel_n,
        "quarantine_unique",
        canonical if canonical != rel_n else None,
        digest,
        None,
        "no hash-identical sibling",
    )


def classify_tree(root: Path, *, tracked: set[str] | None = None) -> list[DriveAction]:
    tracked_set = tracked if tracked is not None else tracked_paths(root)
    actions: list[DriveAction] = []
    for rel in iter_untracked_others(root):
        if not has_drive_conflict_component(rel):
            continue
        path = root / rel
        if path.is_dir():
            continue
        actions.append(classify_conflict(root, rel, tracked=tracked_set))
    return actions


def quarantine_dest(root: Path, rel: str) -> Path:
    dest = root / QUARANTINE / rel
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    n = 2
    while True:
        candidate = dest.with_name(f"{stem}__keep{n}{suffix}")
        if not candidate.exists():
            return candidate
        n += 1


def apply_actions(
    root: Path,
    actions: list[DriveAction],
    *,
    apply: bool,
    ledger: Path | None = None,
) -> dict[str, int]:
    counts = {
        "delete_duplicate": 0,
        "quarantine_unique": 0,
        "skip_tracked": 0,
        "skip_unreadable": 0,
        "applied": 0,
    }
    rows: list[dict[str, object]] = []
    for action in actions:
        counts[action.action] = counts.get(action.action, 0) + 1
        record = asdict(action)
        record["applied"] = False
        if apply and action.action in {"delete_duplicate", "quarantine_unique"}:
            src = root / action.rel
            if not src.exists():
                record["note"] = (action.note + "; already gone").strip("; ")
                rows.append(record)
                continue
            if action.action == "delete_duplicate":
                src.unlink()
            else:
                dest = quarantine_dest(root, action.rel)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dest))
                record["quarantine"] = dest.relative_to(root).as_posix()
            record["applied"] = True
            counts["applied"] += 1
            _remove_empty_parents(src.parent, root)
        rows.append(record)
    if ledger is not None:
        ledger.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).isoformat()
        with ledger.open("a", encoding="utf-8") as fh:
            for row in rows:
                if row["action"] not in {"delete_duplicate", "quarantine_unique"}:
                    continue
                row["utc"] = stamp
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return counts


def _remove_empty_parents(start: Path, root: Path) -> None:
    cur = start
    root_r = root.resolve()
    while cur.exists() and cur.resolve() != root_r:
        try:
            empty = not any(cur.iterdir())
        except OSError:
            break
        if not empty:
            break
        try:
            cur.rmdir()
        except OSError:
            break
        cur = cur.parent


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=WB)
    p.add_argument("--apply", action="store_true")
    p.add_argument("--ledger", type=Path, default=LEDGER_DEFAULT)
    args = p.parse_args(argv)
    root = args.root.resolve()
    actions = classify_tree(root)
    counts = apply_actions(root, actions, apply=args.apply, ledger=args.ledger)
    print(json.dumps({"apply": bool(args.apply), "counts": counts}, indent=2))
    interesting = [a for a in actions if a.action != "skip_tracked"]
    for a in interesting[:40]:
        print(f"  {a.action:20} {a.rel}")
    if len(interesting) > 40:
        print(f"  ... {len(interesting) - 40} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
