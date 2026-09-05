"""SP09: rename version directories to ``<catalog_id>-v…`` and repair junctions.

Default is a dry run. ``--apply`` does every family:

1. ``git mv`` version directories; rewrite FAMILY.yaml ``directory:`` fields.
2. Retarget existing junctions whose target was the old version path.
3. Convert stage-1 family-root junctions (target = family dir) into level-2
   scaffolds, or retarget them when the old root *was* the version itself.
4. Rewrite ``path_map.csv`` ``new_path`` values that pointed at the old dirs.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import catalog_metadata as cm  # noqa: E402
import junctions as jn  # noqa: E402

ROOT_MARKER = ".sst-workbench-root"
PATH_MAP_REL = Path("10_docs") / "migration" / "path_map.csv"
PATH_MAP_FIELDS = (
    "old_path", "new_path", "domain", "letter", "catalog_id",
    "kind", "phase", "junction", "status", "note",
)
NEVER_CONVERT = {
    "gui", "GUI", "scripts", "KnotPlot", "03_data", "07_scripts",
    "Restore_Archives", "DELETE", "experiments", "to_be_processed",
    "08_third_party", "09_archive", "10_docs", "06_templates",
}


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
    """Single-component legacy path, if any (not a shared container like gui/)."""
    singles = [
        p.replace("\\", "/")
        for p in fam.legacy_paths
        if "/" not in p.replace("\\", "/")
    ]
    singles = [s for s in singles if s not in NEVER_CONVERT]
    return singles[0] if singles else None


def _has_project_json(path: Path) -> bool:
    return (path / "project.json").is_file()


def absorb_leftover(src: Path, dest: Path) -> None:
    """Move leftover untracked children (``.venv``, ``build``, …) after a partial rename.

    On Windows ``git mv`` often copies tracked files into ``dest`` but cannot
    remove ``src`` while a ``.venv`` or file lock remains. The leftover husk
    then blocks the next attempt because ``dest`` already exists.
    """
    if not src.exists() or src.resolve() == dest.resolve():
        return
    dest.mkdir(parents=True, exist_ok=True)
    try:
        children = list(src.iterdir())
    except OSError as exc:
        print(f"    leftover: cannot list {src.name}: {exc}")
        return
    for child in children:
        target = dest / child.name
        if target.exists():
            if child.is_dir() and target.is_dir():
                absorb_leftover(child, target)
                try:
                    child.rmdir()
                except OSError:
                    pass
            continue
        try:
            child.rename(target)
        except OSError as exc:
            print(f"    leftover: skip {child.name}: {exc}")
    try:
        src.rmdir()
    except OSError:
        pass


def git_add_rename(root: Path, src: Path, dest: Path) -> None:
    subprocess.run(
        ["git", "add", "-A", "--", str(src), str(dest)],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def git_mv(root: Path, src: Path, dest: Path) -> None:
    last: subprocess.CalledProcessError | None = None
    for attempt in range(1, 8):
        if dest.exists() and _has_project_json(dest):
            absorb_leftover(src, dest)
            git_add_rename(root, src, dest)
            return
        proc = subprocess.run(
            ["git", "mv", str(src), str(dest)],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            absorb_leftover(src, dest)
            return
        last = subprocess.CalledProcessError(
            proc.returncode, proc.args, proc.stdout, proc.stderr,
        )
        err = (proc.stderr or proc.stdout or "").strip()
        print(f"  git mv retry {attempt}/7: {src.name}: {err}")
        time.sleep(0.4 * attempt)
        if dest.exists() and not src.exists():
            git_add_rename(root, src, dest)
            return
    if dest.exists() and _has_project_json(dest):
        absorb_leftover(src, dest)
        git_add_rename(root, src, dest)
        print(f"  recovered partial rename {src.name} -> {dest.name}")
        return
    assert last is not None
    raise last


def load_path_map(root: Path) -> list[dict[str, str]]:
    path = root / PATH_MAP_REL
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def save_path_map(root: Path, rows: list[dict[str, str]]) -> None:
    path = root / PATH_MAP_REL
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(PATH_MAP_FIELDS))
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in PATH_MAP_FIELDS})


def _norm(p: str) -> str:
    return p.replace("\\", "/").strip().strip("/")


def rewrite_path_map_version_targets(
    rows: list[dict[str, str]], fam: cm.Family, mapping: dict[str, str], root: Path,
) -> int:
    fam_rel = _norm(str(fam.path.relative_to(root)))
    n = 0
    for old, new in mapping.items():
        targets = {f"{fam_rel}/{old}", f"{fam_rel}/{new}"}
        pj = fam.path / new / "project.json"
        if not pj.is_file():
            pj = fam.path / old / "project.json"
        if pj.is_file():
            try:
                legacy = (json.loads(pj.read_text(encoding="utf-8")).get("legacy_dir") or "").strip()
            except json.JSONDecodeError:
                legacy = ""
            if legacy:
                targets.add(f"{fam_rel}/{legacy}")
        repl = f"{fam_rel}/{new}"
        for r in rows:
            if _norm(r.get("new_path") or "") in targets and _norm(r.get("new_path") or "") != repl:
                r["new_path"] = repl
                n += 1
    return n


def upsert_level2_path_map_row(
    rows: list[dict[str, str]],
    *,
    old_path: str,
    new_path: str,
    fam: cm.Family,
) -> None:
    key = _norm(old_path)
    for r in rows:
        if _norm(r.get("old_path") or "") == key:
            r["new_path"] = new_path
            r["junction"] = "yes"
            r["status"] = "verified"
            if "SP09" not in (r.get("phase") or ""):
                r["phase"] = "SP09"
            return
    rows.append({
        "old_path": key,
        "new_path": new_path,
        "domain": fam.domain,
        "letter": fam.letter,
        "catalog_id": fam.catalog_id,
        "kind": "code",
        "phase": "SP09",
        "junction": "yes",
        "status": "verified",
        "note": "level-2 version junction",
    })


def mark_family_root_as_scaffold(rows: list[dict[str, str]], old_root: str) -> None:
    key = _norm(old_root)
    for r in rows:
        if _norm(r.get("old_path") or "") != key:
            continue
        r["junction"] = "no"
        phase = (r.get("phase") or "").strip()
        if phase in {"", "-"}:
            r["phase"] = "SP09"
        elif "SP09" not in phase and " / " not in phase:
            r["phase"] = f"{phase} / SP09"
        note = r.get("note") or ""
        if "level-2" not in note:
            r["note"] = (note + "; SP09 level-2 scaffold root").strip("; ")
        return


def iter_junction_links(root: Path) -> list[Path]:
    links: list[Path] = []
    for r in jn.load_registry(root):
        p = root / _norm(r.get("old_path") or "")
        if jn.is_junction(p):
            links.append(p)
    for parent in root.iterdir():
        if not parent.is_dir():
            continue
        if jn.is_junction(parent):
            links.append(parent)
            continue
        try:
            children = list(parent.iterdir())
        except OSError:
            continue
        for child in children:
            if child.is_dir() and jn.is_junction(child):
                links.append(child)
    # unique by resolved path
    seen: set[Path] = set()
    out: list[Path] = []
    for p in links:
        try:
            key = p.resolve()
        except OSError:
            key = p
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def detach_junctions_targeting(root: Path, targets: set[Path]) -> list[tuple[Path, Path]]:
    """Remove junctions whose target is in ``targets``. Windows cannot rename a
    directory while a junction still points at it (or at its parent family)."""
    want = {t.resolve() for t in targets}
    detached: list[tuple[Path, Path]] = []
    for link in iter_junction_links(root):
        try:
            actual = jn.junction_target(link)
        except OSError:
            continue
        if actual not in want:
            continue
        print(f"  detach {link.relative_to(root).as_posix()}")
        jn.remove_junction(link)
        detached.append((link, actual))
    return detached


def retarget_junction(link: Path, target: Path) -> None:
    if jn.is_junction(link):
        current = jn.junction_target(link)
        if current == target.resolve():
            return
        jn.remove_junction(link)
    elif link.exists():
        raise jn.JunctionError(f"refusing to replace non-junction: {link}")
    jn.create_junction(link, target)


def version_pairs(
    fam: cm.Family, mapping: dict[str, str], *, after_rename: bool,
) -> list[tuple[str, Path]]:
    pairs = []
    for old, new in mapping.items():
        src_dir = new if after_rename else old
        pj = fam.path / src_dir / "project.json"
        if not pj.is_file() and after_rename:
            pj = fam.path / old / "project.json"
        data = json.loads(pj.read_text(encoding="utf-8")) if pj.is_file() else {}
        legacy = (data.get("legacy_dir") or old).strip()
        pairs.append((legacy, fam.path / new))
    return pairs


def retarget_junctions_for_mapping(
    root: Path, fam: cm.Family, mapping: dict[str, str],
) -> int:
    """Repoint any junction whose target was fam/old_dir to fam/new_dir."""
    n = 0
    fam_res = fam.path.resolve()
    registry = jn.load_registry(root)
    wanted: dict[Path, Path] = {}
    for old, new in mapping.items():
        dest = fam_res / new
        wanted[fam_res / old] = dest
        pj = fam.path / new / "project.json"
        if not pj.is_file():
            pj = fam.path / old / "project.json"
        if pj.is_file():
            try:
                legacy = (json.loads(pj.read_text(encoding="utf-8")).get("legacy_dir") or "").strip()
            except json.JSONDecodeError:
                legacy = ""
            if legacy:
                wanted[fam_res / legacy] = dest

    def consider(link: Path) -> None:
        nonlocal n
        if not jn.is_junction(link):
            return
        try:
            actual = jn.junction_target(link)
        except OSError:
            return
        dest = wanted.get(actual)
        if dest is None:
            return
        print(f"  retarget {link.relative_to(root).as_posix()} -> {dest.relative_to(root).as_posix()}")
        retarget_junction(link, dest)
        jn.upsert_registry(
            root, old_path=str(link.relative_to(root).as_posix()),
            target=dest, phase="SP09",
        )
        n += 1

    for r in registry:
        consider(root / _norm(r.get("old_path") or ""))
    # Mixed-container real dirs from SP06 already hold per-version junctions
    # that may not all be in the registry under the name we expect.
    names: set[str] = set()
    for old, new in mapping.items():
        names.add(old)
        pj = fam.path / new / "project.json"
        if not pj.is_file():
            pj = fam.path / old / "project.json"
        if pj.is_file():
            try:
                legacy = (json.loads(pj.read_text(encoding="utf-8")).get("legacy_dir") or "").strip()
            except json.JSONDecodeError:
                legacy = ""
            if legacy:
                names.add(legacy)
    for name in names:
        for parent in root.iterdir():
            if not parent.is_dir() or jn.is_junction(parent):
                continue
            consider(parent / name)
    return n


def should_retarget_root(old_root: str, pairs: list[tuple[str, Path]]) -> bool:
    """True when the stage-1 root *was* the version directory itself."""
    return len(pairs) == 1 and pairs[0][0] == Path(old_root).name


def _install_root_junction(
    root: Path, old_root: str, dest: Path, rows: list[dict[str, str]],
) -> None:
    link = root / old_root
    jn.create_junction(link, dest)
    jn.ensure_git_exclude(root, old_root)
    jn.upsert_registry(root, old_path=old_root, target=dest, phase="SP09")
    for r in rows:
        if _norm(r.get("old_path") or "") == _norm(old_root):
            r["new_path"] = dest.relative_to(root).as_posix()
            r["junction"] = "yes"
            if "SP09" not in (r.get("phase") or ""):
                phase = (r.get("phase") or "").strip()
                r["phase"] = "SP09" if phase in {"", "-"} else f"{phase} / SP09"


def convert_family_root(
    root: Path,
    fam: cm.Family,
    mapping: dict[str, str],
    rows: list[dict[str, str]],
    *,
    dry_run: bool,
) -> None:
    old_root = family_legacy_root(fam)
    if not old_root:
        return
    link = root / old_root
    pairs = version_pairs(fam, mapping, after_rename=not dry_run)

    if should_retarget_root(old_root, pairs):
        dest = pairs[0][1]
        if dry_run:
            print(f"  retarget-root {old_root} -> {dest.relative_to(root).as_posix()}")
            return
        if jn.is_junction(link):
            print(f"  retarget-root {old_root} -> {dest.relative_to(root).as_posix()}")
            retarget_junction(link, dest)
            jn.upsert_registry(root, old_path=old_root, target=dest, phase="SP09")
            for r in rows:
                if _norm(r.get("old_path") or "") == _norm(old_root):
                    r["new_path"] = dest.relative_to(root).as_posix()
            return
        if link.exists():
            child = link / pairs[0][0]
            extras = [p for p in link.iterdir() if p.name != pairs[0][0]]
            if extras:
                print(f"  level2: keep scaffold {old_root}/ (extra children)")
            else:
                print(f"  retarget-root collapse {old_root} -> {dest.relative_to(root).as_posix()}")
                if jn.is_junction(child):
                    jn.remove_junction(child)
                elif child.exists():
                    raise jn.JunctionError(f"cannot collapse non-junction child: {child}")
                try:
                    link.rmdir()
                except OSError as exc:
                    print(f"    collapse skip (not empty): {exc}")
                else:
                    _install_root_junction(root, old_root, dest, rows)
                    return
        else:
            print(f"  retarget-root {old_root} -> {dest.relative_to(root).as_posix()}")
            _install_root_junction(root, old_root, dest, rows)
            return

    if not link.exists() and not jn.is_junction(link):
        print(f"  level2: create {old_root}/")
        if dry_run:
            for legacy, target in pairs:
                print(f"    {old_root}/{legacy} -> {target.relative_to(root).as_posix()}")
            return
        link.mkdir(parents=True, exist_ok=True)
        jn.ensure_git_exclude(root, old_root)
        mark_family_root_as_scaffold(rows, old_root)
        for legacy, dest in pairs:
            child = link / legacy
            jn.create_junction(child, dest)
            child_rel = f"{old_root}/{legacy}"
            jn.ensure_git_exclude(root, child_rel)
            jn.upsert_registry(root, old_path=child_rel, target=dest, phase="SP09")
            upsert_level2_path_map_row(
                rows, old_path=child_rel,
                new_path=dest.relative_to(root).as_posix(), fam=fam,
            )
        return
    if not jn.is_junction(link):
        # Already a real dir (shared container or previous convert). Add children.
        print(f"  level2: add children under real {old_root}/")
        if dry_run:
            for legacy, target in pairs:
                print(f"    {old_root}/{legacy} -> {target.relative_to(root).as_posix()}")
            return
        for legacy, target in pairs:
            child = link / legacy
            if jn.is_junction(child):
                retarget_junction(child, target)
            elif child.exists():
                print(f"    skip existing non-junction {old_root}/{legacy}")
                continue
            else:
                jn.create_junction(child, target)
            child_rel = f"{old_root}/{legacy}"
            jn.ensure_git_exclude(root, child_rel)
            jn.upsert_registry(root, old_path=child_rel, target=target, phase="SP09")
            upsert_level2_path_map_row(
                rows, old_path=child_rel,
                new_path=target.relative_to(root).as_posix(), fam=fam,
            )
        return

    target = jn.junction_target(link)
    fam_res = fam.path.resolve()
    if target != fam_res:
        print(f"  level2: skip {old_root} (owned by {target.relative_to(root).as_posix()})")
        return

    # Junction currently points at the family directory.
    if len(pairs) == 1 and pairs[0][0] == Path(old_root).name:
        dest = pairs[0][1]
        print(f"  retarget-root {old_root} -> {dest.relative_to(root).as_posix()}")
        if dry_run:
            return
        retarget_junction(link, dest)
        jn.upsert_registry(root, old_path=old_root, target=dest, phase="SP09")
        for r in rows:
            if _norm(r.get("old_path") or "") == _norm(old_root):
                r["new_path"] = dest.relative_to(root).as_posix()
        return

    print(f"  level2: convert {old_root}/ ({len(pairs)} version junctions)")
    if dry_run:
        for legacy, dest in pairs:
            print(f"    {old_root}/{legacy} -> {dest.relative_to(root).as_posix()}")
        return
    jn.remove_junction(link)
    link.mkdir(parents=True, exist_ok=True)
    jn.ensure_git_exclude(root, old_root)
    mark_family_root_as_scaffold(rows, old_root)
    for legacy, dest in pairs:
        child = link / legacy
        if child.exists() or jn.is_junction(child):
            if jn.is_junction(child) and jn.junction_target(child) == dest.resolve():
                continue
            raise jn.JunctionError(f"level2 path exists: {child}")
        jn.create_junction(child, dest)
        child_rel = f"{old_root}/{legacy}"
        jn.ensure_git_exclude(root, child_rel)
        jn.upsert_registry(root, old_path=child_rel, target=dest, phase="SP09")
        upsert_level2_path_map_row(
            rows, old_path=child_rel,
            new_path=dest.relative_to(root).as_posix(), fam=fam,
        )


def versions_with_project(fam: cm.Family) -> list[cm.Version]:
    """Ignore leftover husks from a partial ``git mv`` (no ``project.json``)."""
    return [
        v for v in fam.versions
        if (fam.path / v.directory / "project.json").is_file()
    ]


def yaml_rewrite_map(fam: cm.Family, mapping: dict[str, str]) -> dict[str, str]:
    """Include ``legacy_dir`` names still sitting in FAMILY.yaml after a partial apply."""
    out = dict(mapping)
    for v in fam.versions:
        short = mapping[v.directory]
        pj = fam.path / v.directory / "project.json"
        try:
            data = json.loads(pj.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        legacy = (data.get("legacy_dir") or "").strip()
        if legacy:
            out[legacy] = short
    return out


def absorb_untracked_husks(root: Path, fam: cm.Family) -> None:
    """Merge version-looking dirs that lost their tracked files onto the short dest."""
    for child in list(fam.path.iterdir()):
        if not child.is_dir() or (child / "project.json").is_file():
            continue
        if not cm.VERSION_TOKEN.search(child.name):
            continue
        dest = fam.path / cm.short_directory_name(
            fam.catalog_id, cm.parse_version(child.name),
        )
        if not dest.exists() or dest.resolve() == child.resolve():
            continue
        if not _has_project_json(dest):
            continue
        print(f"  husk {child.name} -> {dest.name}")
        absorb_leftover(child, dest)
        git_add_rename(root, child, dest)


def rename_family_dirs(root: Path, fam: cm.Family, *, apply: bool) -> dict[str, str]:
    fam = replace(fam, versions=versions_with_project(fam))
    mapping = cm.short_names_for_family(fam)
    pending = {old: new for old, new in mapping.items() if old != new}
    print(f"{fam.catalog_id} {fam.path.relative_to(root).as_posix()}")
    for old, new in mapping.items():
        mark = "already" if old == new else "rename"
        print(f"  [{mark}] {old} -> {new}")
    if not apply:
        return mapping
    absorb_untracked_husks(root, fam)
    yaml_map = yaml_rewrite_map(fam, mapping)
    if pending:
        # Drop inbound junctions first: a family-root junction exposes every version
        # dir, and Windows then refuses git mv with "Permission denied".
        pending_paths = {fam.path / old for old in pending}
        detach_junctions_targeting(root, {fam.path, *pending_paths})
        for old, new in pending.items():
            src = fam.path / old
            dest = fam.path / new
            if not src.exists() and dest.exists():
                continue
            git_mv(root, src, dest)
    yaml_path = fam.path / "FAMILY.yaml"
    yaml_path.write_text(
        rewrite_family_yaml_directories(
            yaml_path.read_text(encoding="utf-8"),
            yaml_map,
        ),
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "-A", "--", str(fam.path.relative_to(root).as_posix())],
        cwd=root, check=True, capture_output=True, text=True,
    )
    return mapping


def install_nested_legacy_junctions(
    root: Path,
    fam: cm.Family,
    mapping: dict[str, str],
    rows: list[dict[str, str]],
    *,
    dry_run: bool,
) -> None:
    """Add ``legacy_dir`` junctions under shared real containers (SP06 splits)."""
    containers: list[Path] = []
    for lp in fam.legacy_paths:
        first = lp.replace("\\", "/").split("/")[0]
        if not first or first in NEVER_CONVERT:
            continue
        parent = root / first
        if parent.is_dir() and not jn.is_junction(parent):
            containers.append(parent)
    if not containers:
        return
    seen: set[Path] = set()
    uniq: list[Path] = []
    for c in containers:
        key = c.resolve()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(c)
    pairs = version_pairs(fam, mapping, after_rename=not dry_run)
    for legacy, dest in pairs:
        for container in uniq:
            child = container / legacy
            rel = f"{container.relative_to(root).as_posix()}/{legacy}"
            if dry_run:
                print(f"    nested {rel} -> {dest.relative_to(root).as_posix()}")
                continue
            if jn.is_junction(child):
                retarget_junction(child, dest)
            elif child.exists():
                continue
            else:
                print(f"  nested {rel} -> {dest.relative_to(root).as_posix()}")
                jn.create_junction(child, dest)
            jn.ensure_git_exclude(root, rel)
            jn.upsert_registry(root, old_path=rel, target=dest, phase="SP09")
            upsert_level2_path_map_row(
                rows, old_path=rel,
                new_path=dest.relative_to(root).as_posix(), fam=fam,
            )


def select_families(all_fams: list[cm.Family], catalog_id: str | None) -> list[cm.Family]:
    families = [f for f in all_fams if f.versions]
    if not catalog_id:
        return families
    matched = [f for f in families if f.catalog_id == catalog_id]
    if not matched:
        raise SystemExit(f"no family {catalog_id}")
    if len(matched) > 1:
        research = [f for f in matched if f.domain == "01_research"]
        return research or matched[:1]
    return matched


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--family", help="catalog id, e.g. A042")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    root = find_root()
    families = select_families(cm.discover(), args.family)
    mappings: list[tuple[cm.Family, dict[str, str]]] = []
    for fam in families:
        mappings.append((fam, rename_family_dirs(root, fam, apply=args.apply)))

    rows = load_path_map(root)
    path_edits = 0
    for fam, mapping in mappings:
        path_edits += rewrite_path_map_version_targets(rows, fam, mapping, root)

    if not args.apply:
        print("\n=== junction / path_map plan ===")
        for fam, mapping in mappings:
            convert_family_root(root, fam, mapping, rows, dry_run=True)
            install_nested_legacy_junctions(root, fam, mapping, rows, dry_run=True)
        print(f"path_map new_path rewrites (planned): {path_edits}")
        return 0

    retargeted = 0
    for fam, mapping in mappings:
        retargeted += retarget_junctions_for_mapping(root, fam, mapping)

    # Owners first (junction currently points at this family), then everyone
    # adds children under already-converted real dirs.
    for fam, mapping in mappings:
        convert_family_root(root, fam, mapping, rows, dry_run=False)
    for fam, mapping in mappings:
        convert_family_root(root, fam, mapping, rows, dry_run=False)
        install_nested_legacy_junctions(root, fam, mapping, rows, dry_run=False)

    save_path_map(root, rows)
    print(f"\nretargeted junctions: {retargeted}")
    print(f"path_map new_path rewrites: {path_edits}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except jn.JunctionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
