"""Seed 10_docs/migration/path_map.csv from RESTRUCTURE_PLAN_v0.1.plan.md.

Parses the six mapping-table layouts and expands path abbreviations and
brace sets (e.g. R/A/{A011,A012}) using CATALOG_v0.1.md family slugs.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Any

WB = Path(__file__).resolve().parents[1]
DEFAULT_PLAN = (
    WB / ".cursor" / "plans" / "restructure" / "RESTRUCTURE_PLAN_v0.1.plan.md"
)
DEFAULT_CATALOG = WB / ".cursor" / "plans" / "restructure" / "CATALOG_v0.1.md"
DEFAULT_OUT = WB / "10_docs" / "migration" / "path_map.csv"

PATH_MAP_FIELDS = [
    "old_path",
    "new_path",
    "domain",
    "letter",
    "catalog_id",
    "kind",
    "phase",
    "junction",
    "status",
    "note",
]

VALID_PHASES = frozenset(
    {f"SP{i:02d}" for i in range(12)} | {"SP04 / SP11", "SP06 / SP11", "-"}
)
VALID_KINDS = frozenset(
    {"code", "data", "output", "tooling", "archive", "vendored", "stub", "app", "campaign", "tool"}
)
VALID_STATUS = frozenset({"pending", "moved", "verified", "reverted", "skipped"})

_ABBREV_ROW = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|"
)
_SECTION = re.compile(r"^##\s+(\d+)\.\s+")
_TABLE_SEP = re.compile(r"^\|[\s\-:|]+\|$")
_BRACE = re.compile(r"^([^{]*)\{([^}]+)\}(.*)$")
_CATALOG_ID = re.compile(r"\b([A-F]\d{3})\b")
_DOMAIN_LETTER = re.compile(
    r"^(0[1-4]_[a-z_]+)/(?:([A-F]_[a-z_]+)/)?(?:([A-F]\d{3})(?:_[a-z0-9_]+)?)?"
)


def strip_ticks(s: str) -> str:
    s = s.strip()
    if s.startswith("`") and s.endswith("`"):
        return s[1:-1]
    return s.strip("`")


def parse_abbreviations(text: str) -> dict[str, str]:
    """Map short codes (R/A, L/C, APP, ...) to full prefix paths ending in /."""
    abbrev: dict[str, str] = {}
    in_abbrev = False
    for line in text.splitlines():
        if line.startswith("## Path abbreviations"):
            in_abbrev = True
            continue
        if in_abbrev and line.startswith("## "):
            break
        if not in_abbrev or not line.startswith("|"):
            continue
        if _TABLE_SEP.match(line) or "Short" in line and "Full" in line:
            continue
        m = _ABBREV_ROW.match(line)
        if not m:
            # Multi-code cell: `L/A` `L/B` `L/C` `L/D` | `02_libraries/{A_...,...}/`
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 2:
                continue
            shorts = re.findall(r"`([^`]+)`", cells[0])
            fulls = re.findall(r"`([^`]+)`", cells[1])
            if not shorts or not fulls:
                continue
            full = fulls[0]
            if "{" in full:
                # Expand 02_libraries/{A_knot_geometry,B_knot_data,...}/
                prefix, body, suffix = _BRACE.match(full).groups()  # type: ignore[union-attr]
                parts = [p.strip() for p in body.split(",")]
                letter_map = {
                    "A": "A_",
                    "B": "B_",
                    "C": "C_",
                    "D": "D_",
                }
                for short in shorts:
                    letter = short.split("/")[-1]  # A from L/A
                    match = next((p for p in parts if p.startswith(letter + "_")), None)
                    if match is None:
                        raise ValueError(f"No brace part for {short} in {full}")
                    abbrev[short] = f"{prefix}{match}{suffix}"
            else:
                for short in shorts:
                    abbrev[short] = full if full.endswith("/") else full + "/"
            continue
        short, full = m.group(1), m.group(2)
        if not full.endswith("/") and "{" not in full:
            full = full + "/"
        abbrev[short] = full
    # APP is listed as APP | 05_apps/
    if "APP" not in abbrev:
        abbrev["APP"] = "05_apps/"
    return abbrev


def parse_catalog(text: str) -> dict[str, dict[str, str]]:
    """Keyed by 'domain/letter/ID' (letter may be empty for flat domains).

    Also exposes bare ID -> entry for the *last* seen ID (legacy); prefer
    ``lookup_catalog`` which is domain-aware.
    """
    catalog: dict[str, dict[str, str]] = {}
    domain = ""
    letter = ""
    domain_re = re.compile(r"^#\s+(0[1-9]_[a-z_]+)\s*$")
    letter_re = re.compile(r"^##\s+([A-F]_[a-z_]+)")
    for line in text.splitlines():
        dm = domain_re.match(line)
        if dm:
            domain = dm.group(1)
            letter = ""
            continue
        lm = letter_re.match(line)
        if lm and domain.startswith(("01_", "02_", "03_", "04_")):
            letter = lm.group(1)
            continue
        if not line.startswith("|"):
            continue
        if _TABLE_SEP.match(line) or line.startswith("| ID ") or line.startswith("|----"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        cid = strip_ticks(cells[0])
        if not re.fullmatch(r"[A-F]\d{3}", cid):
            continue
        family = strip_ticks(cells[1])
        official = strip_ticks(cells[2]) if len(cells) > 2 else family
        entry = {
            "family": family,
            "domain": domain,
            "letter": letter,
            "official_name": official,
            "catalog_id": cid,
        }
        key = f"{domain}/{letter}/{cid}" if letter else f"{domain}/{cid}"
        catalog[key] = entry
        catalog[cid] = entry  # last-wins bare key; prefer scoped lookup
    return catalog


def lookup_catalog(
    catalog: dict[str, dict[str, str]],
    catalog_id: str,
    domain: str = "",
    letter: str = "",
) -> dict[str, str] | None:
    if domain and letter:
        hit = catalog.get(f"{domain}/{letter}/{catalog_id}")
        if hit:
            return hit
    if domain:
        hit = catalog.get(f"{domain}/{catalog_id}")
        if hit:
            return hit
        # scan scoped keys for this domain+id
        prefix = f"{domain}/"
        for k, v in catalog.items():
            if k.startswith(prefix) and v.get("catalog_id") == catalog_id:
                if not letter or v.get("letter") == letter:
                    return v
    return catalog.get(catalog_id)


def expand_destination(
    dest: str,
    abbrev: dict[str, str],
    catalog: dict[str, dict[str, str]],
) -> list[str]:
    """Expand abbreviation prefixes and brace sets into concrete relative paths."""
    dest = dest.strip().rstrip("/")
    # Already a full domain path
    if re.match(r"^0[1-9]_", dest) or dest.startswith("10_docs"):
        return _expand_braces(dest, catalog)

    # APP/A001_dashboard
    if dest.startswith("APP/") or dest == "APP":
        rest = dest[4:] if dest.startswith("APP/") else ""
        base = abbrev.get("APP", "05_apps/").rstrip("/")
        if not rest:
            return [base]
        return _expand_braces(f"{base}/{rest}", catalog)

    # Multi-segment destinations separated by commas OUTSIDE braces:
    # e.g. `R/A/{A017,A028}`, `R/C/C008`
    parts = _split_outside_braces(dest)
    out: list[str] = []
    for part in parts:
        out.extend(_expand_one_abbrev_path(part, abbrev, catalog))
    return out


def _split_outside_braces(text: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    buf: list[str] = []
    for ch in text:
        if ch == "{":
            depth += 1
            buf.append(ch)
        elif ch == "}":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == "," and depth == 0:
            part = "".join(buf).strip()
            if part:
                parts.append(part)
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts or [text.strip()]


def _expand_one_abbrev_path(
    path: str,
    abbrev: dict[str, str],
    catalog: dict[str, dict[str, str]],
) -> list[str]:
    path = path.strip().rstrip("/")
    # Match X/Y/... where X/Y is an abbreviation key
    for short in sorted(abbrev.keys(), key=len, reverse=True):
        if path == short:
            return [abbrev[short].rstrip("/")]
        prefix = short + "/"
        if path.startswith(prefix):
            rest = path[len(prefix) :]
            base = abbrev[short].rstrip("/")
            return _expand_braces(f"{base}/{rest}" if rest else base, catalog)
    # Bare absolute-ish path under domains
    return _expand_braces(path, catalog)


def _expand_braces(path: str, catalog: dict[str, dict[str, str]]) -> list[str]:
    m = _BRACE.match(path)
    if not m:
        return [_resolve_catalog_slug(path, catalog)]
    prefix, body, suffix = m.group(1), m.group(2), m.group(3)
    ids = [x.strip() for x in body.split(",") if x.strip()]
    domain, letter, _ = domain_letter_id(prefix.rstrip("/"))
    results: list[str] = []
    for cid in ids:
        id_only = cid.split("_", 1)[0] if re.match(r"^[A-F]\d{3}_", cid) else cid
        entry = lookup_catalog(catalog, id_only, domain=domain, letter=letter)
        if entry and re.fullmatch(r"[A-F]\d{3}", cid):
            mid = f"{cid}_{entry['family']}"
        elif entry and not cid.startswith(id_only + "_"):
            mid = f"{id_only}_{entry['family']}"
        else:
            mid = cid
        results.append(_resolve_catalog_slug(f"{prefix}{mid}{suffix}".rstrip("/"), catalog))
    return results


def _resolve_catalog_slug(path: str, catalog: dict[str, dict[str, str]]) -> str:
    """If path ends with bare A039, append _family from catalog (domain-aware)."""
    path = path.replace("\\", "/").rstrip("/")
    m = re.search(r"/([A-F]\d{3})$", path)
    if m:
        cid = m.group(1)
        domain, letter, _ = domain_letter_id(path)
        entry = lookup_catalog(catalog, cid, domain=domain, letter=letter)
        if entry:
            return f"{path}_{entry['family']}"
    return path


def split_table_row(line: str) -> list[str]:
    if not line.startswith("|"):
        raise ValueError(f"Not a table row: {line!r}")
    return [c.strip() for c in line.strip().strip("|").split("|")]


def iter_section_tables(text: str) -> list[tuple[int, list[list[str]]]]:
    """Return [(section_number, [header_cells, row_cells, ...]), ...]."""
    sections: list[tuple[int, list[list[str]]]] = []
    current_sec: int | None = None
    current_rows: list[list[str]] = []
    in_table = False

    def flush() -> None:
        nonlocal current_rows, in_table
        if current_sec is not None and current_rows:
            sections.append((current_sec, current_rows))
        current_rows = []
        in_table = False

    for line in text.splitlines():
        sm = _SECTION.match(line)
        if sm:
            flush()
            current_sec = int(sm.group(1))
            continue
        if line.startswith("## ") and not sm:
            # Non-numbered section (e.g. Non-root, Summary)
            if line.startswith("## Non-root") or line.startswith("## Summary"):
                flush()
                current_sec = 0 if line.startswith("## Non-root") else -1
            continue
        if current_sec is None or current_sec < 0:
            continue
        if line.startswith("|") and not _TABLE_SEP.match(line):
            cells = split_table_row(line)
            if not in_table:
                in_table = True
                current_rows = [cells]
            else:
                current_rows.append(cells)
        elif in_table and not line.startswith("|"):
            flush()
            # keep current_sec for a possible second table in same section
            current_sec = current_sec
    flush()
    return sections


def kind_from_label(label: str) -> str:
    label = label.strip().lower()
    mapping = {
        "data": "data",
        "output": "output",
        "code": "code",
        "tooling": "tooling",
        "tool": "tool",
        "archive": "archive",
        "vendored": "vendored",
        "stub": "stub",
        "app": "app",
        "campaign": "campaign",
    }
    if label in mapping:
        return mapping[label]
    if "delete" in label:
        return "stub"
    if "output" in label:
        return "output"
    return "code"


def domain_letter_id(new_path: str) -> tuple[str, str, str]:
    """Extract domain, letter, catalog_id from a concrete new_path."""
    new_path = new_path.replace("\\", "/").strip("/")
    parts = new_path.split("/")
    domain = parts[0] if parts else ""
    letter = ""
    catalog_id = ""
    if len(parts) >= 2 and re.match(r"^[A-F]_", parts[1]):
        letter = parts[1]
    for p in parts:
        m = re.match(r"^([A-F]\d{3})(?:_|$)", p)
        if m:
            catalog_id = m.group(1)
            break
    return domain, letter, catalog_id


def first_tick_path(cell: str) -> str:
    ticks = re.findall(r"`([^`]+)`", cell)
    if ticks:
        return ticks[0].rstrip("/")
    return strip_ticks(cell).split()[0].rstrip("/") if strip_ticks(cell) else ""


def resolve_ellipsis_old_path(raw: str, workbench: Path) -> str:
    """Expand plan ellipsis shorthands to a real path when possible."""
    raw = strip_ticks(raw).replace("\\", "/").rstrip("/")
    if "..." not in raw:
        return raw
    # Known shorthand expansions from RESTRUCTURE_PLAN §5
    known = {
        "SST_Quantum_Galileo_..._v0.1.1_BLIND_SOURCE": (
            "SST_Quantum_Galileo_Action_Gauge_Closure/"
            "SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.1_BLIND_SOURCE"
        ),
        "SST_Quantum_Galileo_..._v0.1.1_REVEAL_KEY": (
            "SST_Quantum_Galileo_Action_Gauge_Closure/"
            "SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.1_REVEAL_KEY"
        ),
        "SST_Trefoil_..._Mega_Falsifier/SST_Trefoil_v0.3.0_with_Knot_Library_v0.2.5": (
            "SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier/"
            "SST_Trefoil_v0.3.0_with_Knot_Library_v0.2.5"
        ),
    }
    if raw in known:
        return known[raw]
    # Generic: replace ... with * and glob
    pattern = raw.replace("...", "*")
    hits = list(workbench.glob(pattern))
    if len(hits) == 1:
        return hits[0].relative_to(workbench).as_posix()
    return raw


def normalize_old_path(raw: str, workbench: Path) -> str:
    """Strip ticks/trailing slash; prefer on-disk casing for gui; expand ellipsis."""
    raw = resolve_ellipsis_old_path(raw, workbench)
    raw = raw.replace("\\", "/").rstrip("/")
    # Drop trailing parenthetical notes that leaked into the path
    raw = re.sub(r"/\s*\(.*$", "", raw)
    raw = re.sub(r"\s*\(.*$", "", raw)
    if not raw:
        return raw
    # Plan says GUI/; filesystem is gui/
    if raw == "GUI" or raw.startswith("GUI/"):
        alt = "gui" + raw[3:]
        if (workbench / alt.split("/")[0]).exists():
            return alt
    return raw


def rows_from_plan(
    plan_text: str,
    catalog_text: str,
    workbench: Path | None = None,
) -> list[dict[str, str]]:
    workbench = workbench or WB
    abbrev = parse_abbreviations(plan_text)
    catalog = parse_catalog(catalog_text)
    rows: list[dict[str, str]] = []
    by_new: dict[str, dict[str, str]] = {}

    def add_row(
        old_path: str,
        new_path: str,
        kind: str,
        phase: str,
        junction: str,
        note: str = "",
    ) -> None:
        old_path = normalize_old_path(old_path, workbench)
        new_path = new_path.replace("\\", "/").strip("/")
        domain, letter, catalog_id = domain_letter_id(new_path)
        phase = phase.strip()
        if phase == "—":
            phase = "-"
        if new_path in by_new:
            # Intentional merges (two roots -> one catalog id): keep one row, record extras
            existing = by_new[new_path]
            extra = f"also_from={old_path}"
            existing["note"] = (
                f"{existing['note']}; {extra}" if existing["note"] else extra
            )
            return
        row = {
            "old_path": old_path,
            "new_path": new_path,
            "domain": domain,
            "letter": letter,
            "catalog_id": catalog_id,
            "kind": kind_from_label(kind) if kind else "code",
            "phase": phase,
            "junction": junction,
            "status": "pending",
            "note": note,
        }
        by_new[new_path] = row
        rows.append(row)

    tables = iter_section_tables(plan_text)
    for sec, table in tables:
        if not table or len(table) < 2:
            continue
        header = [h.lower() for h in table[0]]
        for cells in table[1:]:
            if len(cells) < 2:
                continue
            # Skip summary category tables
            if sec == -1:
                continue

            if sec == 1:
                # # | Current root | Destination | Kind | Phase
                old, dest, kind, phase = cells[1], cells[2], cells[3], cells[4]
                for new in expand_destination(strip_ticks(dest), abbrev, catalog):
                    add_row(old, new, kind, phase, "yes")

            elif sec == 2:
                # # | Current root | Destination | Versions | Phase
                old, dest, versions, phase = cells[1], cells[2], cells[3], cells[4]
                for new in expand_destination(strip_ticks(dest), abbrev, catalog):
                    add_row(old, new, "code", phase, "yes", note=f"versions={strip_ticks(versions)}")

            elif sec == 3:
                # # | Current root | Splits into | Count | Phase
                old, splits, count, phase = cells[1], cells[2], cells[3], cells[4]
                # Cell may list several tick-wrapped destinations with notes:
                # `R/A/{A011,...}` or `T/C/C001` (source), `D/D/D001` (STL)
                tick_dests = re.findall(r"`([^`]+)`", splits)
                if not tick_dests:
                    tick_dests = [strip_ticks(splits)]
                dests: list[str] = []
                for td in tick_dests:
                    dests.extend(expand_destination(td, abbrev, catalog))
                for new in dests:
                    add_row(
                        old,
                        new,
                        "code",
                        phase,
                        "yes",
                        note=f"container_split count={strip_ticks(count)}",
                    )

            elif sec == 4:
                # # | Current sub-path | Destination | Kind | Approx. size
                old_cell, dest, kind, size = cells[1], cells[2], cells[3], cells[4]
                old = first_tick_path(old_cell)
                phase = "SP07"
                for new in expand_destination(strip_ticks(dest), abbrev, catalog):
                    add_row(
                        old,
                        new,
                        kind,
                        phase,
                        "yes",
                        note=f"size={strip_ticks(size)}",
                    )

            elif sec == 5:
                # Current | Belongs to | Placement
                old, belongs, placement = cells[0], cells[1], cells[2]
                old_n = normalize_old_path(old, workbench)
                belongs_s = strip_ticks(belongs)
                cid_m = re.search(r"\b([A-F]\d{3})\b", belongs_s)
                cid = cid_m.group(1) if cid_m else ""
                leaf = old_n.replace("\\", "/").rstrip("/").split("/")[-1]
                entry = lookup_catalog(catalog, cid, domain="01_research", letter="A_falsifiers") if cid else None
                fam = entry["family"] if entry else "variant"
                synth = (
                    f"01_research/A_falsifiers/{cid}_{fam}/_variants/{leaf}"
                    if cid
                    else f"10_docs/migration/variants/{leaf}"
                )
                add_row(
                    old,
                    synth,
                    "code",
                    "SP05",
                    "no",
                    note=f"belongs_to={belongs_s}; placement={strip_ticks(placement)}",
                )

            elif sec == 6:
                # # | Current root | Disposition | Phase
                old, disposition, phase = cells[1], cells[2], cells[3]
                disp = strip_ticks(disposition)
                kind = "stub" if "delete" in disp.lower() else "code"
                # Synthesize a new_path placeholder for deletions / dispositions
                slug = normalize_old_path(old, workbench).replace("/", "_")
                if "to `R/F/F010" in disp or "F010" in disp:
                    news = expand_destination("R/F/F010_sycl_probes", abbrev, catalog)
                    for new in news:
                        add_row(old, new, kind, phase, "yes", note=disp)
                elif "D/D/D003" in disp:
                    news = expand_destination("D/D/D003_timefield_spectral", abbrev, catalog)
                    for new in news:
                        add_row(old, new, "output", phase, "yes", note=disp)
                elif "10_docs/registry" in disp:
                    add_row(old, "10_docs/registry/falsifier_registry_readme", "stub", phase, "no", note=disp)
                else:
                    add_row(
                        old,
                        f"09_archive/pending_delete/{slug}",
                        kind,
                        phase,
                        "no",
                        note=disp,
                    )

            elif sec == 0:
                # Non-root: Item | Disposition | Phase
                item, disposition, phase = cells[0], cells[1], cells[2]
                disp = strip_ticks(disposition)
                if "stay at repo root" in disp.lower():
                    continue
                ticks = re.findall(r"`([^`]+)`", item)
                # Prefer concrete file/dir ticks over the prose label
                items = [t for t in ticks if not t.startswith("*.") and t not in {"zip"}]
                if not items:
                    items = [first_tick_path(item) or strip_ticks(item)]
                # Clean .tmp.driveupload cell
                items = [
                    re.sub(r"^(\.tmp\.driveupload).*", r"\1", i).rstrip("/")
                    for i in items
                ]
                for item_s in items:
                    if item_s.startswith(".tmp"):
                        add_row(
                            ".tmp.driveupload",
                            "09_archive/drive_upload_staging",
                            "archive",
                            phase,
                            "no",
                            note=disp,
                        )
                        continue
                    if "09_archive/restore" in disp:
                        add_row(item_s, "09_archive/restore/root_zips", "archive", phase, "no", note=disp)
                    elif "10_docs/inventory" in disp:
                        add_row(item_s, "10_docs/inventory/root_docs", "tooling", phase, "no", note=disp)
                    elif "07_scripts" in disp:
                        leaf = Path(item_s).name
                        add_row(item_s, f"07_scripts/{leaf}", "tooling", phase, "no", note=disp)
                    elif "A004_ideal_gilbert" in disp or "D/A/A004" in disp:
                        news = expand_destination("D/A/A004_ideal_gilbert", abbrev, catalog)
                        leaf = Path(item_s).name
                        for new in news:
                            add_row(item_s, f"{new}/{leaf}", "data", phase, "no", note=disp)
                    else:
                        add_row(
                            item_s,
                            f"10_docs/migration/non_root/{re.sub(r'[^A-Za-z0-9]+', '_', item_s)[:60]}",
                            "tooling",
                            phase,
                            "no",
                            note=disp,
                        )

    # Mark rows whose old_path is absent as skipped (still listed for planning).
    # Glob patterns (contain *) stay pending — resolved at move time.
    for row in rows:
        op = row["old_path"]
        if not op or "*" in op:
            continue
        target = workbench / op
        if not target.exists():
            row["status"] = "skipped"
            extra = "old_path_missing_on_disk"
            row["note"] = f"{row['note']}; {extra}" if row["note"] else extra

    return rows


def write_path_map(rows: list[dict[str, str]], out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PATH_MAP_FIELDS)
        w.writeheader()
        for row in rows:
            w.writerow(row)
    return out


def load_path_map(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Seed path_map.csv from RESTRUCTURE_PLAN.")
    p.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    p.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--root", type=Path, default=WB)
    args = p.parse_args(argv)
    rows = rows_from_plan(
        args.plan.read_text(encoding="utf-8"),
        args.catalog.read_text(encoding="utf-8"),
        workbench=args.root,
    )
    written = write_path_map(rows, args.out)
    print(f"Wrote {written} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
