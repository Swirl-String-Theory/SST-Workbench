#!/usr/bin/env python3
"""Compatibility directory junctions for the SST-Workbench restructure (SP02).

Reads path_map.csv rows with junction=yes and status=moved.
Creates/verifies/removes mklink /J junctions and keeps .git/info/exclude in sync.

Junction removal never deletes the target tree.
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT_MARKER = ".sst-workbench-root"
PATH_MAP_REL = Path("10_docs") / "migration" / "path_map.csv"
REGISTRY_REL = Path("10_docs") / "migration" / "junction_registry.csv"
EXCLUDE_HEADER = "# SST-Workbench SP02 junctions (do not commit; local compat only)"

REGISTRY_FIELDS = ("old_path", "target", "created_at", "phase")


class JunctionError(RuntimeError):
    """User-facing junction operation failure."""


def find_workbench_root(start: Path | None = None) -> Path:
    cur = (start or Path(__file__)).resolve()
    if cur.is_file():
        cur = cur.parent
    for p in [cur, *cur.parents]:
        if (p / ROOT_MARKER).is_file():
            return p
    raise JunctionError(
        f"Could not find {ROOT_MARKER}; set cwd inside SST-Workbench"
    )


def _norm_rel(path: str | Path) -> str:
    return str(path).replace("\\", "/").strip().strip("/")


def _phase_matches(row_phase: str, want: str | None) -> bool:
    if not want:
        return True
    tokens = [t.strip() for t in (row_phase or "").replace("/", " ").split() if t.strip()]
    return want in tokens or (row_phase or "").strip() == want


def load_path_map(root: Path) -> list[dict[str, str]]:
    path = root / PATH_MAP_REL
    if not path.is_file():
        raise JunctionError(f"missing path_map: {path}")
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


#: A row needs a junction once its content has left the old path. `verified` is the
#: terminal state of a completed move, so it must select just like `moved` - otherwise
#: `verify` silently checks nothing the moment a phase is signed off.
JUNCTION_STATUSES = frozenset({"moved", "verified"})


def selectable_rows(
    rows: list[dict[str, str]], *, phase: str | None = None
) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for r in rows:
        if (r.get("junction") or "").strip().lower() != "yes":
            continue
        if (r.get("status") or "").strip().lower() not in JUNCTION_STATUSES:
            continue
        if not _phase_matches(r.get("phase") or "", phase):
            continue
        old = (r.get("old_path") or "").strip()
        new = (r.get("new_path") or "").strip()
        if not old or not new:
            continue
        out.append(r)
    return out


def is_junction(path: Path) -> bool:
    try:
        if hasattr(path, "is_junction") and path.is_junction():
            return True
    except OSError:
        return False
    if not path.exists():
        return False
    try:
        st = path.lstat() if hasattr(path, "lstat") else os.lstat(path)
        # FILE_ATTRIBUTE_REPARSE_POINT = 0x400
        return bool(getattr(st, "st_file_attributes", 0) & 0x400) and path.is_dir()
    except OSError:
        return False


def junction_target(path: Path) -> Path:
    raw = os.readlink(path)
    # Windows may return \\?\ prefix or relative targets.
    text = str(raw)
    if text.startswith("\\\\?\\"):
        text = text[4:]
    target = Path(text)
    if not target.is_absolute():
        target = (path.parent / target).resolve()
    else:
        target = target.resolve()
    return target


def create_junction(link: Path, target: Path) -> None:
    """Create a directory junction at ``link`` pointing at ``target``."""
    if os.name != "nt":
        raise JunctionError("junctions require Windows (mklink /J)")
    target = target.resolve()
    if not target.is_dir():
        raise JunctionError(f"target is not a directory: {target}")

    if link.exists() or is_junction(link):
        if is_junction(link):
            current = junction_target(link)
            if current == target:
                return  # idempotent
            raise JunctionError(
                f"junction exists but points elsewhere: {link} -> {current} "
                f"(expected {target})"
            )
        raise JunctionError(
            f"path exists and is not a junction (refusing to replace): {link}"
        )

    link.parent.mkdir(parents=True, exist_ok=True)
    # mklink /J does not require elevation.
    proc = subprocess.run(
        ["cmd", "/d", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise JunctionError(
            f"mklink /J failed for {link} -> {target}: "
            f"{(proc.stderr or proc.stdout or '').strip()}"
        )


def remove_junction(link: Path) -> None:
    """Remove a junction without touching the target tree.

    Uses ``os.rmdir`` on the reparse point (safe). Refuses to remove a real directory.
    """
    if not link.exists() and not _is_reparse_present(link):
        return  # already gone
    if not is_junction(link):
        raise JunctionError(
            f"refusing to remove non-junction path: {link}"
        )
    os.rmdir(link)


def _is_reparse_present(path: Path) -> bool:
    """True if a reparse point exists even when .exists() is tricky."""
    try:
        os.lstat(path)
        return is_junction(path)
    except FileNotFoundError:
        return False
    except OSError:
        return False


def git_exclude_path(root: Path) -> Path:
    return root / ".git" / "info" / "exclude"


def _exclude_lines_for(old_rel: str) -> list[str]:
    """Patterns that hide the junction from git status."""
    rel = _norm_rel(old_rel)
    lines = [rel, rel + "/"]
    # Also the Windows-ish form for tools that normalize differently.
    win = rel.replace("/", "\\")
    if win != rel:
        lines.append(win)
        lines.append(win + "\\")
    return lines


def ensure_git_exclude(root: Path, old_rel: str) -> bool:
    """Append junction patterns to .git/info/exclude. Return True if file changed."""
    path = git_exclude_path(root)
    if not path.parent.is_dir():
        raise JunctionError(f"not a git work tree (missing {path.parent})")
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    lines = existing.splitlines()
    wanted = _exclude_lines_for(old_rel)
    # Prefer a single canonical forward-slash entry with trailing slash.
    canonical = _norm_rel(old_rel) + "/"
    if canonical in lines or _norm_rel(old_rel) in lines:
        return False
    out = list(lines)
    if EXCLUDE_HEADER not in out:
        if out and out[-1].strip():
            out.append("")
        out.append(EXCLUDE_HEADER)
    out.append(canonical)
    text = "\n".join(out) + "\n"
    path.write_text(text, encoding="utf-8")
    return True


def strip_git_exclude(root: Path, old_rel: str) -> bool:
    """Remove junction patterns from exclude. Return True if file changed."""
    path = git_exclude_path(root)
    if not path.is_file():
        return False
    lines = path.read_text(encoding="utf-8").splitlines()
    drop = set(_exclude_lines_for(old_rel))
    new_lines = [ln for ln in lines if ln not in drop]
    # Drop orphan header if no SP02 entries remain.
    if EXCLUDE_HEADER in new_lines:
        body_after = new_lines[new_lines.index(EXCLUDE_HEADER) + 1 :]
        if not any(ln.strip() and not ln.strip().startswith("#") for ln in body_after):
            new_lines = [ln for ln in new_lines if ln != EXCLUDE_HEADER]
    while new_lines and new_lines[-1] == "":
        new_lines.pop()
    new_text = ("\n".join(new_lines) + "\n") if new_lines else ""
    old_text = path.read_text(encoding="utf-8")
    if new_text == old_text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def load_registry(root: Path) -> list[dict[str, str]]:
    path = root / REGISTRY_REL
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f) if any(r.values())]


def save_registry(root: Path, rows: list[dict[str, str]]) -> None:
    path = root / REGISTRY_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(REGISTRY_FIELDS))
        w.writeheader()
        for r in sorted(rows, key=lambda x: _norm_rel(x.get("old_path") or "")):
            w.writerow({k: r.get(k, "") for k in REGISTRY_FIELDS})


def upsert_registry(
    root: Path, *, old_path: str, target: Path, phase: str
) -> None:
    rows = load_registry(root)
    key = _norm_rel(old_path)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = [r for r in rows if _norm_rel(r.get("old_path") or "") != key]
    try:
        target_rec = _norm_rel(target.resolve().relative_to(root.resolve()))
    except ValueError:
        target_rec = str(target.resolve())
    rows.append(
        {
            "old_path": key,
            "target": target_rec,
            "created_at": now,
            "phase": phase,
        }
    )
    save_registry(root, rows)


def drop_registry(root: Path, old_path: str) -> None:
    key = _norm_rel(old_path)
    rows = [
        r
        for r in load_registry(root)
        if _norm_rel(r.get("old_path") or "") != key
    ]
    save_registry(root, rows)


def has_glob(old_rel: str) -> bool:
    return any(ch in old_rel for ch in "*?[")


def expand_glob_row(root: Path, old_rel: str, new_rel: str) -> list[tuple[str, Path]]:
    """Concrete (link_rel, target) pairs for a row whose old_path is a glob.

    A glob cannot be a junction: there is no single path to link. The mover placed each
    match under the destination keeping its own name, so the compat layer is one
    junction per *directory* match, created next to where the glob used to live.

    File matches are skipped - a junction can only point at a directory. Old references
    to those files (for example KnotPlot/*.py) need the SP01 resolver instead.
    """
    old_parent = str(Path(old_rel.replace("\\", "/")).parent).replace("\\", "/")
    dest = root / new_rel.replace("\\", "/")
    if not dest.is_dir():
        return []
    out: list[tuple[str, Path]] = []
    for child in sorted(dest.iterdir()):
        if not child.is_dir():
            continue
        link_rel = f"{old_parent}/{child.name}" if old_parent not in ("", ".") else child.name
        out.append((link_rel, child))
    return out


def _abs_old(root: Path, old_rel: str) -> Path:
    return (root / old_rel.replace("\\", "/")).resolve()


def _abs_new(root: Path, new_rel: str) -> Path:
    return (root / new_rel.replace("\\", "/")).resolve()


def cmd_create(
    root: Path, *, phase: str | None, dry_run: bool
) -> int:
    rows = selectable_rows(load_path_map(root), phase=phase)
    if not rows:
        print(f"create: nothing to do (no junction=yes status=moved rows"
              f"{f' for phase={phase}' if phase else ''})")
        return 0
    errors = 0
    for r in rows:
        old_rel = r["old_path"].strip()
        new_rel = r["new_path"].strip()
        row_phase = (r.get("phase") or phase or "").strip()

        if has_glob(old_rel):
            pairs = expand_glob_row(root, old_rel, new_rel)
            if not pairs:
                print(f"create: {old_rel} -> {new_rel} (no directory matches; skipped)")
                continue
            for link_rel, target in pairs:
                print(f"create: {link_rel} -> {target.relative_to(root).as_posix()}"
                      f"{' (dry-run)' if dry_run else ''}")
                if dry_run:
                    continue
                try:
                    create_junction(root / link_rel, target)
                    ensure_git_exclude(root, link_rel)
                    upsert_registry(
                        root, old_path=link_rel, target=target, phase=row_phase
                    )
                except JunctionError as e:
                    print(f"ERROR: {e}", file=sys.stderr)
                    errors += 1
            continue

        link = root / old_rel.replace("\\", "/")
        target = _abs_new(root, new_rel)
        print(f"create: {old_rel} -> {new_rel}"
              f"{' (dry-run)' if dry_run else ''}")
        if dry_run:
            continue
        try:
            if not target.is_dir():
                raise JunctionError(f"target missing: {target}")
            create_junction(link, target)
            ensure_git_exclude(root, old_rel)
            upsert_registry(
                root, old_path=old_rel, target=target, phase=row_phase
            )
        except JunctionError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            errors += 1
    return 1 if errors else 0


def cmd_verify(root: Path, *, phase: str | None) -> int:
    rows = selectable_rows(load_path_map(root), phase=phase)
    if not rows:
        print("verify: nothing to check (no moved junction rows)")
        return 0
    errors = 0
    checks: list[tuple[str, Path]] = []
    for r in rows:
        old_rel = r["old_path"].strip()
        new_rel = r["new_path"].strip()
        if has_glob(old_rel):
            checks.extend(expand_glob_row(root, old_rel, new_rel))
        else:
            checks.append((old_rel, _abs_new(root, new_rel)))

    for old_rel, expected in checks:
        link = root / old_rel.replace("\\", "/")
        try:
            if not link.exists() and not is_junction(link):
                raise JunctionError(f"missing junction: {old_rel}")
            if not is_junction(link):
                raise JunctionError(
                    f"expected junction, found real path: {old_rel}"
                )
            actual = junction_target(link)
            if actual != expected:
                raise JunctionError(
                    f"wrong target for {old_rel}: {actual} != {expected}"
                )
            # Identity check: same file reachable both ways when possible.
            probe = _first_file(expected)
            if probe is not None:
                via_new = probe
                via_old = link / probe.relative_to(expected)
                if not via_old.is_file():
                    raise JunctionError(
                        f"probe not reachable via junction: {via_old}"
                    )
                if via_old.stat().st_size != via_new.stat().st_size:
                    raise JunctionError(
                        f"size mismatch through junction for {probe.name}"
                    )
            print(f"ok: {old_rel} -> {new_rel}")
        except JunctionError as e:
            print(f"FAIL: {e}", file=sys.stderr)
            errors += 1
    return 1 if errors else 0


def _first_file(directory: Path, limit_depth: int = 3) -> Path | None:
    if not directory.is_dir():
        return None
    for depth, dirpath, _dirnames, filenames in _walk_limited(directory, limit_depth):
        for name in filenames:
            p = Path(dirpath) / name
            if p.is_file():
                return p
    return None


def _walk_limited(root: Path, max_depth: int):
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        rel = Path(dirpath).relative_to(root)
        depth = 0 if str(rel) == "." else len(rel.parts)
        yield depth, dirpath, dirnames, filenames
        if depth >= max_depth:
            dirnames.clear()


def cmd_remove(
    root: Path, *, phase: str | None, dry_run: bool
) -> int:
    rows = selectable_rows(load_path_map(root), phase=phase)
    # Also remove registry entries for the same selection.
    if not rows:
        print("remove: nothing to do")
        return 0
    errors = 0
    for r in rows:
        old_rel = r["old_path"].strip()
        link = root / old_rel.replace("\\", "/")
        print(f"remove: {old_rel}{' (dry-run)' if dry_run else ''}")
        if dry_run:
            continue
        try:
            remove_junction(link)
            strip_git_exclude(root, old_rel)
            drop_registry(root, old_rel)
        except JunctionError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            errors += 1
    return 1 if errors else 0


def cmd_status(root: Path, *, phase: str | None) -> int:
    rows = selectable_rows(load_path_map(root), phase=phase)
    pending = [
        r
        for r in load_path_map(root)
        if (r.get("junction") or "").strip().lower() == "yes"
        and (r.get("status") or "").strip().lower() == "pending"
        and _phase_matches(r.get("phase") or "", phase)
    ]
    print(f"moved junction rows: {len(rows)}")
    print(f"pending junction rows: {len(pending)}")
    for r in rows:
        old_rel = r["old_path"].strip()
        new_rel = r["new_path"].strip()
        link = root / old_rel.replace("\\", "/")
        expected = _abs_new(root, new_rel)
        if is_junction(link):
            actual = junction_target(link)
            state = "ok" if actual == expected else f"WRONG->{actual}"
        elif link.exists():
            state = "REAL_DIR"
        else:
            state = "MISSING"
        print(f"  [{state}] {old_rel} -> {new_rel}")
    reg = load_registry(root)
    print(f"registry rows: {len(reg)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Workbench root (default: search for .sst-workbench-root)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    def add_phase(sp: argparse.ArgumentParser) -> None:
        sp.add_argument(
            "--phase",
            default=None,
            help="Only rows whose phase field contains this token (e.g. SP04)",
        )

    c = sub.add_parser("create", help="Create junctions for moved rows")
    add_phase(c)
    c.add_argument("--dry-run", action="store_true")

    v = sub.add_parser("verify", help="Verify junction identity")
    add_phase(v)

    r = sub.add_parser("remove", help="Remove junctions (never deletes targets)")
    add_phase(r)
    r.add_argument("--dry-run", action="store_true")

    s = sub.add_parser("status", help="Show junction status")
    add_phase(s)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = (args.root.resolve() if args.root else find_workbench_root())
    if args.command == "create":
        return cmd_create(root, phase=args.phase, dry_run=args.dry_run)
    if args.command == "verify":
        return cmd_verify(root, phase=args.phase)
    if args.command == "remove":
        return cmd_remove(root, phase=args.phase, dry_run=args.dry_run)
    if args.command == "status":
        return cmd_status(root, phase=args.phase)
    raise JunctionError(f"unknown command: {args.command}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except JunctionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
