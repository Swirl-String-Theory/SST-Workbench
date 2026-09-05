#!/usr/bin/env python3
"""One-shot scaffold + copy for Knot_Library provenance layout. Safe to re-run."""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KL = Path(__file__).resolve().parent
WB = ROOT

PROVIDERS = [
    {
        "provider_id": "gilbert_ideal",
        "provider_name": "Brian Gilbert Ideal Knots",
        "directory": "Ideal_Gilbert",
        "construction_objective": (
            "SONO relaxation to approximately ideal/minimal-rope geometry, "
            "then Fourier representation (max 256 A_i,B_i)."
        ),
        "class_default": "original",
        "subdirs": ["original", "extracted"],
    },
    {
        "provider_id": "fremlin_fourier",
        "provider_name": "David Fremlin Fourier-Series Knots",
        "directory": "FourierSeries_Fremlin",
        "construction_objective": (
            "Elegant/symmetric 3D realization represented as coordinate lists and Fourier series."
        ),
        "class_default": "original",
        "subdirs": ["original", "extracted"],
    },
    {
        "provider_id": "knotplot",
        "provider_name": "Robert G. Scharein KnotPlot",
        "directory": "KnotPlot_Scharein",
        "construction_objective": (
            "KnotPlot-authored geometry: database originals, seeds, exports, "
            "and SST relaxation campaigns (scientifically distinct classes)."
        ),
        "class_default": "unknown",
        "subdirs": [
            "Database_Original",
            "Initial_Seeds",
            "Relaxed",
            "Fourier_Exports",
            "VECT_Exports",
            "SST_Relaxation_Campaigns",
        ],
    },
    {
        "provider_id": "ridgerunner",
        "provider_name": "Ridgerunner (Cantarella/Rawdon)",
        "directory": "Ridgerunner_Cantarella_Rawdon",
        "construction_objective": (
            "Constrained ropelength relaxation / near-ideal polylines "
            "(distinct from KnotPlot and Gilbert ideal Fourier)."
        ),
        "class_default": "original",
        "subdirs": [
            "original",
            "Seeds",
            "N0600",
            "N1200",
            "Continued",
            "NearIdeal",
            "Final",
        ],
    },
    {
        "provider_id": "katlas",
        "provider_name": "The Knot Atlas (Bar-Natan)",
        "directory": "KAtlas_BarNatan",
        "construction_objective": (
            "Topology/reference source: presentations, braid seeds, offline snapshot "
            "— not SST 3D realizations."
        ),
        "class_default": "snapshot",
        "subdirs": ["snapshot", "topology", "braid_seeds"],
    },
    {
        "provider_id": "sst_generated",
        "provider_name": "SST Generated Geometries",
        "directory": "SST_Generated",
        "construction_objective": (
            "SST-authored analytic, braid-derived, shader-inspired, and other constructed "
            "embeddings (never mixed with upstream providers)."
        ),
        "class_default": "generated",
        "subdirs": [
            "Analytic/ClassicTrefoil",
            "Analytic/TorusKnot",
            "TrackTrefoil",
            "BraidClosure",
            "KAtlasBraidDerived",
            "S3Projection",
            "ThreadBundle",
            "PerturbedSeeds",
        ],
    },
]

QUARANTINE = [
    "Unknown_Source",
    "Unknown_Format",
    "Topology_Mismatch",
    "Hash_Mismatch",
]
CORE = ["3_1", "4_1", "6_2", "7_4"]
# Gilbert AB Id scheme is crossings:1:index (Rolfsen order within crossing number),
# not Rolfsen underscore form. Verified via Conway attrs in Ideal.txt.gz.
GILBERT_IDS = {"3_1": "3:1:1", "4_1": "4:1:1", "6_2": "6:1:2", "7_4": "7:1:4"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def copy_file(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return sha256_file(dst)


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8", newline="\n")


def ensure_gitkeep(d: Path) -> None:
    d.mkdir(parents=True, exist_ok=True)
    if not any(d.iterdir()):
        (d / ".gitkeep").write_text("", encoding="utf-8")


def clear_gitkeep_if_populated(d: Path) -> None:
    gk = d / ".gitkeep"
    if gk.exists() and any(p.name != ".gitkeep" for p in d.iterdir()):
        gk.unlink()


def scaffold() -> None:
    for name in ["Sources", "Registry", "Derived", "Quarantine"]:
        (KL / name).mkdir(parents=True, exist_ok=True)

    for q in QUARANTINE:
        ensure_gitkeep(KL / "Quarantine" / q)

    ensure_gitkeep(KL / "Derived")
    (KL / "Registry").mkdir(parents=True, exist_ok=True)

    providers_index = {"schema": "sst-knot-library-providers/1", "providers": {}}
    for p in PROVIDERS:
        base = KL / "Sources" / p["directory"]
        base.mkdir(parents=True, exist_ok=True)
        for sd in p["subdirs"]:
            ensure_gitkeep(base / sd)
        write_json(
            base / "SOURCE.json",
            {
                "schema": "sst-knot-library-source/1",
                "provider_id": p["provider_id"],
                "provider_name": p["provider_name"],
                "directory": p["directory"],
                "class": p["class_default"],
                "construction_objective": p["construction_objective"],
                "origin_paths": [],
                "copied": False,
                "moved": False,
            },
        )
        providers_index["providers"][p["provider_id"]] = {
            "directory": p["directory"],
            "provider_name": p["provider_name"],
            "path": f"Sources/{p['directory']}",
        }
    write_json(KL / "Registry" / "providers.json", providers_index)
    print("scaffold ok")


def copy_gilbert(manifest_hashes: dict[str, str]) -> None:
    gilbert_dir = KL / "Sources" / "Ideal_Gilbert"
    gilbert_orig = gilbert_dir / "original"
    gilbert_gz = [
        "Ideal.txt.gz",
        "Ideal_11a.txt.gz",
        "Ideal_11n.txt.gz",
        "IdealLinks.txt.gz",
        "IdealLinks_10a.txt.gz",
        "IdealLinks_10n.txt.gz",
        "IdealLinks_11a1.txt.gz",
        "IdealLinks_11a2.txt.gz",
        "IdealLinks_11n1.txt.gz",
        "IdealLinks_11n2.txt.gz",
    ]
    ideal_src = WB / "Ideal_Sources"
    gilbert_origin = []
    for name in gilbert_gz:
        src = ideal_src / name
        dst = gilbert_orig / name
        h = copy_file(src, dst)
        expected = manifest_hashes.get(name)
        if expected and h != expected:
            raise SystemExit(f"hash mismatch Gilbert {name}: {h} != {expected}")
        gilbert_origin.append(f"Ideal_Sources/{name}")
        print(f"Gilbert copy OK {name}")
    clear_gitkeep_if_populated(gilbert_orig)

    text = gzip.open(ideal_src / "Ideal.txt.gz", "rt", encoding="utf-8", errors="ignore").read()
    for topo, ab_id in GILBERT_IDS.items():
        m = re.search(
            rf'(<AB\s+Id="{re.escape(ab_id)}"[^>]*>.*?</AB>)',
            text,
            flags=re.DOTALL,
        )
        if not m:
            raise SystemExit(f"missing AB block {ab_id}")
        out = gilbert_dir / "extracted" / topo / f"{topo}_AB.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(m.group(1) + "\n", encoding="utf-8", newline="\n")
        print(f"extracted {ab_id} -> {out.relative_to(KL)}")
    clear_gitkeep_if_populated(gilbert_dir / "extracted")

    write_json(
        gilbert_dir / "SOURCE.json",
        {
            "schema": "sst-knot-library-source/1",
            "provider_id": "gilbert_ideal",
            "provider_name": "Brian Gilbert Ideal Knots",
            "directory": "Ideal_Gilbert",
            "class": "original",
            "construction_objective": (
                "SONO relaxation to approximately ideal/minimal-rope geometry, "
                "then Fourier representation (max 256 A_i,B_i)."
            ),
            "origin_paths": gilbert_origin,
            "copied": True,
            "moved": False,
            "extracted_core_knots": CORE,
            "extracted_ab_ids": GILBERT_IDS,
        },
    )


def copy_fremlin() -> None:
    fremlin_src = WB / "Ideal_Fremlin_Fseries" / "fremlin"
    fremlin_dir = KL / "Sources" / "FourierSeries_Fremlin"
    fremlin_orig = fremlin_dir / "original"
    # Prefer incremental copy to avoid Windows rmtree locks on large trees.
    fremlin_orig.mkdir(parents=True, exist_ok=True)
    gk = fremlin_orig / ".gitkeep"
    if gk.exists():
        gk.unlink()
    for src in fremlin_src.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(fremlin_src)
        dst = fremlin_orig / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or dst.stat().st_size != src.stat().st_size:
            shutil.copy2(src, dst)
    n = sum(1 for p in fremlin_orig.rglob("*") if p.is_file())
    print(f"Fremlin original files: {n}")
    for topo in CORE:
        src = fremlin_src / topo
        dst = fremlin_dir / "extracted" / topo
        dst.mkdir(parents=True, exist_ok=True)
        for f in src.iterdir():
            if f.is_file():
                shutil.copy2(f, dst / f.name)
        print(f"Fremlin extracted {topo}")
    clear_gitkeep_if_populated(fremlin_dir / "extracted")
    write_json(
        fremlin_dir / "SOURCE.json",
        {
            "schema": "sst-knot-library-source/1",
            "provider_id": "fremlin_fourier",
            "provider_name": "David Fremlin Fourier-Series Knots",
            "directory": "FourierSeries_Fremlin",
            "class": "original",
            "construction_objective": (
                "Elegant/symmetric 3D realization represented as coordinate lists and Fourier series."
            ),
            "origin_paths": ["Ideal_Fremlin_Fseries/fremlin"],
            "copied": True,
            "moved": False,
            "extracted_core_knots": CORE,
            "file_count_original": n,
        },
    )


def copy_knotplot_campaigns() -> None:
    kp_dir = KL / "Sources" / "KnotPlot_Scharein"
    campaigns = kp_dir / "SST_Relaxation_Campaigns"
    final_src = WB / "KnotPlot" / "knots" / "final"
    clear_gitkeep_if_populated(campaigns)
    gk = campaigns / ".gitkeep"
    if gk.exists():
        gk.unlink()
    copied = []
    for f in sorted(final_src.iterdir()):
        if f.is_file() and f.name != ".gitkeep":
            shutil.copy2(f, campaigns / f.name)
            copied.append(f.name)
    print(f"KnotPlot campaigns copied: {len(copied)}")
    write_json(
        kp_dir / "SOURCE.json",
        {
            "schema": "sst-knot-library-source/1",
            "provider_id": "knotplot",
            "provider_name": "Robert G. Scharein KnotPlot",
            "directory": "KnotPlot_Scharein",
            "class": "relaxed",
            "construction_objective": (
                "KnotPlot-authored geometry: database originals, seeds, exports, "
                "and SST relaxation campaigns (scientifically distinct classes)."
            ),
            "origin_paths": ["KnotPlot/knots/final"],
            "copied": True,
            "moved": False,
            "notes": (
                "SST_Relaxation_Campaigns holds KnotPlot×Ridgerunner polished finals "
                "— NOT KnotPlot Database_Original."
            ),
            "campaign_file_count": len(copied),
        },
    )
    write_json(
        campaigns / "CLASS.json",
        {
            "schema": "sst-knot-library-sample-class/1",
            "provider_id": "knotplot",
            "class": "relaxed",
            "directory_class": "SST_Relaxation_Campaigns",
            "note": (
                "Shared finals mirrored from KnotPlot/knots/final; "
                "alias.json documents Ridgerunner polish provenance."
            ),
        },
    )


def copy_ridgerunner(manifest_hashes: dict[str, str]) -> None:
    rr_dir = KL / "Sources" / "Ridgerunner_Cantarella_Rawdon"
    rr_orig = rr_dir / "original"
    ideal_src = WB / "Ideal_Sources"
    gk = rr_orig / ".gitkeep"
    if gk.exists():
        gk.unlink()
    rr_files = ["TwelveData.zip", "TwelveSummary.zip", "0TwelveData.csv"]
    rr_origin = []
    for name in rr_files:
        src = ideal_src / name
        if not src.exists():
            print(f"WARN missing {name}")
            continue
        h = copy_file(src, rr_orig / name)
        expected = manifest_hashes.get(name)
        if expected and h != expected:
            raise SystemExit(f"hash mismatch RR {name}")
        rr_origin.append(f"Ideal_Sources/{name}")
        print(f"RR copy OK {name}")
    write_json(
        rr_dir / "SOURCE.json",
        {
            "schema": "sst-knot-library-source/1",
            "provider_id": "ridgerunner",
            "provider_name": "Ridgerunner (Cantarella/Rawdon)",
            "directory": "Ridgerunner_Cantarella_Rawdon",
            "class": "original",
            "construction_objective": (
                "Constrained ropelength relaxation / near-ideal polylines "
                "(distinct from KnotPlot and Gilbert ideal Fourier)."
            ),
            "origin_paths": rr_origin,
            "copied": True,
            "moved": False,
            "notes": (
                "Twelve* archives are Klotz/Anderson 12-crossing polylines hosted via "
                "Knot Atlas Ideal knots page — not Gilbert Fourier."
            ),
        },
    )


def copy_katlas_snapshot() -> None:
    katlas_dir = KL / "Sources" / "KAtlas_BarNatan"
    snap_dir = katlas_dir / "snapshot"
    gk = snap_dir / ".gitkeep"
    if gk.exists():
        gk.unlink()
    pkg_data = (
        KL
        / "SST_Knot_Library"
        / "SST_Knot_Library_v0.2.0"
        / "sst_knotlib"
        / "data"
    )
    for name in ["katlas_snapshot_v1.json", "katlas_snapshot_v1.sha256"]:
        src = pkg_data / name
        if not src.exists():
            raise SystemExit(f"missing {src}; data dir={list(pkg_data.iterdir())}")
        shutil.copy2(src, snap_dir / name)
        print(f"KAtlas snapshot {name}")
    write_json(
        katlas_dir / "SOURCE.json",
        {
            "schema": "sst-knot-library-source/1",
            "provider_id": "katlas",
            "provider_name": "The Knot Atlas (Bar-Natan)",
            "directory": "KAtlas_BarNatan",
            "class": "snapshot",
            "construction_objective": (
                "Topology/reference source: presentations, braid seeds, offline snapshot "
                "— not SST 3D realizations."
            ),
            "origin_paths": [
                "Knot_Library/SST_Knot_Library/SST_Knot_Library_v0.2.0/sst_knotlib/data/katlas_snapshot_v1.json",
                "Katlas_Sources_v0.2.2_Outputs (not duplicated; inventory only)",
            ],
            "copied": True,
            "moved": False,
            "notes": (
                "Full Katlas RDF/page export tree is not duplicated here. "
                "Use inventory for Katlas_Sources_v0.2.2_Outputs."
            ),
        },
    )


def finalize_sst_generated() -> None:
    sst_dir = KL / "Sources" / "SST_Generated"
    write_json(
        sst_dir / "SOURCE.json",
        {
            "schema": "sst-knot-library-source/1",
            "provider_id": "sst_generated",
            "provider_name": "SST Generated Geometries",
            "directory": "SST_Generated",
            "class": "generated",
            "construction_objective": (
                "SST-authored analytic, braid-derived, shader-inspired, and other constructed "
                "embeddings (never mixed with upstream providers)."
            ),
            "origin_paths": [],
            "copied": False,
            "moved": False,
            "notes": (
                "KAtlasBraidDerived holds SST 3D realizations of KAtlas braids — "
                "distinct from KAtlas_BarNatan source data."
            ),
        },
    )


def main() -> None:
    scaffold()
    ideal_src = WB / "Ideal_Sources"
    manifest = json.loads((ideal_src / "MANIFEST.json").read_text(encoding="utf-8"))
    manifest_hashes = {a["path"]: a["sha256_container"] for a in manifest["artifacts"]}
    copy_gilbert(manifest_hashes)
    copy_fremlin()
    copy_knotplot_campaigns()
    copy_ridgerunner(manifest_hashes)
    copy_katlas_snapshot()
    finalize_sst_generated()
    print("ALL COPY/SCAFFOLD DONE")


if __name__ == "__main__":
    main()
