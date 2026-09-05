#!/usr/bin/env python3
"""Execute one restructure phase from path_map.csv (SP04+).

Moves are `git mv` only. Nothing is ever deleted: rows whose destination is under
`DELETE/` are still ordinary moves that preserve the path relative to the repo root.

Per row the sequence is:

    path_map row (status=pending)
      -> git mv old new
      -> status=moved
      -> junctions.py create   (separate step, run after this script)
      -> verify + status=verified

Three shapes of row need different handling:

* **glob** (`*.zip`, `INVENTORY*.md`) - expanded against the repo root, each match moved
  into the destination directory.
* **merge** - destination already exists as a directory, so children are moved one by one
  instead of nesting the source inside the destination.
* **untracked** - `git mv` refuses paths git does not know. Those fall back to a
  filesystem move, which is equivalent here because the content is gitignored anyway.

Usage:
    python 07_scripts/move_phase.py --phase SP04 --dry-run
    python 07_scripts/move_phase.py --phase SP04 --apply
    python 07_scripts/move_phase.py --phase SP04 --verify
"""
from __future__ import annotations

import argparse
import csv
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from junctions import (  # noqa: E402
    PATH_MAP_REL,
    JunctionError,
    _phase_matches,
    find_workbench_root,
)


class MoveError(RuntimeError):
    """User-facing move failure."""


def clear_readonly(path: Path) -> None:
    """Drop the Windows ReadOnly attribute from a path.

    Every directory in this working tree carries `ReadOnly, Directory` (a Google Drive
    sync artifact). Windows then refuses both `git mv` and `rmdir` on them, which is
    what stopped the first SP04 run on KnotTheory and Restore_Archives.
    """
    if os.name != "nt":
        return
    try:
        attrs = os.stat(path, follow_symlinks=False).st_file_attributes
    except (OSError, AttributeError):
        return
    readonly = 0x1  # FILE_ATTRIBUTE_READONLY
    if attrs & readonly:
        try:
            os.chmod(path, stat.S_IWRITE)
        except OSError:
            pass


def _same_bytes(a: Path, b: Path) -> bool:
    import hashlib

    def digest(p: Path) -> str:
        h = hashlib.sha256()
        with p.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    return a.stat().st_size == b.stat().st_size and digest(a) == digest(b)


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "core.longpaths=true", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def is_tracked(root: Path, rel: str) -> bool:
    proc = git(root, "ls-files", "--error-unmatch", rel)
    if proc.returncode == 0:
        return True
    # A directory is "tracked" if it contains at least one tracked file.
    proc = git(root, "ls-files", rel)
    return bool(proc.stdout.strip())


def load_rows(root: Path) -> tuple[list[dict[str, str]], list[str]]:
    path = root / PATH_MAP_REL
    with path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader), list(reader.fieldnames or [])


def save_rows(root: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path = root / PATH_MAP_REL
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def phase_rows(rows: list[dict[str, str]], phase: str, status: str) -> list[dict[str, str]]:
    """Rows for one phase, ordered deepest-path-first.

    Ordering matters: `datasets/twist_knots` has its own destination while the
    container row `datasets` sweeps whatever is left. If the container ran first it
    would swallow the child. Sorting by descending path depth makes every child row
    win over its ancestor without special-casing.
    """
    selected = [
        r
        for r in rows
        if _phase_matches(r.get("phase") or "", phase)
        and (r.get("status") or "").strip().lower() == status
        and (r.get("old_path") or "").strip()
        and (r.get("new_path") or "").strip()
    ]
    return sorted(
        selected,
        key=lambda r: (-r["old_path"].replace("\\", "/").count("/"), r["old_path"]),
    )


def expand(root: Path, old_rel: str) -> list[Path]:
    """Resolve a path_map old_path to concrete existing paths."""
    if any(ch in old_rel for ch in "*?["):
        return sorted(p for p in root.glob(old_rel) if p.exists())
    p = root / old_rel
    return [p] if p.exists() else []


def move_one(root: Path, src: Path, dst: Path, *, dry_run: bool) -> list[str]:
    """Move src to dst, returning a log of the operations performed."""
    rel_src = src.relative_to(root).as_posix()
    rel_dst = dst.relative_to(root).as_posix()
    log: list[str] = []

    if dst.is_dir() and src.is_file():
        # A file addressed at an existing directory belongs inside it, not beside it.
        return move_one(root, src, dst / src.name, dry_run=dry_run)

    if dst.exists() and src.is_dir() and dst.is_dir():
        # Merge: move children individually so the source does not nest inside.
        for child in sorted(src.iterdir()):
            log += move_one(root, child, dst / child.name, dry_run=dry_run)
        if not dry_run and src.is_dir() and not any(src.iterdir()):
            clear_readonly(src)
            try:
                src.rmdir()
                log.append(f"rmdir empty {rel_src}")
            except OSError as exc:
                # An empty leftover directory is cosmetic; never fail the phase for it.
                log.append(f"WARN could not remove empty {rel_src}: {exc}")
        return log

    if dst.exists():
        # A file already sits at the destination. Never overwrite. If the two are
        # byte-identical the source is a duplicate and is retired to DELETE/ with its
        # original path intact; anything else needs a human decision.
        if src.is_file() and dst.is_file() and _same_bytes(src, dst):
            grave = root / "DELETE" / rel_src
            if dry_run:
                log.append(f"duplicate -> DELETE/{rel_src}")
                return log
            grave.parent.mkdir(parents=True, exist_ok=True)
            if is_tracked(root, rel_src):
                proc = git(root, "mv", rel_src, grave.relative_to(root).as_posix())
                if proc.returncode != 0:
                    raise MoveError(
                        f"git mv to DELETE failed for {rel_src}: "
                        f"{(proc.stderr or proc.stdout).strip()}"
                    )
            else:
                shutil.move(str(src), str(grave))
            log.append(f"duplicate (identical) -> DELETE/{rel_src}")
            return log
        raise MoveError(
            f"destination already exists and differs: {rel_dst} "
            f"(source {rel_src}) - resolve by hand"
        )

    if dry_run:
        log.append(f"git mv {rel_src} -> {rel_dst}")
        return log

    dst.parent.mkdir(parents=True, exist_ok=True)
    clear_readonly(src)

    if is_tracked(root, rel_src):
        proc = git(root, "mv", rel_src, rel_dst)
        if proc.returncode != 0:
            message = (proc.stderr or proc.stdout).strip()
            if src.is_dir() and "denied" in message.lower():
                # Something holds a handle on the directory itself, so it cannot be
                # renamed as a unit. Its children usually can be. Move them one by one
                # and leave the empty shell for SP11.
                log.append(f"WARN {rel_src} locked; moving children individually")
                dst.mkdir(parents=True, exist_ok=True)
                for child in sorted(src.iterdir()):
                    log += move_one(root, child, dst / child.name, dry_run=dry_run)
                clear_readonly(src)
                try:
                    src.rmdir()
                    log.append(f"rmdir empty {rel_src}")
                except OSError:
                    log.append(f"WARN empty shell remains: {rel_src}")
                return log
            raise MoveError(f"git mv failed for {rel_src} -> {rel_dst}: {message}")
        log.append(f"git mv {rel_src} -> {rel_dst}")
    else:
        shutil.move(str(src), str(dst))
        log.append(f"fs move (untracked) {rel_src} -> {rel_dst}")
    return log


def run_phase(root: Path, phase: str, *, dry_run: bool) -> int:
    rows, fields = load_rows(root)
    todo = phase_rows(rows, phase, "pending")
    if not todo:
        print(f"{phase}: no pending rows")
        return 0

    print(f"{phase}: {len(todo)} pending rows{' (dry-run)' if dry_run else ''}\n")
    errors = 0
    moved = 0
    for row in todo:
        old_rel = row["old_path"].strip()
        new_rel = row["new_path"].strip()
        sources = expand(root, old_rel)

        if not sources:
            row["status"] = "skipped"
            note = row.get("note") or ""
            row["note"] = (note + "; " if note else "") + "old_path_missing_on_disk"
            print(f"  SKIP  {old_rel}  (not on disk)")
            continue

        try:
            for src in sources:
                if any(ch in old_rel for ch in "*?["):
                    dst = root / new_rel / src.name
                else:
                    dst = root / new_rel
                for line in move_one(root, src, dst, dry_run=dry_run):
                    print(f"    {line}")
            if not dry_run:
                row["status"] = "moved"
            moved += 1
            print(f"  OK    {old_rel} -> {new_rel}")
        except (MoveError, OSError) as exc:
            # One unmovable row must never abort the phase and lose the status of
            # everything already moved. That is how the first SP04 run left 11 moved
            # directories with path_map still saying "pending".
            print(f"  ERROR {old_rel}: {exc}", file=sys.stderr)
            errors += 1

    if not dry_run:
        save_rows(root, rows, fields)
        print(f"\npath_map.csv updated ({moved} rows -> moved)")
    else:
        print(f"\n(dry run; {moved} rows would move)")
    return 1 if errors else 0


def reconcile_phase(root: Path, phase: str) -> int:
    """Re-derive row status from what is actually on disk.

    Needed after an interrupted run: a row whose source is gone and whose destination
    exists did move, whatever the CSV says.
    """
    rows, fields = load_rows(root)
    fixed = 0
    for row in rows:
        if not _phase_matches(row.get("phase") or "", phase):
            continue
        if (row.get("status") or "").strip().lower() != "pending":
            continue
        old_rel, new_rel = row["old_path"].strip(), row["new_path"].strip()
        if not old_rel or not new_rel:
            continue
        gone = not expand(root, old_rel)
        landed = (root / new_rel).exists()
        if gone and landed:
            row["status"] = "moved"
            fixed += 1
            print(f"  reconciled -> moved: {old_rel}")
    save_rows(root, rows, fields)
    print(f"\n{fixed} rows reconciled to moved")
    return 0


def verify_phase(root: Path, phase: str) -> int:
    rows, fields = load_rows(root)
    todo = phase_rows(rows, phase, "moved")
    if not todo:
        print(f"{phase}: no moved rows to verify")
        return 0
    errors = 0
    for row in todo:
        new_rel = row["new_path"].strip()
        old_rel = row["old_path"].strip()
        dst = root / new_rel
        if not dst.exists():
            print(f"  FAIL  destination missing: {new_rel}", file=sys.stderr)
            errors += 1
            continue
        row["status"] = "verified"
        print(f"  ok    {old_rel} -> {new_rel}")
    if not errors:
        save_rows(root, rows, fields)
        print(f"\n{len(todo)} rows -> verified")
    return 1 if errors else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=None)
    ap.add_argument("--phase", required=True)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--reconcile", action="store_true")
    args = ap.parse_args(argv)

    root = args.root.resolve() if args.root else find_workbench_root()
    if args.reconcile:
        return reconcile_phase(root, args.phase)
    if args.verify:
        return verify_phase(root, args.phase)
    return run_phase(root, args.phase, dry_run=args.dry_run)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (MoveError, JunctionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
