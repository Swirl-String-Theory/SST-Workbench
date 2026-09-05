"""SP09: rename version directories to ``<catalog_id>-v…`` and install level-2 junctions.

Default is a dry run. ``--apply --family A042`` does one family: git mv, rewrite
FAMILY.yaml ``directory:`` fields, leave ``project.json`` ``legacy_dir`` untouched,
then replace the stage-1 root junction with a real directory of per-version junctions.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import catalog_metadata as cm  # noqa: E402
import junctions as jn  # noqa: E402

ROOT_MARKER = ".sst-workbench-root"


def find_root(start: Path | None = None) -> Path:
    cur = (start or Path(__file__)).resolve()
    if cur.is_file():
        cur = cur.parent
    for p in [cur, *cur.parents]:
        if (p / ROOT_MARKER).is_file():
            return p
    raise SystemExit(f"Could not find {ROOT_MARKER}")


def rewrite_family_yaml_directories(text: str, mapping: dict[str, str]) -> str:
    for old, new in mapping.items():
        text = text.replace(f'directory: "{old}"', f'directory: "{new}"')
    return text


def family_legacy_root(fam: cm.Family) -> str | None:
    """Single-component legacy path that currently junctions at the family, if any."""
    singles = [
        p.replace("\\", "/")
        for p in fam.legacy_paths
        if "/" not in p.replace("\\", "/")
    ]
    return singles[0] if singles else None


def git_mv(root: Path, src: Path, dest: Path) -> None:
    subprocess.run(
        ["git", "mv", str(src), str(dest)],
        cwd=root,
        check=True,
    )


def install_level2(
    root: Path,
    fam: cm.Family,
    mapping: dict[str, str],
    *,
    dry_run: bool,
) -> None:
    """Replace a stage-1 family junction with per-version junctions.

    ``mapping`` is current-dir -> short-dir. After git mv the short dir is on disk
    and ``project.json`` ``legacy_dir`` still names the old folder.
    """
    old_root = family_legacy_root(fam)
    if not old_root:
        print(f"  level2: skip (no single-component legacy root)")
        return
    link = root / old_root
    pairs: list[tuple[str, Path]] = []
    for v in fam.versions:
        pj = fam.path / mapping[v.directory] / "project.json"
        if dry_run:
            pj = fam.path / v.directory / "project.json"
        data = json.loads(pj.read_text(encoding="utf-8")) if pj.is_file() else {}
        legacy = (data.get("legacy_dir") or v.directory).strip()
        target = fam.path / mapping[v.directory]
        pairs.append((legacy, target))

    print(f"  level2: {old_root}/  ({len(pairs)} version junctions)")
    if dry_run:
        for legacy, target in pairs:
            print(f"    {old_root}/{legacy} -> {target.relative_to(root).as_posix()}")
        return

    if jn.is_junction(link):
        jn.remove_junction(link)
    link.mkdir(parents=True, exist_ok=True)
    jn.ensure_git_exclude(root, old_root)
    for legacy, target in pairs:
        child = link / legacy
        if child.exists() or jn.is_junction(child):
            if jn.is_junction(child) and jn.junction_target(child) == target.resolve():
                continue
            raise jn.JunctionError(f"level2 path exists: {child}")
        jn.create_junction(child, target)
        child_rel = f"{old_root}/{legacy}"
        jn.ensure_git_exclude(root, child_rel)
        jn.upsert_registry(root, old_path=child_rel, target=target, phase="SP09")


def rename_family(root: Path, fam: cm.Family, *, apply: bool) -> dict[str, str]:
    mapping = cm.short_names_for_family(fam)
    already = [old for old, new in mapping.items() if old == new]
    pending = {old: new for old, new in mapping.items() if old != new}
    print(f"{fam.catalog_id} {fam.path.relative_to(root).as_posix()}")
    for old, new in mapping.items():
        mark = "already" if old == new else "rename"
        print(f"  [{mark}] {old} -> {new}")
    if not pending:
        return mapping
    if not apply:
        install_level2(root, fam, mapping, dry_run=True)
        return mapping

    for old, new in pending.items():
        src = fam.path / old
        dest = fam.path / new
        if dest.exists():
            raise SystemExit(f"target exists: {dest}")
        git_mv(root, src, dest)
    yaml_path = fam.path / "FAMILY.yaml"
    yaml_path.write_text(
        rewrite_family_yaml_directories(yaml_path.read_text(encoding="utf-8"), pending),
        encoding="utf-8",
    )
    install_level2(root, fam, mapping, dry_run=False)
    return mapping


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--family", help="catalog id, e.g. A042")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    root = find_root()
    families = cm.discover()
    if args.family:
        families = [f for f in families if f.catalog_id == args.family]
        if not families:
            print(f"no family {args.family}", file=sys.stderr)
            return 1
        if len(families) > 1:
            print(
                f"{args.family} is reused across domains; pass is unique here? "
                f"{[f.domain for f in families]}",
                file=sys.stderr,
            )
            # Prefer 01_research when the user names a bare id.
            families = [f for f in families if f.domain == "01_research"] or families[:1]

    for fam in families:
        if not fam.versions:
            continue
        rename_family(root, fam, apply=args.apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
