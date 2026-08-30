"""Consolidate Workbench *.zip files under Restore_Archives/<theme>/...

Default mode is dry-run. Pass --apply to move files.

Collision rule when destination basename already exists:
  - same size + SHA256 -> delete source (duplicate)
  - different -> move as <stem>__from_repo.zip (or __from_sources if from Sources_Zips)

Usage (from Workbench root):
  python scripts/consolidate_archives.py
  python scripts/consolidate_archives.py --apply
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

WB = Path(__file__).resolve().parents[1]
RESTORE = WB / "Restore_Archives"
SOURCES_ZIPS = RESTORE / "Sources_Zips"
MANIFEST_NAME = "_MANIFEST.csv"
SKIP_DIR_NAMES = {".git", ".venv", "node_modules", "__pycache__", ".tmp.driveupload"}

# Ordered (theme, series_or_None, compiled pattern) — first match wins.
THEME_RULES: list[tuple[str, str | None, re.Pattern[str]]] = [
    ("Fermat", None, re.compile(r"fermat", re.I)),
    ("ContactBilliard", None, re.compile(r"contact_billiard|billiard_hydro", re.I)),
    ("Dimensionless", None, re.compile(r"dimensionless|relclock", re.I)),
    ("IdealLinks", None, re.compile(
        r"ideal_links|Ideal_Links|continuum_ladder|"
        r"CMD_runners_patch|reporting_CMD_hotfix",
        re.I,
    )),
    ("KelvinFloquet", None, re.compile(
        r"Kelvin_Floquet|KelvinFloquet|Kelvin_Joule|Kelvin_Kirchhoff", re.I
    )),
    ("Route_I", None, re.compile(r"Route_I|relative_entropy|routeI_", re.I)),
    ("Routes_v0819", None, re.compile(
        r"v0_8_19|Planck_Routes|RouteA_|nonfit|torsion_impedance|route_ABCD", re.I
    )),
    ("RouteB_BEM", None, re.compile(r"routeB|BEM|bem_|Steklov|stecklov", re.I)),
    ("ChiPhase", None, re.compile(r"chi_phase|chiE|sstcore_chiE", re.I)),
    ("Coil", None, re.compile(
        r"Coil|coil_|rodin_GUI|SawBowl|sawcoil|Halbach|halbach|starshaped", re.I
    )),
    ("VortexLab", None, re.compile(r"vortexring|vortexlab|VortexLab", re.I)),
    ("Maxwell", None, re.compile(r"Maxwell", re.I)),
    ("Falsifiers", None, re.compile(
        r"falsif|minimal_falsif|Sutcliffe|dark_knot|Gilbert|"
        r"Einstein_SST|Helmholtz_SST",
        re.I,
    )),
    ("DeriveConstants", None, re.compile(
        r"Derive_Constants|derive_|gp_core|phase_pressure|half_budget|"
        r"finite_cell|finite.?core|FiniteCore|accessible_area|pressure_mode|"
        r"nonlinear_shape|nlse_|phase_budget|next_step_two_gate|"
        r"SpectralSelector",
        re.I,
    )),
    ("Trefoil", None, re.compile(r"Trefoil|trefoil|biot|trefoil_closure", re.I)),
    ("Hopf", None, re.compile(r"Hopf|hopf", re.I)),
    ("Horn_SSDL", None, re.compile(r"horn|ssdl", re.I)),
    ("FS_Attachment", None, re.compile(r"fs_|attachment|hopfion", re.I)),
    ("Bridge", None, re.compile(
        r"contra_swirl|bridge|timefield|CASTLE|Eckvahl", re.I
    )),
    ("KnotPlot", None, re.compile(
        r"KnotPlot|knotplot|ridgerunner|RidgeRunner|Fresnel|"
        r"Knots_Fourier|knots\.zip|fseries|ideal_3_1",
        re.I,
    )),
    ("SST21D", None, re.compile(r"SST21D|21D_knot", re.I)),
    ("Templates", None, re.compile(r"template|pybind_audit_template", re.I)),
    ("Datasets", None, re.compile(
        r"SPARC|portfolio|visualization|Hydrodynamic|"
        r"Electron_Scale|Kelvin_Mode|Relational_Time|sn-article",
        re.I,
    )),
    ("ProofScripts", None, re.compile(
        r"VAM_|VAM_Fseries|SST_Fseries|knots_for_particles|"
        r"canon_evidence|twistknots|proof",
        re.I,
    )),
    ("TripleGear", None, re.compile(r"Triple.?[Gg]ear|triple_gear", re.I)),
    ("Canon", None, re.compile(
        r"SST_CANON|SST_Canon|NotebookLM|architecture_patch|"
        r"rhoF-cosmological|cantarella|eight-source|whisper_asr|"
        r"orthodox_vortex|ovms_windows",
        re.I,
    )),
]


# Run-output archives stay next to research packs until SSTcore ingest.
_OUTPUT_ZIP_RE = re.compile(
    r"(?:^|[_-])outputs?(?:[_-]|\.zip$)|(?:^|[_-])output\.zip$",
    re.I,
)

DOWNLOADS_DIR = Path.home() / "Downloads"

# Source/hotfix families to copy from Downloads into Restore_Archives.
DOWNLOADS_INGEST_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"SST_Intrinsic_Modal_Swirl_Clock", re.I),
    re.compile(r"SST_SCII", re.I),
    re.compile(r"SST_SCIIb", re.I),
    re.compile(r"SST_Breathing_Stretching", re.I),
    re.compile(r"SST_Chirality_Helicity", re.I),
    re.compile(r"SST_QHP_Stability", re.I),
    re.compile(r"SST_KnotPlot_QHP_Sweep_Generator", re.I),
    re.compile(r"SST_Trefoil_Dynamic_Seed", re.I),
    re.compile(r"KnotPlot_MultiTopology_QHP_Sweep", re.I),
    re.compile(r"Trefoil_Balance_Point_Campaign", re.I),
]


def is_output_archive(basename: str) -> bool:
    """True for campaign/run output zips that must not leave the working tree."""
    return bool(_OUTPUT_ZIP_RE.search(basename))


def matches_downloads_ingest(basename: str) -> bool:
    if is_output_archive(basename):
        return False
    return any(pat.search(basename) for pat in DOWNLOADS_INGEST_PATTERNS)


def canonical_zip_basename(basename: str) -> str:
    """Strip Chrome duplicate suffixes like ' (1).zip'."""
    return re.sub(r"\s+\(\d+\)\.zip$", ".zip", basename, flags=re.I)


def classify(basename: str) -> tuple[str, str | None]:
    """Return (theme, series) for a zip basename."""
    name = basename
    series: str | None = None

    # Series hints (optional nesting)
    m = re.search(r"v(\d+(?:\.\d+)+)", name, re.I)
    if m and re.search(r"fermat", name, re.I):
        series = f"v{m.group(1)}"
    elif re.search(r"vortexring-lab-v7\.6", name, re.I):
        series = "v7.6-release-train"
    elif re.search(r"chi_phase_package_v\d+", name, re.I):
        series = "TrackB"
    elif re.search(r"chiE_local", name, re.I):
        series = "chiE"

    for theme, rule_series, pat in THEME_RULES:
        if pat.search(name):
            return theme, rule_series or series
    return "Misc", series


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def should_skip_dir(path: Path) -> bool:
    return path.name in SKIP_DIR_NAMES


@dataclass
class PlannedMove:
    source: Path
    dest: Path
    theme: str
    series: str | None
    action: str  # move | copy | delete_duplicate | skip_duplicate | move_renamed | copy_renamed
    note: str = ""


def iter_zips_outside_restore(root: Path | None = None) -> list[Path]:
    if root is None:
        root = WB
    found: list[Path] = []
    for p in root.rglob("*.zip"):
        if not p.is_file():
            continue
        try:
            rel = p.relative_to(root)
        except ValueError:
            continue
        parts = set(rel.parts)
        if parts & SKIP_DIR_NAMES:
            continue
        if rel.parts and rel.parts[0] == "Restore_Archives":
            continue
        found.append(p)
    return sorted(found)


def iter_sources_zips() -> list[Path]:
    if not SOURCES_ZIPS.is_dir():
        return []
    return sorted(p for p in SOURCES_ZIPS.glob("*.zip") if p.is_file())


def iter_restore_root_zips() -> list[Path]:
    """Zips sitting directly in Restore_Archives/ (not in theme subdirs)."""
    if not RESTORE.is_dir():
        return []
    return sorted(p for p in RESTORE.glob("*.zip") if p.is_file())


def dest_for(basename: str, theme: str, series: str | None) -> Path:
    base = RESTORE / theme
    if series:
        base = base / series
    return base / basename


def resolve_collision(
    source: Path,
    dest: Path,
    rename_suffix: str,
) -> PlannedMove:
    rel_parts = dest.relative_to(RESTORE).parts
    theme = rel_parts[0]
    series = rel_parts[1] if len(rel_parts) >= 3 else None

    existing: Path | None = dest if dest.exists() else None
    if existing is None:
        # Phase1 may still hold this basename under Sources_Zips
        alt = SOURCES_ZIPS / source.name
        if alt.is_file() and alt.resolve() != source.resolve():
            existing = alt

    if existing is None:
        return PlannedMove(source, dest, theme, series, "move")

    same_size = existing.stat().st_size == source.stat().st_size
    if same_size and sha256_file(existing) == sha256_file(source):
        return PlannedMove(
            source,
            dest,
            theme,
            series,
            "delete_duplicate",
            note="identical to existing Restore_Archives / Sources_Zips copy",
        )

    stem = dest.stem
    renamed = dest.with_name(f"{stem}{rename_suffix}{dest.suffix}")
    n = 2
    while renamed.exists():
        renamed = dest.with_name(f"{stem}{rename_suffix}_{n}{dest.suffix}")
        n += 1
    return PlannedMove(
        source,
        renamed,
        theme,
        series,
        "move_renamed",
        note=f"content differs from {existing.name}",
    )


def plan_sources() -> list[PlannedMove]:
    plans: list[PlannedMove] = []
    for src in iter_sources_zips():
        theme, series = classify(src.name)
        dest = dest_for(src.name, theme, series)
        plans.append(resolve_collision(src, dest, "__from_sources"))
    return plans


def plan_repo() -> list[PlannedMove]:
    plans: list[PlannedMove] = []
    for src in iter_zips_outside_restore():
        if is_output_archive(src.name):
            continue
        theme, series = classify(src.name)
        dest = dest_for(src.name, theme, series)
        plans.append(resolve_collision(src, dest, "__from_repo"))
    return plans


def iter_downloads_ingest_zips(downloads: Path | None = None) -> list[Path]:
    root = downloads if downloads is not None else DOWNLOADS_DIR
    if not root.is_dir():
        return []
    found: list[Path] = []
    for p in sorted(root.glob("*.zip")):
        if not p.is_file():
            continue
        if not matches_downloads_ingest(p.name):
            continue
        found.append(p)
    return found


def plan_downloads_copy(downloads: Path | None = None) -> list[PlannedMove]:
    """Copy matching Downloads zips into Restore_Archives (never delete Downloads)."""
    plans: list[PlannedMove] = []
    for src in iter_downloads_ingest_zips(downloads):
        dest_name = canonical_zip_basename(src.name)
        theme, series = classify(dest_name)
        dest = dest_for(dest_name, theme, series)
        plans.append(resolve_collision(src, dest, "__from_downloads"))
        if plans[-1].action == "move":
            plans[-1].action = "copy"
        elif plans[-1].action == "move_renamed":
            plans[-1].action = "copy_renamed"
        elif plans[-1].action == "delete_duplicate":
            plans[-1].action = "skip_duplicate"
            plans[-1].note = "identical copy already in Restore_Archives; Downloads kept"
    return plans


def plan_restore_root() -> list[PlannedMove]:
    plans: list[PlannedMove] = []
    for src in iter_restore_root_zips():
        theme, series = classify(src.name)
        dest = dest_for(src.name, theme, series)
        if dest.resolve() == src.resolve():
            continue
        plans.append(resolve_collision(src, dest, "__from_root"))
    return plans


def plan_misc_reclassify() -> list[PlannedMove]:
    """Move Misc zips that now classify to a real theme (e.g. IdealLinks)."""
    plans: list[PlannedMove] = []
    misc = RESTORE / "Misc"
    if not misc.is_dir():
        return plans
    for src in sorted(misc.rglob("*.zip")):
        if not src.is_file():
            continue
        theme, series = classify(src.name)
        if theme == "Misc":
            continue
        dest = dest_for(src.name, theme, series)
        try:
            if dest.resolve() == src.resolve():
                continue
        except FileNotFoundError:
            pass
        plans.append(resolve_collision(src, dest, "__from_misc"))
    return plans


def plan_all() -> list[PlannedMove]:
    """Sources → repo → Restore root → Misc reclassify (apply phases sequentially)."""
    return (
        plan_sources()
        + plan_repo()
        + plan_restore_root()
        + plan_misc_reclassify()
    )



def ensure_parent(path: Path, apply: bool) -> None:
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)


def apply_plan(plans: list[PlannedMove], apply: bool) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for p in plans:
        rel_src = _rel(p.source)
        rel_dst = _rel(p.dest)
        size = p.source.stat().st_size if p.source.exists() else 0

        if p.action in {"delete_duplicate", "skip_duplicate"}:
            if p.dest.exists():
                digest = sha256_file(p.dest)
            elif p.source.exists():
                digest = sha256_file(p.source)
            else:
                digest = ""
            if apply and p.action == "delete_duplicate":
                p.source.unlink()
            rows.append(
                {
                    "action": p.action,
                    "theme": p.theme,
                    "series": p.series or "",
                    "basename": p.dest.name,
                    "size": str(size),
                    "sha256": digest,
                    "source_path": rel_src,
                    "dest_path": rel_dst,
                    "note": p.note,
                }
            )
            continue

        if apply:
            ensure_parent(p.dest, True)
            if p.action in {"copy", "copy_renamed"}:
                shutil.copy2(str(p.source), str(p.dest))
            else:
                shutil.move(str(p.source), str(p.dest))
            digest = sha256_file(p.dest)
            out_size = p.dest.stat().st_size
        else:
            digest = sha256_file(p.source) if p.source.exists() else ""
            out_size = size

        rows.append(
            {
                "action": p.action,
                "theme": p.theme,
                "series": p.series or "",
                "basename": p.dest.name,
                "size": str(out_size),
                "sha256": digest,
                "source_path": rel_src,
                "dest_path": rel_dst,
                "note": p.note,
            }
        )
    return rows


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(WB)).replace("\\", "/")
    except ValueError:
        return str(path)


def write_manifest(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "action",
        "theme",
        "series",
        "basename",
        "size",
        "sha256",
        "source_path",
        "dest_path",
        "note",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def remove_empty_sources_zips(apply: bool) -> bool:
    if not SOURCES_ZIPS.is_dir():
        return False
    leftover = list(SOURCES_ZIPS.iterdir())
    if leftover:
        return False
    if apply:
        SOURCES_ZIPS.rmdir()
    return True


def _summarize(plans: list[PlannedMove]) -> dict[str, int]:
    by_action: dict[str, int] = {}
    for p in plans:
        by_action[p.action] = by_action.get(p.action, 0) + 1
    return by_action


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--apply",
        action="store_true",
        help="Perform moves (default is dry-run)",
    )
    ap.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Manifest CSV path (default Restore_Archives/_MANIFEST.csv)",
    )
    args = ap.parse_args(argv)
    apply = bool(args.apply)
    manifest_path = args.manifest or (RESTORE / MANIFEST_NAME)

    mode = "APPLY" if apply else "DRY-RUN"

    # Phase 0: copy matching Downloads zips (Downloads is never deleted)
    phase0 = plan_downloads_copy()
    print(f"[{mode}] phase0 Downloads copy: {len(phase0)} ops {_summarize(phase0)}")
    rows = apply_plan(phase0, apply=apply)

    # Phase 1: reorganize Sources_Zips into themes
    phase1 = plan_sources()
    print(f"[{mode}] phase1 Sources_Zips: {len(phase1)} ops {_summarize(phase1)}")
    rows.extend(apply_plan(phase1, apply=apply))

    # Phase 2: move remaining Workbench zips (collisions see phase1 destinations)
    phase2 = plan_repo()
    print(f"[{mode}] phase2 repo zips: {len(phase2)} ops {_summarize(phase2)}")
    rows.extend(apply_plan(phase2, apply=apply))

    # Phase 3: zips left in Restore_Archives/ root
    phase3 = plan_restore_root()
    print(f"[{mode}] phase3 Restore root: {len(phase3)} ops {_summarize(phase3)}")
    rows.extend(apply_plan(phase3, apply=apply))

    # Phase 4: reclassify Misc into new/updated themes
    phase4 = plan_misc_reclassify()
    print(f"[{mode}] phase4 Misc reclassify: {len(phase4)} ops {_summarize(phase4)}")
    rows.extend(apply_plan(phase4, apply=apply))

    write_manifest(rows, manifest_path)
    if not rows and apply is False:
        # Keep a useful inventory when there is nothing left to move
        rows = scan_restore_manifest()
        write_manifest(rows, manifest_path)
        print(f"manifest refreshed from Restore_Archives/ ({len(rows)} rows)")
    else:
        print(f"manifest: {_rel(manifest_path)} ({len(rows)} rows)")

    removed = remove_empty_sources_zips(apply)
    if removed:
        print(f"[{mode}] removed empty Sources_Zips/")
    elif SOURCES_ZIPS.is_dir() and apply:
        leftover = list(SOURCES_ZIPS.iterdir())
        print(f"Sources_Zips not empty ({len(leftover)} entries); not removed")

    if not apply:
        print("Re-run with --apply to execute.")
    return 0


def scan_restore_manifest() -> list[dict[str, str]]:
    """Build manifest rows from current Restore_Archives/*.zip layout."""
    rows: list[dict[str, str]] = []
    if not RESTORE.is_dir():
        return rows
    for z in sorted(RESTORE.rglob("*.zip")):
        if not z.is_file():
            continue
        rel = z.relative_to(RESTORE)
        parts = rel.parts
        theme = parts[0] if parts else "Misc"
        series = parts[1] if len(parts) >= 3 else ""
        rows.append(
            {
                "action": "present",
                "theme": theme,
                "series": series,
                "basename": z.name,
                "size": str(z.stat().st_size),
                "sha256": sha256_file(z),
                "source_path": "",
                "dest_path": _rel(z),
                "note": "inventory scan",
            }
        )
    return rows


if __name__ == "__main__":
    sys.exit(main())
