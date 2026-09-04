"""Build file_manifest.csv and checksums.sha256 for SP00 freeze provenance."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

WB = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = WB / "10_docs" / "migration" / "file_manifest.csv"
DEFAULT_CHECKSUMS = WB / "10_docs" / "migration" / "checksums.sha256"

SKIP_DIR_NAMES = frozenset({".git", ".tmp.driveupload"})
MANIFEST_FIELDS = ["path", "size", "mtime", "tracked", "ignored"]


def _git_lines(root: Path, *args: str) -> list[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr}")
    return [ln for ln in proc.stdout.splitlines() if ln]


def tracked_set(root: Path) -> set[str]:
    return {p.replace("\\", "/") for p in _git_lines(root, "ls-files")}


def ignored_set(root: Path, candidates: Iterable[str]) -> set[str]:
    """Return the subset of candidates that git check-ignore accepts."""
    cand_list = list(candidates)
    if not cand_list:
        return set()
    ignored: set[str] = set()
    # Batch to avoid command-line limits
    batch = 200
    for i in range(0, len(cand_list), batch):
        chunk = cand_list[i : i + batch]
        proc = subprocess.run(
            ["git", "check-ignore", "-z", "--stdin"],
            cwd=root,
            input="\0".join(chunk) + "\0",
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
        # exit 0 = some ignored, 1 = none ignored
        if proc.stdout:
            for p in proc.stdout.split("\0"):
                if p:
                    ignored.add(p.replace("\\", "/"))
    return ignored


def iter_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in SKIP_DIR_NAMES and not d.startswith(".tmp.driveupload")
        ]
        base = Path(dirpath)
        for name in filenames:
            yield base / name


def rel_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def file_mtime_iso(path: Path) -> str:
    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def build_manifest(root: Path) -> list[dict[str, str]]:
    tracked = tracked_set(root)
    rows: list[dict[str, str]] = []
    rels: list[str] = []
    meta: dict[str, tuple[int, str]] = {}
    for path in iter_files(root):
        try:
            st = path.stat()
        except OSError:
            continue
        rel = rel_posix(path, root)
        rels.append(rel)
        meta[rel] = (st.st_size, file_mtime_iso(path))
    ignored = ignored_set(root, [r for r in rels if r not in tracked])
    for rel in sorted(rels):
        size, mtime = meta[rel]
        is_tracked = rel in tracked
        is_ignored = rel in ignored
        rows.append(
            {
                "path": rel,
                "size": str(size),
                "mtime": mtime,
                "tracked": "yes" if is_tracked else "no",
                "ignored": "yes" if is_ignored else "no",
            }
        )
    return rows


def write_manifest(rows: list[dict[str, str]], out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        w.writeheader()
        w.writerows(rows)
    return out


def build_checksums(root: Path, rows: list[dict[str, str]], min_ignored_bytes: int = 1_000_000) -> list[tuple[str, str]]:
    """SHA-256 for every tracked file plus ignored files above min_ignored_bytes."""
    out: list[tuple[str, str]] = []
    for row in rows:
        path = root / row["path"]
        tracked = row["tracked"] == "yes"
        ignored = row["ignored"] == "yes"
        size = int(row["size"])
        if not tracked and not (ignored and size >= min_ignored_bytes):
            continue
        if not path.is_file():
            continue
        digest = sha256_file(path)
        out.append((digest, row["path"]))
    return out


def write_checksums(entries: list[tuple[str, str]], out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        for digest, path in entries:
            f.write(f"{digest}  {path}\n")
    return out


def load_checksums(path: Path) -> dict[str, str]:
    """Map path -> hex digest."""
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, _, rest = line.partition("  ")
        if not rest:
            digest, _, rest = line.partition(" ")
        result[rest.strip().replace("\\", "/")] = digest.strip()
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="SP00 file_manifest.csv + checksums.sha256")
    p.add_argument("--root", type=Path, default=WB)
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p.add_argument("--checksums", type=Path, default=DEFAULT_CHECKSUMS)
    p.add_argument("--skip-checksums", action="store_true")
    p.add_argument("--min-ignored-bytes", type=int, default=1_000_000)
    args = p.parse_args(argv)

    print("Building file_manifest.csv ...")
    rows = build_manifest(args.root)
    write_manifest(rows, args.manifest)
    tracked_n = sum(1 for r in rows if r["tracked"] == "yes")
    print(f"Wrote {args.manifest} ({len(rows)} files, {tracked_n} tracked)")

    if not args.skip_checksums:
        print("Building checksums.sha256 (tracked + ignored >1MB) ...")
        entries = build_checksums(args.root, rows, min_ignored_bytes=args.min_ignored_bytes)
        write_checksums(entries, args.checksums)
        print(f"Wrote {args.checksums} ({len(entries)} digests)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
