#!/usr/bin/env python3
"""Reorganize .cursor/plans into status folders with chronological root numbering.

Usage:
  python _reorganize_by_status.py --dry-run
  python _reorganize_by_status.py --apply
  python _reorganize_by_status.py --fix-links   # after moves; rewrite relative links
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

PLANS_ROOT = Path(__file__).resolve().parent
STATUS_DIRS = ("complete", "almost_complete", "not_done")
EPICS = ("paper_upgrade", "restructure", "vortexlab_v7x")

# README overrides win over YAML (paths relative to PLANS_ROOT, posix).
OVERRIDES: dict[str, str] = {
    # restructure — all DONE per README
    "restructure/SP00_freeze_and_provenance.plan.md": "complete",
    "restructure/SP01_path_resolver.plan.md": "complete",
    "restructure/SP02_compat_junction_layer.plan.md": "complete",
    "restructure/SP03_catalog_skeleton_and_hygiene.plan.md": "complete",
    "restructure/SP04_low_risk_moves.plan.md": "complete",
    "restructure/SP05_clean_family_moves.plan.md": "complete",
    "restructure/SP06_container_splits.plan.md": "complete",
    "restructure/SP07_knotplot_refactor.plan.md": "complete",
    "restructure/SP08_catalog_metadata_and_registry.plan.md": "complete",
    "restructure/SP09_version_rename_stage2.plan.md": "complete",
    "restructure/SP10_reproducibility_gate.plan.md": "complete",
    "restructure/SP11_decommission.plan.md": "complete",
    "restructure/RESTRUCTURE_EPIC.plan.md": "complete",
    "restructure/RESTRUCTURE_PLAN_v0.1.plan.md": "complete",
    "restructure/CATALOG_01_03_FREEZE.plan.md": "complete",
    # paper_upgrade
    "paper_upgrade/PU00_selftests.plan.md": "complete",
    "paper_upgrade/PU01_run_all_selftest_hook.plan.md": "complete",
    "paper_upgrade/PU01b_resume_and_heartbeat.plan.md": "complete",
    "paper_upgrade/PU02_certificate_adapters.plan.md": "complete",
    "paper_upgrade/PU02b_certificate_semantics.plan.md": "complete",
    "paper_upgrade/PU03_infra_d006_c006.plan.md": "complete",
    "paper_upgrade/PU04_primary_gates_a037_a034.plan.md": "complete",
    "paper_upgrade/PU04b_a037_numerics_ladder.plan.md": "complete",
    "paper_upgrade/PU04c_a037_paper_2505.plan.md": "complete",
    "paper_upgrade/PU04d_a034_dual_branch.plan.md": "complete",
    "paper_upgrade/PC00_certificate_contract.plan.md": "complete",
    "paper_upgrade/PAPER_UPGRADE_EPIC.plan.md": "almost_complete",
    "paper_upgrade/PRODUCTION_CERTIFICATION.plan.md": "almost_complete",
    "paper_upgrade/PU05_modal_a029_a035_a008.plan.md": "not_done",
    "paper_upgrade/PU06_phase_floquet_a030_a023_a031.plan.md": "not_done",
    "paper_upgrade/PU07_orchestrator_a038_a021.plan.md": "not_done",
    "paper_upgrade/PU08_optional_and_deferred.plan.md": "not_done",
    "paper_upgrade/PC01_d006_regression.plan.md": "not_done",
    "paper_upgrade/PC02_a037_v031.plan.md": "not_done",
    "paper_upgrade/PC03_a034_v021.plan.md": "not_done",
    "paper_upgrade/PC04_a038_v041.plan.md": "not_done",
    "paper_upgrade/PC05_provenance_ledger.plan.md": "not_done",
}

ROOT_UNKNOWN_OVERRIDES: dict[str, str] = {
    "falsifier_inventory_table_7c1e1d64.plan.md": "not_done",
    "outputs_zips_under_50mb.plan.md": "not_done",
    "clock_origin_independent_observable_p26.plan.md": "not_done",
}

SKIP_NAMES = {
    "_reorganize_by_status.py",
    "MANIFEST.json",
    "README.md",
}


def rel_posix(path: Path) -> str:
    return path.relative_to(PLANS_ROOT).as_posix()


def parse_todos(text: str) -> list[str] | None:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return None
    return re.findall(r"^\s+status:\s*(\w+)", m.group(1), re.M)


def yaml_bucket(statuses: list[str] | None) -> str:
    if statuses is None or not statuses:
        return "unknown"
    done = sum(1 for s in statuses if s == "completed")
    if done == len(statuses):
        return "complete"
    if done == 0 and not any(s == "in_progress" for s in statuses):
        return "not_done"
    return "almost_complete"


def creation_time(path: Path) -> float:
    st = path.stat()
    # Windows: st_ctime is creation; elsewhere birthtime if available.
    return getattr(st, "st_birthtime", st.st_ctime)


def classify(rel: str, text: str) -> tuple[str, str]:
    statuses = parse_todos(text)
    bucket = yaml_bucket(statuses)
    src = "yaml"
    if rel in OVERRIDES:
        return OVERRIDES[rel], "readme_override"
    if rel in ROOT_UNKNOWN_OVERRIDES:
        return ROOT_UNKNOWN_OVERRIDES[rel], "unknown->not_done"
    if bucket == "unknown":
        return "not_done", "unknown->not_done"
    return bucket, src


def discover_plans() -> list[Path]:
    plans: list[Path] = []
    for p in PLANS_ROOT.rglob("*.plan.md"):
        # Skip already-reorganized copies if re-run: only consider plans not already
        # under a status dir OR still at epic/root pre-move locations.
        plans.append(p)
    return sorted(plans, key=lambda p: (creation_time(p), p.name.lower()))


def already_in_status(rel: str) -> bool:
    parts = Path(rel).parts
    if len(parts) >= 2 and parts[0] in STATUS_DIRS:
        return True
    if len(parts) >= 3 and parts[0] in EPICS and parts[1] in STATUS_DIRS:
        return True
    return False


def build_mapping() -> list[dict]:
    """Build old→new mapping from current tree (pre-move or idempotent)."""
    entries: list[dict] = []
    root_candidates: list[tuple[float, Path]] = []
    epic_plans: list[Path] = []

    for p in discover_plans():
        rel = rel_posix(p)
        if already_in_status(rel):
            # Already moved — record as identity for link-fix / manifest rebuild.
            parts = Path(rel).parts
            if parts[0] in STATUS_DIRS:
                scope = "ROOT"
                status = parts[0]
            else:
                scope = parts[0]
                status = parts[1]
            entries.append(
                {
                    "old": rel,
                    "new": rel,
                    "scope": scope,
                    "status": status,
                    "source": "already_placed",
                    "ctime": creation_time(p),
                    "ctime_iso": datetime.fromtimestamp(
                        creation_time(p), tz=timezone.utc
                    ).isoformat(),
                }
            )
            continue

        parts = Path(rel).parts
        if len(parts) == 1:
            root_candidates.append((creation_time(p), p))
        elif parts[0] in EPICS and len(parts) == 2:
            epic_plans.append(p)
        else:
            # Nested non-status (e.g. unexpected) — treat as epic if first part matches
            if parts[0] in EPICS:
                epic_plans.append(p)
            else:
                root_candidates.append((creation_time(p), p))

    root_candidates.sort(key=lambda t: (t[0], t[1].name.lower()))
    for i, (ctime, p) in enumerate(root_candidates, 1):
        rel = rel_posix(p)
        text = p.read_text(encoding="utf-8", errors="replace")
        status, src = classify(rel, text)
        new_name = f"{i:03d}_{p.name}"
        new_rel = f"{status}/{new_name}"
        entries.append(
            {
                "old": rel,
                "new": new_rel,
                "scope": "ROOT",
                "status": status,
                "source": src,
                "ctime": ctime,
                "ctime_iso": datetime.fromtimestamp(ctime, tz=timezone.utc).isoformat(),
                "nnn": i,
            }
        )

    for p in sorted(epic_plans, key=lambda x: (creation_time(x), x.name.lower())):
        rel = rel_posix(p)
        text = p.read_text(encoding="utf-8", errors="replace")
        status, src = classify(rel, text)
        epic = Path(rel).parts[0]
        new_rel = f"{epic}/{status}/{p.name}"
        entries.append(
            {
                "old": rel,
                "new": new_rel,
                "scope": epic,
                "status": status,
                "source": src,
                "ctime": creation_time(p),
                "ctime_iso": datetime.fromtimestamp(
                    creation_time(p), tz=timezone.utc
                ).isoformat(),
            }
        )

    return entries


def git_tracked(path: Path) -> bool:
    try:
        r = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(path)],
            cwd=PLANS_ROOT.parent.parent,  # repo root if .cursor/plans
            capture_output=True,
            text=True,
        )
        # PLANS_ROOT is .cursor/plans → parent is .cursor → parent.parent is repo
        return r.returncode == 0
    except OSError:
        return False


def repo_root() -> Path:
    return PLANS_ROOT.parent.parent


def move_one(old: Path, new: Path, dry_run: bool) -> None:
    new.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        print(f"  MOVE {rel_posix(old)} -> {rel_posix(new)}")
        return
    if old.resolve() == new.resolve():
        return
    if new.exists():
        raise FileExistsError(f"target exists: {new}")
    tracked = False
    try:
        r = subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(old.relative_to(repo_root()))],
            cwd=repo_root(),
            capture_output=True,
            text=True,
        )
        tracked = r.returncode == 0
    except OSError:
        tracked = False

    if tracked:
        subprocess.run(
            ["git", "mv", str(old.relative_to(repo_root())), str(new.relative_to(repo_root()))],
            cwd=repo_root(),
            check=True,
        )
    else:
        shutil.move(str(old), str(new))


def apply_moves(entries: list[dict], dry_run: bool) -> None:
    pending = [e for e in entries if e["old"] != e["new"]]
    print(f"{'DRY-RUN' if dry_run else 'APPLY'}: {len(pending)} moves")
    for e in pending:
        old = PLANS_ROOT / e["old"]
        new = PLANS_ROOT / e["new"]
        if not old.exists():
            print(f"  SKIP missing {e['old']}")
            continue
        move_one(old, new, dry_run)


def reconstruct_historical_old(new_rel: str) -> str:
    """Infer pre-move path from a post-move status path."""
    parts = Path(new_rel).parts
    name = parts[-1]
    if len(parts) >= 2 and parts[0] in STATUS_DIRS:
        m = re.match(r"^(\d{3})_(.+)$", name)
        if m:
            return m.group(2)
        return name
    if len(parts) >= 3 and parts[0] in EPICS and parts[1] in STATUS_DIRS:
        return f"{parts[0]}/{name}"
    return new_rel


def normalize_entries(entries: list[dict]) -> list[dict]:
    """Ensure old≠new historical paths are preserved for link rewriting."""
    out = []
    for e in entries:
        e = dict(e)
        if e.get("source") == "already_placed" or e["old"] == e["new"]:
            hist = reconstruct_historical_old(e["new"])
            e["old"] = hist
            e["source"] = e.get("source") or "reconstructed"
            if e["scope"] == "ROOT":
                m = re.match(r"^(\d{3})_", Path(e["new"]).name)
                if m:
                    e["nnn"] = int(m.group(1))
        out.append(e)
    return out


def write_manifest(entries: list[dict]) -> Path:
    path = PLANS_ROOT / "MANIFEST.json"
    entries = normalize_entries(entries)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rules": {
            "root_numbering": "CreationTime ascending NNN_slug",
            "status_folders": list(STATUS_DIRS),
            "classification": "YAML todos + README overrides",
        },
        "counts": {
            "total": len(entries),
            "by_scope_status": {
                f"{a}|{b}": n
                for (a, b), n in Counter((e["scope"], e["status"]) for e in entries).items()
            },
        },
        "entries": entries,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def write_root_readme(entries: list[dict]) -> Path:
    path = PLANS_ROOT / "README.md"
    lines = [
        "# SST-Workbench plans index",
        "",
        "Plans are organized by **status** and (for root plans) **creation order**.",
        "",
        "## Status folders",
        "",
        "- `complete/` — 100% YAML todos completed, or README override DONE",
        "- `almost_complete/` — partial progress / in_progress, or epic still active",
        "- `not_done/` — all pending, or not started",
        "",
        "Epic folders (`paper_upgrade/`, `restructure/`, `vortexlab_v7x/`) keep their",
        "IDs (`PU*`, `PC*`, `SP*`, `VL*`) and place plans under the same status names.",
        "",
        "Classification: YAML frontmatter todos, with overrides from epic READMEs",
        "(see `MANIFEST.json`).",
        "",
        "## Counts",
        "",
        "| Scope | complete | almost_complete | not_done |",
        "|-------|----------|-----------------|----------|",
    ]
    scopes = sorted({e["scope"] for e in entries})
    for scope in scopes:
        c = Counter(e["status"] for e in entries if e["scope"] == scope)
        lines.append(
            f"| {scope} | {c.get('complete', 0)} | {c.get('almost_complete', 0)} | {c.get('not_done', 0)} |"
        )
    lines += ["", f"Total plans: **{len(entries)}**.", "", "## Root plans (chronological)", ""]

    root = [e for e in entries if e["scope"] == "ROOT"]
    root.sort(key=lambda e: e.get("nnn") or 0 or Path(e["new"]).name)
    # Sort by NNN in filename if present
    def root_key(e: dict) -> tuple:
        name = Path(e["new"]).name
        m = re.match(r"^(\d{3})_", name)
        return (int(m.group(1)) if m else 999, name)

    root.sort(key=root_key)
    lines += [
        "| NNN | Status | File |",
        "|-----|--------|------|",
    ]
    for e in root:
        name = Path(e["new"]).name
        m = re.match(r"^(\d{3})_", name)
        nnn = m.group(1) if m else "—"
        lines.append(f"| {nnn} | {e['status']} | [{name}]({e['new']}) |")

    lines += ["", "## Epics", ""]
    for epic in EPICS:
        epic_entries = [e for e in entries if e["scope"] == epic]
        if not epic_entries:
            continue
        lines.append(f"### [{epic}]({epic}/README.md)")
        lines.append("")
        lines.append("| Status | File |")
        lines.append("|--------|------|")
        for e in sorted(epic_entries, key=lambda x: Path(x["new"]).name.lower()):
            name = Path(e["new"]).name
            lines.append(f"| {e['status']} | [{name}]({e['new']}) |")
        lines.append("")

    lines += [
        "## Manifest",
        "",
        "Machine-readable mapping: [`MANIFEST.json`](MANIFEST.json).",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def load_manifest() -> list[dict]:
    path = PLANS_ROOT / "MANIFEST.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["entries"]


def basename_targets(entries: list[dict]) -> dict[str, str]:
    """Map any historical basename (old or new leaf) → new relative path from PLANS_ROOT."""
    out: dict[str, str] = {}
    for e in normalize_entries(entries):
        new = e["new"]
        new_name = Path(new).name
        old_name = Path(e["old"]).name
        out[new_name] = new
        out[old_name] = new
        # Strip NNN_ for lookups of pre-rename root links
        m = re.match(r"^(\d{3})_(.+)$", new_name)
        if m:
            out[m.group(2)] = new
        # Epic-relative old path key
        if "/" in e["old"]:
            out[Path(e["old"]).name] = new
    return out


def relative_link(from_file: Path, to_rel_from_plans: str) -> str:
    target = PLANS_ROOT / to_rel_from_plans
    return Path(os.path.relpath(target, start=from_file.parent)).as_posix()


def fix_links_in_text(text: str, from_file: Path, basename_map: dict[str, str]) -> str:
    """Rewrite markdown links and bare .plan.md references that point at known plan basenames."""

    def resolve_dest(path_only: str) -> str | None:
        # Normalize repo-style .cursor/plans/... links
        norm = path_only.replace("\\", "/")
        if ".cursor/plans/" in norm:
            norm = norm.split(".cursor/plans/", 1)[1]
        base = Path(norm).name
        if base in basename_map:
            return basename_map[base]
        # Try without NNN if present in link already broken
        m = re.match(r"^\d{3}_(.+)$", base)
        if m and m.group(1) in basename_map:
            return basename_map[m.group(1)]
        return None

    def repl_md(m: re.Match) -> str:
        label, dest = m.group(1), m.group(2)
        path_part = dest.strip()
        if path_part.startswith(("http://", "https://", "mailto:", "c:/", "C:/", "file:")):
            return m.group(0)
        path_only, anchor = path_part, ""
        if "#" in path_part:
            path_only, anchor = path_part.split("#", 1)
            anchor = "#" + anchor
        mapped = resolve_dest(path_only)
        if not mapped:
            return m.group(0)
        new_rel = relative_link(from_file, mapped)
        return f"[{label}]({new_rel}{anchor})"

    text = re.sub(r"\[([^\]]*)\]\(([^)]+)\)", repl_md, text)

    # dependsOn: old_basename without extension sometimes
    def repl_depends(m: re.Match) -> str:
        key = m.group(1)
        # try with .plan.md
        for cand in (key, key + ".plan.md", Path(key).name):
            base = Path(cand).name
            if not base.endswith(".plan.md"):
                base = base + ".plan.md" if not base.endswith(".md") else base
            # fuzzy: find key in basename_map
            if base in basename_map:
                new_base = Path(basename_map[base]).name
                # strip .plan.md for dependsOn style if original had no extension
                if not key.endswith(".plan.md") and not key.endswith(".md"):
                    stem = new_base.replace(".plan.md", "")
                    return f"dependsOn: {stem}"
                return f"dependsOn: {new_base}"
            # match by suffix after NNN_
            for b, dest in basename_map.items():
                if b.endswith(key + ".plan.md") or b == key or Path(b).stem.endswith(key):
                    new_base = Path(dest).name
                    if not key.endswith(".plan.md"):
                        return f"dependsOn: {new_base.replace('.plan.md', '')}"
                    return f"dependsOn: {new_base}"
        return m.group(0)

    text = re.sub(r"(?m)^dependsOn:\s*(\S+)\s*$", repl_depends, text)
    return text


def fix_all_links(entries: list[dict], dry_run: bool) -> int:
    basename_map = basename_targets(entries)
    changed = 0
    # All markdown under plans
    for md in PLANS_ROOT.rglob("*.md"):
        if md.name == "MANIFEST.json":
            continue
        text = md.read_text(encoding="utf-8", errors="replace")
        new_text = fix_links_in_text(text, md, basename_map)
        if new_text != text:
            changed += 1
            rel = rel_posix(md)
            if dry_run:
                print(f"  LINK-FIX {rel}")
            else:
                md.write_text(new_text, encoding="utf-8")
                print(f"  LINK-FIX wrote {rel}")
    return changed


def print_summary(entries: list[dict]) -> None:
    print("\nSummary by scope|status:")
    c = Counter((e["scope"], e["status"]) for e in entries)
    for k in sorted(c):
        print(f"  {k[0]:15} {k[1]:18} {c[k]}")
    print(f"Total: {len(entries)}")


def validate(entries: list[dict]) -> int:
    errors = 0
    on_disk = list(PLANS_ROOT.rglob("*.plan.md"))
    print(f"On-disk .plan.md count: {len(on_disk)} (manifest {len(entries)})")
    if len(on_disk) != len(entries):
        print("ERROR: count mismatch")
        errors += 1

    expected_new = {e["new"] for e in entries}
    for p in on_disk:
        rel = rel_posix(p)
        if rel not in expected_new and not already_in_status(rel):
            # allow if matches new path
            print(f"WARN orphan or unexpected: {rel}")
        if not already_in_status(rel):
            print(f"ERROR not under status folder: {rel}")
            errors += 1

    # Broken relative links to .plan.md
    link_re = re.compile(r"\[([^\]]*)\]\(([^)]+\.plan\.md)(?:#[^)]*)?\)")
    for md in PLANS_ROOT.rglob("*.md"):
        text = md.read_text(encoding="utf-8", errors="replace")
        for m in link_re.finditer(text):
            dest = m.group(2).split("#")[0]
            if dest.startswith(("http://", "https://")):
                continue
            target = (md.parent / dest).resolve()
            try:
                target.relative_to(PLANS_ROOT.resolve())
            except ValueError:
                continue
            if not target.exists():
                print(f"BROKEN LINK in {rel_posix(md)}: {dest}")
                errors += 1
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--fix-links", action="store_true")
    ap.add_argument("--write-index", action="store_true", help="Write MANIFEST+README from current mapping")
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()

    if not any([args.dry_run, args.apply, args.fix_links, args.write_index, args.validate]):
        args.dry_run = True

    if args.fix_links:
        if not (PLANS_ROOT / "MANIFEST.json").exists():
            print("MANIFEST.json missing; run --apply first", file=sys.stderr)
            return 1
        entries = normalize_entries(load_manifest())
        write_manifest(entries)  # persist reconstructed old paths
        n = fix_all_links(entries, dry_run=False)
        print(f"Link-fix files touched: {n}")
        err = validate(entries)
        return 1 if err else 0

    entries = build_mapping()
    print_summary(entries)

    if args.dry_run and not args.apply:
        apply_moves(entries, dry_run=True)
        return 0

    if args.apply:
        pre_move = [dict(e) for e in entries]
        apply_moves(entries, dry_run=False)
        # Keep historical old paths from pre-move mapping
        write_manifest(pre_move)
        write_root_readme(pre_move)
        print("Wrote MANIFEST.json and README.md")
        n = fix_all_links(pre_move, dry_run=False)
        print(f"Link-fix files touched: {n}")
        err = validate(pre_move)
        return 1 if err else 0

    if args.write_index:
        if (PLANS_ROOT / "MANIFEST.json").exists():
            entries = normalize_entries(load_manifest())
        write_manifest(entries)
        write_root_readme(entries)
        print("Wrote MANIFEST.json and README.md")

    if args.validate:
        if (PLANS_ROOT / "MANIFEST.json").exists():
            entries = normalize_entries(load_manifest())
        return 1 if validate(entries) else 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
