"""Fast stage: git add -A with longpaths, then unstage files >= limit."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=WB,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit-mb", type=float, default=49.0)
    args = ap.parse_args()
    limit = int(args.limit_mb * 1024 * 1024)

    run("reset")

    add = subprocess.run(
        ["git", "-c", "core.longpaths=true", "add", "-A"],
        cwd=WB,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if add.returncode != 0:
        print(add.stderr or add.stdout, file=sys.stderr)
        return add.returncode

    staged = run("diff", "--cached", "--name-only", "-z")
    skipped_large: list[tuple[str, int]] = []
    for rel in staged.stdout.split("\0"):
        if not rel:
            continue
        p = WB / rel
        if not p.is_file():
            continue
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size >= limit:
            skipped_large.append((rel, size))
            run("reset", "HEAD", "--", rel)

    summary = run("diff", "--cached", "--stat")
    print(summary.stdout)
    if summary.stderr:
        print(summary.stderr, file=sys.stderr)
    print(f"Skipped >={args.limit_mb}MB: {len(skipped_large)}")
    for rel, sz in sorted(skipped_large, key=lambda x: -x[1]):
        print(f"  {sz / 1024 / 1024:6.1f} MB  {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
