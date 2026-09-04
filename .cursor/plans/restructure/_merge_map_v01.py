"""
Merge RESTRUCTURE_PLAN + CATALOG + path_map.csv into a unified
SST_WORKBENCH_RESTRUCTURE_MAP_v0.1.json aligned with the planning set.

Legacy map version targets are remapped by source path / slug when possible.
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLAN_DIR = Path(__file__).resolve().parent
CATALOG_MD = PLAN_DIR / "CATALOG_v0.1.md"
PLAN_MD = PLAN_DIR / "RESTRUCTURE_PLAN_v0.1.plan.md"
LEGACY_JSON = PLAN_DIR / "SST_WORKBENCH_RESTRUCTURE_MAP_v0.1.json"
PATH_MAP = ROOT / "10_docs" / "migration" / "path_map.csv"
OUT_JSON = PLAN_DIR / "SST_WORKBENCH_RESTRUCTURE_MAP_v0.1.json"
BACKUP_JSON = PLAN_DIR / "SST_WORKBENCH_RESTRUCTURE_MAP_v0.1.legacy_draft.json"


DOMAIN_LETTERS = {
    "01_research": [
        "A_falsifiers",
        "B_closures",
        "C_dynamics",
        "D_benchmarks",
        "E_pipelines",
        "F_exploratory",
    ],
    "02_libraries": [
        "A_knot_libraries",
        "B_finite_core",
    ],
    "03_data": ["A_knots", "B_external", "C_media", "D_generated", "E_reference"],
    "04_tools": ["A_geometry", "B_crawlers", "C_fabrication", "D_proof", "D_compute"],
}


TARGET_LAYOUT = {
    "01_research": {
        "A_falsifiers": "Hypothesis-bearing physics falsifiers; Axxx IDs are chronological and immutable.",
        "B_closures": "Closure, field-equation and bridge research.",
        "C_dynamics": "Reusable vortex/dynamical research workbenches.",
        "D_benchmarks": "Audits, numerical certification and metrology.",
        "E_pipelines": "Dataset, geometry and campaign generation/qualification pipelines.",
        "F_exploratory": "PoCs and exploratory research not yet promoted to a falsifier/closure.",
    },
    "02_libraries": {
        "A_knot_libraries": "Knot geometry library + Knot Library packages.",
        "B_finite_core": "Reusable finite-core selectors/libraries.",
    },
    "03_data": {
        "A_knots": "Knot/source geometry by provenance (01_ideal … 05_twist_knots); no dataset catalog IDs.",
        "B_external": "External scientific datasets (e.g. SPARC).",
        "C_media": "Media assets.",
        "D_generated": "Generated figures, QHP, meshes, research outputs.",
        "E_reference": "Reserved; no concrete moves yet.",
    },
    "04_tools": {
        "A_geometry": "KnotPlot / RidgeRunner tooling.",
        "B_crawlers": "Source crawlers (Katlas).",
        "C_fabrication": "3D generation tooling (source only).",
        "D_proof": "Proof and calculation helper scripts.",
        "D_compute": "Compute probes (SYCL).",
    },
    "05_apps": "Flat domain with catalog IDs (A001…).",
    "06_templates": "Code/project templates; descriptive names only.",
    "07_scripts": "Repository/workbench maintenance scripts.",
    "08_third_party": "Vendored third-party software.",
    "09_archive": "Restore archives, bundles, legacy trees.",
    "10_docs": "inventory / architecture / migration / registry.",
    "DELETE": "Soft-delete staging: DELETE/<original/relative/path>; git mv only, never unlink.",
}


def parse_catalog(md: str) -> list[dict]:
    """Parse CATALOG_v0.1.md tables into family records.

    Rows vary (with/without official name, size, first-version). We take:
    - column 1: catalog_id
    - first backtick field: slug
    - remaining backtick fields joined as current_location
    - last pipe cell: status
    - optional plain-text cells between slug and location as official_name / first_version / size
    """
    families: list[dict] = []
    current_domain = None
    current_letter = None

    for line in md.splitlines():
        if re.match(r"^# 0[1-5]_", line):
            current_domain = line[2:].strip().split()[0]
            current_letter = None
            continue
        if current_domain and current_domain.startswith("0") and re.match(
            r"^# 0[6-9]_", line
        ):
            current_domain = None
            current_letter = None
            continue
        m_letter = re.match(r"^## ([A-F]_[a-z0-9_]+)", line)
        if m_letter and current_domain in ("01_research", "03_data"):
            current_letter = m_letter.group(1)
            continue

        m = re.match(r"^\| ([A-F]\d{3}) \|", line)
        if not m or not current_domain:
            continue
        catalog_id = m.group(1)
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        # Prefer location from table cells that are primarily backtick paths,
        # not from incidental backticks inside the official-name prose.
        status = cells[-1]
        slug_m = re.match(r"^`([^`]+)`$", cells[1].strip())
        if not slug_m:
            continue
        slug = slug_m.group(1)

        location_parts = []
        official = slug
        first_ver = ""
        approx_size = ""
        for i, cell in enumerate(cells[2:-1]):
            cell = cell.strip()
            if re.match(r"^\d{4}-\d{2}-\d{2}", cell) or cell == "TBC":
                first_ver = cell
                continue
            if cell.startswith("~") or (
                re.match(r"^~?\d", cell) and " " not in cell and "/" not in cell
            ):
                approx_size = cell
                continue
            # Pure path cell(s): one or more `path` tokens, optional commas.
            # Ignore incidental inline code in prose (e.g. `.kps` inside official name).
            paths = re.findall(r"`([^`]+)`", cell)
            prose = re.sub(r"`[^`]+`", "", cell).strip()
            looks_like_path_cell = bool(paths) and (
                not prose
                or all(ch in ",;/" for ch in prose.replace(" ", ""))
            )
            if looks_like_path_cell and all(
                ("/" in p)
                or ("*" in p)
                or p.endswith((".py", ".kps", ".lnk", ".stl", ".gcode", ".cmd"))
                or p.startswith(("qhp", "KnotPlot", "GUI", "3D", "SST_", "experiments"))
                for p in paths
            ):
                # Drop extension-only tokens that are not real paths (`.kps`)
                location_parts.extend(
                    p for p in paths if ("/" in p) or ("*" in p) or p[0].isalnum()
                )
                continue
            # Official name (may contain incidental `code` backticks)
            if i == 0 and not cell.startswith("`"):
                official = re.sub(r"`([^`]+)`", r"\1", cell)
                continue
            if cell.startswith("`"):
                location_parts.extend(
                    p for p in paths if ("/" in p) or ("*" in p) or (p and p[0].isalnum())
                )

        location = " + ".join(location_parts)

        letter = _letter_for(current_domain, current_letter, catalog_id)
        fam = {
            "catalog_id": catalog_id,
            "slug": slug,
            "official_name": official,
            "current_location": location.rstrip("/") if location else "",
            "first_version": first_ver,
            "status": status,
            "domain": current_domain,
            "letter": letter,
        }
        if approx_size:
            fam["approx_size"] = approx_size
        families.append(fam)
    return families


def _letter_for(domain, current_letter, catalog_id: str) -> str:
    if domain == "01_research":
        return {
            "A": "A_falsifiers",
            "B": "B_closures",
            "C": "C_dynamics",
            "D": "D_benchmarks",
            "E": "E_pipelines",
            "F": "F_exploratory",
        }[catalog_id[0]]
    if domain == "02_libraries":
        return {
            "A": "A_knot_libraries",
            "B": "B_finite_core",
        }.get(catalog_id[0], "")
    if domain == "03_data":
        # Data no longer uses family catalog IDs in the freeze; ignore if parsed.
        if current_letter:
            return current_letter
        return {
            "A": "A_knots",
            "B": "B_external",
            "C": "C_media",
            "D": "D_generated",
            "E": "E_reference",
        }.get(catalog_id[0], "")
    if domain == "04_tools":
        return {
            "A": "A_geometry",
            "B": "B_crawlers",
            "C": "C_fabrication",
            "D": "D_proof",
        }.get(catalog_id[0], "D_compute")
    if domain == "05_apps":
        return ""
    return current_letter or ""


def load_path_map() -> list[dict]:
    with PATH_MAP.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def index_legacy_versions(legacy: dict) -> dict[str, list[dict]]:
    """Map normalized source path -> list of version_target dicts from legacy JSON."""
    by_source: dict[str, list[dict]] = defaultdict(list)
    by_slug: dict[str, list[dict]] = defaultdict(list)

    def ingest(entry: dict):
        slug = entry.get("slug")
        for vt in entry.get("version_targets") or []:
            src = (vt.get("source") or "").replace("\\", "/")
            if not src:
                continue
            payload = {
                **vt,
                "_legacy_id": entry.get("catalog_id"),
                "_legacy_slug": slug,
            }
            by_source[src].append(payload)
            # parent directory (family container) for matching catalog locations
            parent = "/".join(src.split("/")[:-1])
            if parent:
                by_source[parent].append(payload)
        if slug:
            for vt in entry.get("version_targets") or []:
                by_slug[slug].append(vt)
                by_slug[slug.replace("-", "_")].append(vt)

    for section in (legacy.get("research_catalog") or {}).values():
        for entry in section:
            ingest(entry)
    for section in (legacy.get("non_research_catalog") or {}).values():
        for entry in section if isinstance(section, list) else []:
            ingest(entry)
    return {"by_source": by_source, "by_slug": by_slug}


def target_family_path(fam: dict) -> str:
    if fam["domain"] == "05_apps":
        return f"05_apps/{fam['catalog_id']}_{fam['slug']}"
    return f"{fam['domain']}/{fam['letter']}/{fam['catalog_id']}_{fam['slug']}"


def remap_version_target(vt: dict, fam: dict) -> dict:
    src = vt.get("source") or ""
    source_key = vt.get("source_key") or Path(src).name
    # Stage-1 keeps long version names; stage-2 (SP09) renames to ID-v...
    # Prefer keeping source basename as stage-1 target leaf.
    leaf = Path(src).name if src else source_key
    target = f"{target_family_path(fam)}/{leaf}"
    return {
        "source": src,
        "target": target,
        "created": vt.get("created"),
        "source_key": source_key,
        "stage1_leaf": leaf,
        "stage2_leaf": f"{fam['catalog_id']}-{_normalize_version_key(source_key)}",
    }


def _normalize_version_key(key: str) -> str:
    k = key
    if k.startswith("v") or k.startswith("V"):
        pass
    # collapse underscores used as dots in some packs
    return k.replace("_", "-")


def match_versions(fam: dict, legacy_idx: dict) -> list[dict]:
    loc = fam["current_location"].replace("\\", "/")
    loc_parts = [p.strip().rstrip("/") for p in re.split(r"\s*\+\s*", loc) if p.strip()]
    # File-glob locations (KnotPlot/*.py) are not version directories.
    dirish = [
        p
        for p in loc_parts
        if not (re.search(r"\.\w+$", p) or p.startswith("*."))
    ]
    prefixes = [
        re.sub(r"[*].*$", "", p).rstrip("/").rstrip(",") for p in dirish if p
    ]
    prefixes = [p for p in prefixes if p]
    if not prefixes:
        return []

    candidates: list[dict] = []
    seen: set[str] = set()

    all_sources = []
    for vts in legacy_idx["by_source"].values():
        for vt in vts:
            src = vt.get("source")
            if src:
                all_sources.append(vt)
    unique_vts = []
    seen_src = set()
    for vt in all_sources:
        src = vt["source"]
        if src in seen_src:
            continue
        seen_src.add(src)
        unique_vts.append(vt)

    for vt in unique_vts:
        src_n = vt["source"].replace("\\", "/")
        matched = False
        for p in prefixes:
            if src_n == p or src_n.startswith(p):
                matched = True
                break
            if "/" not in p and (src_n == p or src_n.startswith(p + "/")):
                matched = True
                break
        if not matched or src_n in seen:
            continue
        seen.add(src_n)
        candidates.append(remap_version_target(vt, fam))

    if not candidates:
        for key in (fam["slug"], fam["slug"].replace("_", "-")):
            for vt in legacy_idx["by_slug"].get(key, []):
                src = vt.get("source")
                if not src or src in seen:
                    continue
                seen.add(src)
                candidates.append(remap_version_target(vt, fam))

    return candidates


def build_research_catalog(families: list[dict], legacy_idx: dict) -> dict:
    out: dict[str, list] = {letter: [] for letter in DOMAIN_LETTERS["01_research"]}
    for fam in families:
        if fam["domain"] != "01_research":
            continue
        vts = match_versions(fam, legacy_idx)
        out[fam["letter"]].append(
            {
                "catalog_id": fam["catalog_id"],
                "slug": fam["slug"],
                "official_name": fam["official_name"],
                "target_family": target_family_path(fam),
                "catalog_created_tree": fam.get("first_version") or None,
                "status": fam["status"],
                "source_paths": [fam["current_location"]],
                "mapped_version_count": len(vts),
                "version_targets": vts,
            }
        )
    for letter in out:
        out[letter].sort(key=lambda x: x["catalog_id"])
    return out


def build_non_research(families: list[dict], legacy_idx: dict) -> dict:
    out: dict[str, list] = {
        "02_libraries": [],
        "03_data": [],
        "04_tools": [],
        "05_apps": [],
    }
    for fam in families:
        if fam["domain"] not in out:
            continue
        vts = match_versions(fam, legacy_idx)
        out[fam["domain"]].append(
            {
                "catalog_id": fam["catalog_id"],
                "slug": fam["slug"],
                "official_name": fam["official_name"],
                "letter": fam.get("letter") or None,
                "target_family": target_family_path(fam),
                "status": fam["status"],
                "source_paths": [fam["current_location"]],
                "mapped_version_count": len(vts),
                "version_targets": vts,
            }
        )
    return out


def build_root_plan(path_map_rows: list[dict], plan_md: str) -> list[dict]:
    """One entry per path_map row that is a top-level root move/split, plus non-root extras.

    True family roots are rows whose old_path has no `/` (or KnotPlot subtrees under SP07).
    Non-root path_map rows (root scripts, zips, inventory docs) are tagged is_root=false.
    """
    roots = []
    for row in path_map_rows:
        old = row["old_path"]
        is_root = "/" not in old.replace("\\", "/")
        phase = row["phase"]
        if row["status"] == "skipped":
            action = "skip"
        elif "SP07" in phase or old.startswith("KnotPlot"):
            action = "split"
        elif "SP06" in phase:
            action = "split"
        else:
            action = "move"

        child_ids = []
        if is_root:
            child_ids = sorted(
                {
                    r["catalog_id"]
                    for r in path_map_rows
                    if (
                        r["old_path"] == old
                        or r["old_path"].startswith(old + "/")
                        or r["old_path"].startswith(old + "\\")
                    )
                    and r.get("catalog_id")
                }
            )
        elif row.get("catalog_id"):
            child_ids = [row["catalog_id"]]

        roots.append(
            {
                "source_root": old if is_root else old.split("/")[0].split("\\")[0],
                "source_path": old,
                "is_top_level_root": is_root,
                "action": action,
                "destination": row["new_path"] if action == "move" else row["new_path"],
                "catalog_ids": child_ids,
                "phase": phase,
                "kind": row.get("kind"),
                "junction": row.get("junction"),
                "status": row.get("status"),
                "note": row.get("note") or None,
            }
        )
    roots.sort(key=lambda r: (not r["is_top_level_root"], r["source_path"].lower()))
    return roots


def build_operations(path_map_rows: list[dict]) -> list[dict]:
    """Flatten path_map into SP-aligned operations (not the old 10/20/30 phases)."""
    phase_order = {
        "SP03": 30,
        "SP04": 40,
        "SP05": 50,
        "SP06": 60,
        "SP07": 70,
        "SP08": 80,
        "SP09": 90,
        "SP10": 100,
        "SP11": 110,
    }
    ops = []
    # namespace ensures
    n = 1
    for domain, letters in DOMAIN_LETTERS.items():
        for letter in letters:
            ops.append(
                {
                    "op_id": f"N{n:04d}",
                    "phase": "SP03",
                    "action": "ensure_directory",
                    "source": None,
                    "destination": f"{domain}/{letter}",
                }
            )
            n += 1
    for domain in ("05_apps", "06_templates", "07_scripts", "08_third_party", "09_archive", "10_docs"):
        ops.append(
            {
                "op_id": f"N{n:04d}",
                "phase": "SP03",
                "action": "ensure_directory",
                "source": None,
                "destination": domain,
            }
        )
        n += 1

    m = 1
    for row in path_map_rows:
        if row["status"] == "skipped":
            action = "skip"
        elif "/" in row["old_path"] or row["phase"] in ("SP06", "SP07", "SP06 / SP11"):
            action = "split_or_move"
        else:
            action = "move"
        ops.append(
            {
                "op_id": f"M{m:04d}",
                "phase": row["phase"].split("/")[0].strip(),
                "action": action,
                "source": row["old_path"],
                "destination": row["new_path"],
                "catalog_id": row.get("catalog_id") or None,
                "kind": row.get("kind"),
                "junction": row.get("junction"),
                "status": row.get("status"),
                "note": row.get("note") or None,
                "phase_rank": phase_order.get(row["phase"].split("/")[0].strip(), 999),
            }
        )
        m += 1
    return ops


def main() -> None:
    catalog_md = CATALOG_MD.read_text(encoding="utf-8")
    plan_md = PLAN_MD.read_text(encoding="utf-8")
    families = parse_catalog(catalog_md)
    path_map_rows = load_path_map()

    if not BACKUP_JSON.exists() and LEGACY_JSON.exists():
        BACKUP_JSON.write_text(LEGACY_JSON.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Backed up legacy draft -> {BACKUP_JSON.name}")

    legacy = json.loads(
        (BACKUP_JSON if BACKUP_JSON.exists() else LEGACY_JSON).read_text(encoding="utf-8")
    )
    legacy_idx = index_legacy_versions(legacy)

    research = build_research_catalog(families, legacy_idx)
    non_research = build_non_research(families, legacy_idx)
    root_plan = build_root_plan(path_map_rows, plan_md)
    operations = build_operations(path_map_rows)
    top_level_roots = [r for r in root_plan if r["is_top_level_root"]]

    research_count = sum(len(v) for v in research.values())
    non_count = sum(len(v) for v in non_research.values())
    version_mapped = sum(
        e["mapped_version_count"]
        for section in list(research.values()) + list(non_research.values())
        for e in section
    )

    if research_count < 70:
        raise SystemExit(
            f"Expected ~73+ research families, got {research_count} "
            f"(non_research={non_count})"
        )

    merged = {
        "schema": "SST-WORKBENCH-RESTRUCTURE-MAP-0.1",
        "generated_for": "SST-Workbench",
        "merged_at": datetime.now(timezone.utc).isoformat(),
        "authoritative_sources": {
            "catalog": "CATALOG_v0.1.md",
            "plan": "RESTRUCTURE_PLAN_v0.1.plan.md",
            "path_map": "10_docs/migration/path_map.csv",
            "epic": "RESTRUCTURE_EPIC.plan.md",
            "legacy_draft_backup": BACKUP_JSON.name,
            "precedence": [
                "path_map.csv (machine-checked moves)",
                "CATALOG_v0.1.md (permanent IDs)",
                "RESTRUCTURE_PLAN_v0.1.plan.md (root destinations)",
                "legacy draft (version timestamps / source keys only, remapped)",
            ],
        },
        "basis": {
            **legacy.get("basis", {}),
            "aligned_to_catalog": True,
            "path_map_rows": len(path_map_rows),
            "catalog_family_count": research_count + non_count,
            "note": (
                "Regenerated to match CATALOG_v0.1 / RESTRUCTURE_PLAN_v0.1 / path_map.csv. "
                "Legacy draft used different A/B/C ID allocation and target_layout; "
                "IDs in this file follow CATALOG. Stage-1 version leaves keep long names; "
                "stage2_leaf shows the SP09 rename target."
            ),
        },
        "naming_policy": {
            "top_level": "NN_domain",
            "research_section": "LETTER_section",
            "research_family": "{catalog_id}_{slug}",
            "research_version_stage1": "<long official / existing version directory name>",
            "research_version_stage2": "{catalog_id}-{version}",
            "examples": [
                "01_research/A_falsifiers/A038_trefoil_dynamic_seed_qualification/<long>/",
                "01_research/A_falsifiers/A038_trefoil_dynamic_seed_qualification/A038-v0.3.0",
                "DELETE/to_be_processed/",
            ],
            "catalog_id_rules": [
                "IDs follow CATALOG_v0.1.md and are permanent after that document is committed.",
                "Axxx falsifiers are chronological within A_falsifiers (A001-A042).",
                "03_data has no per-dataset catalog IDs in this freeze.",
                "Version changes do not allocate a new catalog ID.",
                "Reveal keys and blind variants are not families and get no catalog ID.",
                "Former delete candidates are git_mv'd to DELETE/<original/relative/path>.",
            ],
        },
        "target_layout": TARGET_LAYOUT,
        "research_catalog": research,
        "non_research_catalog": non_research,
        "root_plan": root_plan,
        "path_map_rows": path_map_rows,
        "migration_phases": [
            {"phase": "SP00", "name": "freeze_and_provenance", "status": "DONE"},
            {"phase": "SP01", "name": "path_resolver", "status": "PLANNED"},
            {"phase": "SP02", "name": "compat_junction_layer", "status": "PLANNED"},
            {"phase": "SP03", "name": "catalog_skeleton_and_hygiene", "status": "PLANNED"},
            {"phase": "SP04", "name": "low_risk_moves", "status": "PLANNED"},
            {"phase": "SP05", "name": "clean_family_moves", "status": "PLANNED"},
            {"phase": "SP06", "name": "container_splits", "status": "PLANNED"},
            {"phase": "SP07", "name": "knotplot_refactor", "status": "PLANNED"},
            {"phase": "SP08", "name": "catalog_metadata_and_registry", "status": "PLANNED"},
            {"phase": "SP09", "name": "version_rename_stage2", "status": "PLANNED"},
            {"phase": "SP10", "name": "reproducibility_gate", "status": "PLANNED"},
            {"phase": "SP11", "name": "decommission_soft_delete", "status": "PLANNED"},
        ],
        "operations": operations,
        "safety_rules": [
            "git_mv_only — never unlink research or stub content.",
            "Former delete candidates → DELETE/<original/relative/path> via git mv.",
            "Every move gets a path_map.csv row before execution.",
            "Old paths keep working via junctions until SP11.",
            "Reproducibility beats tidiness.",
            "Blind and revealed artifacts are never merged.",
        ],
        "coverage": {
            "root_families_total": 73,
            "top_level_root_plan_entries": len(top_level_roots),
            "path_map_rows": len(path_map_rows),
            "path_map_root_plan_entries": len(root_plan),
            "catalog_families_total": research_count + non_count,
            "research_catalog_family_count": research_count,
            "non_research_catalog_family_count": non_count,
            "version_targets_remapped_from_legacy": version_mapped,
            "flattened_operation_count": len(operations),
            "delete_staging_prefix": "DELETE/",
        },
        "id_realignment_note": (
            "Canonical IDs follow CATALOG_v0.1.md as frozen 2026-09-04 "
            "(A001=route_a_parallel_derivation_falsification … A042=quantum_galileo). "
            "01/02/03 layout follows the user inventory-map tables; soft-deletes use DELETE/."
        ),
    }

    OUT_JSON.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"catalog families parsed: {len(families)}")
    print(f"research={research_count} non_research={non_count} total={research_count+non_count}")
    print(f"root_plan={len(root_plan)} path_map={len(path_map_rows)} ops={len(operations)}")
    print(f"version_targets remapped: {version_mapped}")

    # sanity: A001 must be contact_billiard
    a001 = next(x for x in research["A_falsifiers"] if x["catalog_id"] == "A001")
    assert a001["slug"] == "route_a_parallel_derivation_falsification", a001["slug"]
    a006 = next(x for x in research["A_falsifiers"] if x["catalog_id"] == "A006")
    assert a006["slug"] == "contact_billiard_hydrodynamic", a006["slug"]
    a042 = next(x for x in research["A_falsifiers"] if x["catalog_id"] == "A042")
    assert a042["slug"] == "quantum_galileo_action_gauge_closure", a042["slug"]
    print("A001/A006/A042 OK:", a001["slug"], a006["slug"], a042["slug"])
    print("A_falsifiers count:", len(research["A_falsifiers"]))


if __name__ == "__main__":
    main()
