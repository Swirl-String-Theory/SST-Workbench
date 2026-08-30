"""One-shot apply: copy zips, split 50-500MB output zips, untrack git index."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))

import consolidate_archives as ca
import output_zip_policy as pol
import workbench_hygiene as hy


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=WB,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def copy_family_zips() -> int:
    n = 0
    for src, dest in hy.plan_family_zip_copies(WB, hy.DOWNLOADS_DIR):
        action = hy.copy_if_missing(src, dest)
        print(f"  {action}: {dest.relative_to(WB)}")
        n += 1
    return n


def ingest_downloads_to_restore() -> int:
    plans = ca.plan_downloads_copy(hy.DOWNLOADS_DIR)
    rows = ca.apply_plan(plans, apply=True)
    print(f"Restore_Archives downloads ops: {len(rows)}")
    return len(rows)


def split_existing_output_zips() -> list[Path]:
    added: list[Path] = []
    for z in WB.rglob("*_outputs.zip"):
        if not z.is_file():
            continue
        if "Restore_Archives" in z.parts:
            continue
        kind = pol.output_zip_class(z.stat().st_size)
        print(f"  {kind} {z.stat().st_size / (1024*1024):.1f}MB {z.relative_to(WB)}")
        if kind == "parts":
            added.extend(pol.prepare_output_archive_for_git(z))
        elif kind == "single":
            added.append(z)
    return added


def untrack_index() -> int:
    listed = git("ls-files")
    rels = [ln for ln in listed.stdout.splitlines() if ln]
    drop = [rel for rel in rels if hy.should_untrack_rel(rel, WB, pol)]
    keep = [rel for rel in rels if not hy.should_untrack_rel(rel, WB, pol)]
    print(f"tracked={len(rels)} untrack={len(drop)} keep={len(keep)}")
    if not drop:
        return 0
    list_file = WB / ".git" / "untrack-outputs.txt"
    list_file.write_text("\n".join(drop) + "\n", encoding="utf-8")
    # batch to avoid command-line limits
    r = git("rm", "-r", "--cached", "--ignore-unmatch", f"--pathspec-from-file={list_file}")
    if r.returncode != 0:
        print(r.stderr or r.stdout)
        raise SystemExit(r.returncode)
    print(r.stdout[-2000:] if r.stdout else "git rm --cached done")
    return len(drop)


def relocate_swirl() -> None:
    delete_root = hy.DELETE_ROOT
    for rel in hy.SWIRL_RELOCATE:
        src = WB / rel
        if not src.is_dir():
            print(f"  skip missing {rel}")
            continue
        if not hy.source_zip_present(WB, rel):
            print(f"  SKIP no source zip yet: {rel}")
            continue
        dest = hy.relocate_to_delete(src, WB, delete_root)
        print(f"  moved {rel} -> {dest}")


def main() -> int:
    print("== copy family source zips from Downloads ==")
    copy_family_zips()
    print("== copy Downloads source zips into Restore_Archives ==")
    ingest_downloads_to_restore()
    print("== classify/split sibling *_outputs.zip ==")
    git_add = split_existing_output_zips()
    print("== git rm --cached unpacked outputs / non-sibling zips ==")
    untrack_index()
    print("== relocate swirl patch folders if zips present ==")
    relocate_swirl()
    print("== force-add commitable output artifacts ==")
    for p in git_add:
        if not p.is_file():
            continue
        if not pol.is_commitable_output_artifact(p) and not p.name.endswith(".parts.json"):
            continue
        rel = str(p.relative_to(WB)).replace("\\", "/")
        git("add", "-f", "--", rel)
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
