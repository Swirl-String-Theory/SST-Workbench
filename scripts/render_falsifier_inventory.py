"""Render INVENTORY_FALSIFIERS.md from falsifier_registry.yaml."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from falsifier_registry import (
    DEFAULT_REGISTRY,
    FAMILIES,
    WB,
    RegistryEntry,
    discover_unregistered,
    load_entries,
    load_registry,
    reset_pack_index,
    validate_registry,
)

OUT = WB / "INVENTORY_FALSIFIERS.md"

FAMILY_TITLES = {
    "I": "Dynamic particle stability",
    "II": "Local mode / field structure",
    "III": "Gravity / pressure / emergent fields",
    "IV": "Energy / thermodynamics / Maxwell–Kelvin",
    "V": "Anti-self-deception / metrology",
}


def _esc_cell(text: str) -> str:
    return (text or "—").replace("|", "\\|").replace("\n", " ")


def _blind_cell(blind: bool) -> str:
    return "yes" if blind else "no"


def _status_badge(physics: str, numerics: str) -> str:
    return f"P:{physics} / N:{numerics}"


def render_legend() -> str:
    return "\n".join(
        [
            "## Status legend",
            "",
            "| Symbol | Meaning |",
            "|---|---|",
            "| 🔴 | Physics FAIL or strong falsification signal |",
            "| 🟢 | Physics PASS (blind gate cleared) |",
            "| 🟠 | Physics INDETERMINATE — numerics may pass |",
            "| 🟡 | Physics weak / partial signal |",
            "| ⚪ | Physics UNTESTED |",
            "| 🔧 | REFERENCE_ONLY — metrology / QA, not a physics claim |",
            "",
            "**Physics vs numerics:** `physics_status` (PASS | FAIL | INDETERMINATE | UNTESTED | REFERENCE_ONLY) "
            "is independent of `numerics_status` (PASS | FAIL | NOT_RUN | N/A). "
            "A green pytest run never implies a physics PASS.",
            "",
        ]
    )


def render_hypothesis_table(entries: list[RegistryEntry]) -> str:
    rows = [e for e in entries if e.hypothesis_table is not None]
    rows.sort(key=lambda e: e.hypothesis_table or 0)
    extra = [e for e in entries if e.hypothesis_table is None and e.question]

    lines = [
        "## Hypothesis roadmap",
        "",
        f"Core hypothesis rows ({len(rows)}) plus {len(extra)} registry-only hypotheses.",
        "",
        "| # | ID | Status | ★ | Central question | Pack (latest) | Physics | Numerics |",
        "|---:|---|:---:|:---:|---|---|:---:|:---:|",
    ]
    for e in rows:
        ver = e.resolved.version_str if e.resolved else "?"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(e.hypothesis_table),
                    e.id,
                    e.physics_emoji or "⚪",
                    e.stars or "—",
                    _esc_cell(e.question or e.hypothesis),
                    _esc_cell(f"{e.name} ({ver})"),
                    e.physics_status,
                    e.numerics_status,
                ]
            )
            + " |"
        )

    if extra:
        lines.extend(
            [
                "",
                "### Additional hypotheses (not in original 28-row table)",
                "",
                "| ID | Family | Status | Central question | Physics | Numerics |",
                "|---|:---:|:---:|:---|:---:|:---:|",
            ]
        )
        for e in sorted(extra, key=lambda x: (x.family, x.id)):
            lines.append(
                "| "
                + " | ".join(
                    [
                        e.id,
                        e.family,
                        e.physics_emoji or "⚪",
                        _esc_cell(e.question or e.hypothesis),
                        e.physics_status,
                        e.numerics_status,
                    ]
                )
                + " |"
            )
    lines.append("")
    return "\n".join(lines)


def render_master_registry(entries: list[RegistryEntry]) -> str:
    lines = [
        "## Master registry",
        "",
        f"**{len(entries)}** entries — single source of truth in [`falsifier_registry.yaml`](falsifier_registry.yaml).",
        "",
        "| ID | Name | Version | Family | Blind | Physics | Numerics | Next test |",
        "|---|---|:---:|:---:|:---:|:---:|:---:|---|",
    ]
    for e in sorted(entries, key=lambda x: x.id):
        ver = e.resolved.version_str if e.resolved else "?"
        lines.append(
            "| "
            + " | ".join(
                [
                    e.id,
                    _esc_cell(e.name),
                    ver,
                    e.family,
                    _blind_cell(e.blind),
                    e.physics_status,
                    e.numerics_status,
                    _esc_cell(e.next_test),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def render_family_sections(entries: list[RegistryEntry]) -> str:
    lines = ["## Per-family overview", ""]
    for fam in sorted(FAMILIES, key=lambda f: ["I", "II", "III", "IV", "V"].index(f)):
        fam_entries = [e for e in entries if e.family == fam]
        lines.extend(
            [
                f"### Family {fam} — {FAMILY_TITLES[fam]}",
                "",
                f"{len(fam_entries)} entries.",
                "",
                "| ID | Version | Blind | Physics | Numerics |",
                "|---|:---:|:---:|:---:|:---:|",
            ]
        )
        for e in sorted(fam_entries, key=lambda x: x.id):
            ver = e.resolved.version_str if e.resolved else "?"
            lines.append(
                "| "
                + " | ".join(
                    [
                        e.id,
                        ver,
                        _blind_cell(e.blind),
                        e.physics_status,
                        e.numerics_status,
                    ]
                )
                + " |"
            )
        lines.append("")
    return "\n".join(lines)


def render_paths_appendix(entries: list[RegistryEntry]) -> str:
    lines = [
        "## Latest pack paths",
        "",
        "<details>",
        "<summary>Resolved working trees and archive zips</summary>",
        "",
        "| ID | Working tree | Archive zip |",
        "|---|---|---|",
    ]
    for e in sorted(entries, key=lambda x: x.id):
        if e.resolved:
            lines.append(
                "| "
                + " | ".join(
                    [
                        e.id,
                        _esc_cell(e.resolved.rel_working()),
                        _esc_cell(e.resolved.rel_archive()),
                    ]
                )
                + " |"
            )
        else:
            lines.append(f"| {e.id} | — | — |")
    lines.extend(["", "</details>", ""])
    return "\n".join(lines)


def render_document(entries: list[RegistryEntry], *, unregistered: list[str]) -> str:
    data = load_registry()
    version = data.get("registry_version", 1)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = "\n".join(
        [
            "# Falsifier inventory",
            "",
            f"Generated from `falsifier_registry.yaml` (schema v{version}) on {now}.",
            "Regenerate: `python scripts/render_falsifier_inventory.py --write`.",
            "",
        ]
    )
    footer = ""
    if unregistered:
        footer = "\n".join(
            [
                "## Unregistered packs (CI warning)",
                "",
                f"{len(unregistered)} working-tree pack(s) match falsifier heuristics but no registry glob:",
                "",
            ]
            + [f"- `{p}`" for p in unregistered]
            + [""]
        )
    return "\n".join(
        [
            header,
            render_legend(),
            render_hypothesis_table(entries),
            render_master_registry(entries),
            render_family_sections(entries),
            render_paths_appendix(entries),
            footer,
        ]
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help="Path to falsifier_registry.yaml",
    )
    ap.add_argument(
        "--write",
        action="store_true",
        help=f"Write {OUT.name}",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=OUT,
        help="Output markdown path",
    )
    args = ap.parse_args(argv)

    reset_pack_index()
    errs = validate_registry(path=args.registry)
    if errs:
        for e in errs:
            print(e, file=sys.stderr)
        return 1

    entries = load_entries(args.registry)
    unregistered = discover_unregistered(entries)
    doc = render_document(entries, unregistered=unregistered)

    if args.write:
        args.output.write_text(doc, encoding="utf-8")
        print(f"Wrote {args.output} ({len(entries)} entries, {len(unregistered)} unregistered)")
    else:
        print(doc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
