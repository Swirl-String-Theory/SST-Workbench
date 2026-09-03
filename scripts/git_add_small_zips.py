"""Pack missing sibling output zips and git add -f every zip under 50 MiB.

Restore_Archives and files at or above 50 MiB stay local. Archives in
[50 MiB, 500 MiB) are split into tracked ``*.zip.partNN`` pieces.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))

import output_zip_policy as pol


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=WB,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def force_add(path: Path) -> None:
    rel = str(path.relative_to(WB)).replace("\\", "/")
    r = git("add", "-f", "--", rel)
    if r.returncode != 0:
        raise SystemExit(r.stderr or r.stdout or f"git add failed: {rel}")


def main() -> int:
    print("== pack missing sibling *_outputs.zip ==")
    created = pol.ensure_sibling_output_zips(WB)
    for p in created:
        print(f"  packed {p.stat().st_size / (1024 * 1024):.2f} MB  {p.relative_to(WB)}")
    if not created:
        print("  (none missing)")

    print("== split 50-500 MiB output zips; collect git paths ==")
    to_add: list[Path] = []
    seen: set[Path] = set()
    for z in pol.iter_commitable_zips(WB):
        for item in pol.prepare_output_archive_for_git(z):
            if item not in seen:
                seen.add(item)
                to_add.append(item)
        sidecar = Path(str(z) + ".sha256")
        if sidecar.is_file() and sidecar not in seen:
            seen.add(sidecar)
            to_add.append(sidecar)

    for z in WB.rglob("*_outputs.zip"):
        if not z.is_file() or "Restore_Archives" in z.parts:
            continue
        kind = pol.output_zip_class(z.stat().st_size)
        if kind != "parts":
            continue
        part1 = pol.part_path(z, 1)
        if part1.is_file():
            continue
        print(f"  split {z.stat().st_size / (1024 * 1024):.1f} MB  {z.relative_to(WB)}")
        for item in pol.prepare_output_archive_for_git(z):
            if item not in seen:
                seen.add(item)
                to_add.append(item)

    print(f"== git add -f {len(to_add)} files under 50 MiB ==")
    over = [p for p in to_add if p.is_file() and p.suffix.lower() == ".zip" and p.stat().st_size >= pol.SPLIT_MIN_BYTES]
    if over:
        print("refusing zip >= 50 MiB:")
        for p in over:
            print(f"  {p.stat().st_size / (1024 * 1024):.1f} MB  {p.relative_to(WB)}")
        raise SystemExit(1)
    for p in to_add:
        if p.is_file():
            force_add(p)
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
