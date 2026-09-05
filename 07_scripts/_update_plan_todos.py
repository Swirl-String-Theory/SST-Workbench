"""Sync plan-file todo state with what has actually been executed.

Each plan carries three parallel trackers that drifted apart during execution: YAML
frontmatter `todos`, a `## Todos` checkbox list, and a `Status:` line. SP01-SP07 ran to
completion while all three still said PLANNED/pending.

Run with --apply to write; default is a dry run.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

PLANS = Path(__file__).resolve().parents[1] / ".cursor" / "plans" / "restructure"

#: file stem -> (status, next-line text)
DONE = {
    "SP00_freeze_and_provenance": "Freeze closed; provenance artifacts under 10_docs/migration/.",
    "SP01_path_resolver": "Resolver shipped: sst_workbench_paths + paths.cmd + resolve_family.",
    "SP02_compat_junction_layer": "58 junctions live and verified; bootstrap reproduces them.",
    "SP03_catalog_skeleton_and_hygiene": "Skeleton seeded; placeholders are _NAMESPACE.md; longpaths global.",
    "SP04_low_risk_moves": "24 rows verified, 17 junctions. scripts/ is now 07_scripts/.",
    "SP05_clean_family_moves": "43 rows verified, variants and reveal keys in _variants/.",
    "SP06_container_splits": "191 rows verified; 7 collapsed containers re-split into 16 families.",
    "SP07_knotplot_refactor": "21 rows verified; 12.4 GB split into tool, geometry, campaigns, results.",
}

#: still to run - refresh the Next line so it names the real blocker, not a stale one
PENDING_NEXT = {
    "SP08_catalog_metadata_and_registry":
        "Ready. First fix 3 duplicate catalog ids on disk (B003, B004, C006) and "
        "3 catalog rows with no directory (B002, D001 research, E007).",
    "SP09_version_rename_stage2": "Blocked on SP08 (needs project.json legacy_dir).",
    "SP10_reproducibility_gate": "Blocked on SP09.",
    "SP11_decommission": "Blocked on SP10. 4 path_map rows pending.",
}


def set_frontmatter_status(text: str, status: str) -> str:
    """Rewrite every `status:` inside the frontmatter todo block."""
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    head, rest = text[:end], text[end:]
    head = re.sub(r"^(\s+)status: \w+$", rf"\1status: {status}", head, flags=re.M)
    return head + rest


def set_checkboxes(text: str, checked: bool) -> str:
    src, dst = ("- [ ]", "- [x]") if checked else ("- [x]", "- [ ]")
    return text.replace(src, dst)


def set_status_line(text: str, status: str) -> str:
    return re.sub(r"^(Status: )`\w[\w ]*`", rf"\1`{status}`", text, count=1, flags=re.M)


def set_next_line(text: str, note: str) -> str:
    if re.search(r"^\*\*Next:\*\*", text, flags=re.M):
        return re.sub(r"^\*\*Next:\*\* .*$", f"**Next:** {note}", text, count=1, flags=re.M)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    changed = 0
    for stem, note in DONE.items():
        path = PLANS / f"{stem}.plan.md"
        if not path.is_file():
            print(f"  !! missing {path.name}")
            continue
        text = original = path.read_text(encoding="utf-8")
        text = set_frontmatter_status(text, "completed")
        text = set_checkboxes(text, checked=True)
        text = set_status_line(text, "DONE")
        text = set_next_line(text, note)
        if text != original:
            changed += 1
            print(f"  DONE     {path.name}")
            if args.apply:
                path.write_text(text, encoding="utf-8")

    for stem, note in PENDING_NEXT.items():
        path = PLANS / f"{stem}.plan.md"
        if not path.is_file():
            print(f"  !! missing {path.name}")
            continue
        text = original = path.read_text(encoding="utf-8")
        text = set_next_line(text, note)
        if text != original:
            changed += 1
            print(f"  PENDING  {path.name}")
            if args.apply:
                path.write_text(text, encoding="utf-8")

    print(f"\nfiles changed: {changed}")
    if not args.apply:
        print("(dry run)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
