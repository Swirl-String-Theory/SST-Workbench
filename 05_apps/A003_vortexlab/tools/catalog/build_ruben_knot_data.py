#!/usr/bin/env python3
"""
Build ruben_knot_data.js from E010 Ruban Torus Dynamics Family XYZ seeds.

Source (default):
  01_research/.../E010_Ruban_Torus_Dynamics_Family_v0.3.5-outputs/
    seeds/T_p_q/T_p_q_B####_N512.xyz
    seeds_perturbed/T_p_q/T_p_q_B####_N512_eps01.xyz
    FAMILY_INDEX.json

Filename → catalog ID:
  T_2_3_B0800_N512.xyz        → RUBEN_T_2_3_B0800_N512
  T_2_3_B0800_N512_eps01.xyz  → RUBEN_T_2_3_B0800_N512_eps01

Scientific status: static/candidate geometry from Ruban 2018 / E010 parametric
torus embeddings. Not ideal/tight and not dynamics/survival certified.

JS filename keeps the user-facing spelling ruben_*; labels say Ruban (E010).
"""

from __future__ import annotations

from pathlib import Path
import argparse
import datetime as dt
import json
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_twist_knot_data import (  # noqa: E402
    component_length,
    dft_coefficients,
    geometry_metadata,
    linking_metadata,
    parse_xyz_components,
    sha256_file,
)

DB_MARKER = "const RUBEN_KNOT_DB = "
IDS_MARKER = "const RUBEN_KNOT_IDS = "

_STEM_RE = re.compile(
    r"^T_(?P<p>\d+)_(?P<q>\d+)_B(?P<b>\d{4})_N(?P<n>\d+)(?P<eps>_eps01)?$",
    flags=re.IGNORECASE,
)

DEFAULT_E010 = (
    ROOT.parents[3]
    / "01_research"
    / "E_pipelines"
    / "E010_pklsa_parametric_knot_link_seed_atlas"
    / "E010_Ruban_Torus_Dynamics_Family_v0.3.5-outputs"
)


def b0_from_token(token: str) -> float:
    """B0800 → 0.08, B1000 → 0.10, B2000 → 0.20."""
    raw = int(token)
    return raw / 10000.0


def parse_ruben_stem(stem: str) -> dict[str, Any]:
    match = _STEM_RE.fullmatch(stem)
    if not match:
        raise ValueError(
            f"{stem}: stem does not match T_p_q_B####_N####[_eps01]"
        )
    p = int(match.group("p"))
    q = int(match.group("q"))
    b_token = match.group("b")
    resolution_n = int(match.group("n"))
    perturbed = bool(match.group("eps"))
    embedding = f"T_{p}_{q}"
    seed_id = f"{embedding}_B{b_token}_N{resolution_n}"
    catalog_id = f"RUBEN_{seed_id}{'_eps01' if perturbed else ''}"
    return {
        "p": p,
        "q": q,
        "B0": b0_from_token(b_token),
        "bToken": b_token,
        "resolutionN": resolution_n,
        "parametricEmbedding": embedding,
        "variant": "perturbed" if perturbed else "baseline",
        "seedId": seed_id,
        "canonical_id": catalog_id,
        "kind": "KNOT",
    }


def load_family_index(path: Path | None) -> dict[str, dict]:
    """Map seed_id → FAMILY_INDEX seed record (baseline rows)."""
    if path is None or not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for seed in data.get("seeds") or []:
        if not isinstance(seed, dict):
            continue
        seed_id = str(seed.get("seed_id") or "")
        if seed_id:
            out[seed_id] = seed
    return out


def collect_xyz_inputs(root: Path) -> list[Path]:
    seeds = sorted((root / "seeds").glob("T_*/*.xyz"))
    perturbed = sorted((root / "seeds_perturbed").glob("T_*/*.xyz"))
    return [*seeds, *perturbed]


def build_entry(
    path: Path,
    *,
    max_harmonic: int | None,
    linking_subdivisions: int,
    family_by_seed: dict[str, dict] | None = None,
    outputs_root: Path | None = None,
) -> tuple[str, dict]:
    meta = parse_ruben_stem(path.stem)
    components = parse_xyz_components(path)
    if len(components) != 1:
        raise ValueError(
            f"{path.name}: expected 1 filament, got {len(components)}"
        )
    if len(components[0]) != int(meta["resolutionN"]):
        raise ValueError(
            f"{path.name}: point count {len(components[0])} != "
            f"N={meta['resolutionN']}"
        )

    geometry = geometry_metadata(components)
    component_rows = []
    reconstruction_max = 0.0
    reconstruction_rms = 0.0
    for index, points in enumerate(components, 1):
        coeffs, validation = dft_coefficients(points, max_harmonic)
        reconstruction_max = max(
            reconstruction_max, validation["maxNodeReconstructionError"]
        )
        reconstruction_rms = max(
            reconstruction_rms, validation["rmsNodeReconstructionError"]
        )
        component_rows.append({
            "I": index,
            "L": component_length(points),
            "pointCount": len(points),
            "harmonicMax": validation["harmonicMax"],
            "coeffs": coeffs,
        })

    family_row = (family_by_seed or {}).get(meta["seedId"]) or {}
    topology = family_row.get("topology_id")
    if topology is not None:
        topology = str(topology) if topology not in ("", "null") else None

    catalog_id = meta["canonical_id"]
    embedding = meta["parametricEmbedding"]
    variant = meta["variant"]
    resolution_n = int(meta["resolutionN"])
    b0 = float(meta["B0"])
    p, q = int(meta["p"]), int(meta["q"])

    rel_path = path.name
    if outputs_root is not None:
        try:
            rel_path = str(path.resolve().relative_to(outputs_root.resolve()))
        except ValueError:
            rel_path = path.name

    variant_label = "perturbed ε01" if variant == "perturbed" else "baseline"
    label = (
        f"{catalog_id} / Ruban (E010) {embedding} B0={b0:g} "
        f"N{resolution_n} {variant_label}"
    )
    if topology:
        label = f"{label} · topology {topology}"

    source_sha = None
    if family_row:
        if variant == "perturbed":
            source_sha = family_row.get("perturbed_sha256")
        else:
            source_sha = family_row.get("sha256")
    if not source_sha:
        source_sha = sha256_file(path)

    linking = linking_metadata(components, linking_subdivisions)
    entry = {
        "knotId": catalog_id,
        "label": label,
        "selectorLabel": f"{embedding} · B0={b0:g} · {variant_label}",
        "sourceFile": rel_path,
        "sourceSha256": source_sha,
        "source": (
            "E010 Ruban Torus Dynamics Family v0.3.5 polygonal XYZ "
            "(Ruban 2018 parametric embedding) converted to discrete Fourier series"
        ),
        "sourceFormat": "XYZ vertices; single closed filament; no blank separators",
        "sourceRole": f"e010-ruban-{variant}-N{resolution_n}",
        "generator": "build_ruben_knot_data.py",
        "ideal": False,
        "status": "static-candidate",
        "warning": (
            "Ruban/E010 research seed; INITIAL_GEOMETRY_ONLY. Not certified as "
            "global ideal/tight, ropelength-minimizing, or dynamics/survival result."
        ),
        "family": "ruban-torus",
        "kind": "KNOT",
        "topology": topology,
        "parametricEmbedding": embedding,
        "p": p,
        "q": q,
        "B0": b0,
        "R0": float(family_row.get("R0") or 1.0),
        "variant": variant,
        "resolutionN": resolution_n,
        "profile": None,
        "chirality": None,
        "cpMode": None,
        "D": None,
        "L": geometry["totalLength"],
        "componentCount": 1,
        "pointCount": int(sum(len(c) for c in components)),
        "pointsPerComponent": [len(c) for c in components],
        "normalization": {
            "label": f"native-N{resolution_n}",
            "method": "A006-style native bead count (Ruban R0=1 frame)",
            "note": (
                f"Polygonal centerline at native N={resolution_n}; "
                "coordinates remain in Ruban R0=1 dimensionless frame (D=null)."
            ),
        },
        "torus": {
            "class": "torus-knot",
            "p": p,
            "q": q,
            "notation": f"T({p},{q})",
            "parametricEmbedding": embedding,
            "B0": b0,
        },
        "pairwiseLinking": linking,
        "diagnostics": {
            "geometry": geometry,
            "fourier": {
                "maxNodeReconstructionError": reconstruction_max,
                "maxRmsNodeReconstructionError": reconstruction_rms,
                "fullSpectrum": max_harmonic is None,
            },
            "familyIndexStatus": family_row.get("status"),
            "sourceClass": family_row.get("source_class"),
        },
        "components": component_rows,
    }
    return catalog_id, entry


def write_javascript(path: Path, database: dict, compact: bool) -> None:
    ids = sorted(database)
    if compact:
        ids_json = json.dumps(ids, ensure_ascii=False, separators=(",", ":"))
        db_json = json.dumps(database, ensure_ascii=False, separators=(",", ":"))
    else:
        ids_json = json.dumps(ids, ensure_ascii=False, indent=2)
        db_json = json.dumps(database, ensure_ascii=False, indent=2)

    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()
    content = f"""// Generated by build_ruben_knot_data.py; do not hand-edit.
// E010 Ruban Torus Dynamics Family polygonal XYZ → discrete Fourier series.
// Source: E010_Ruban_Torus_Dynamics_Family_v0.3.5-outputs (seeds + seeds_perturbed).
// Native N=512; filters (embedding/B0/variant) select subsets.
// Static/candidate geometry; not ideal/tight or dynamics certified.
// Generated at: {generated_at}
const RUBEN_KNOT_IDS = {ids_json};
const RUBEN_KNOT_DB = {db_json};

if (typeof window !== "undefined") {{
  window.RUBEN_KNOT_IDS = RUBEN_KNOT_IDS;
  window.RUBEN_KNOT_DB = RUBEN_KNOT_DB;
}}
"""
    path.write_text(content, encoding="utf-8")


def entry_matches_filters(
    entry: dict,
    *,
    embedding: str = "ALL",
    b0: float | None = None,
    variant: str = "ALL",
) -> bool:
    if not entry:
        return False
    if embedding and embedding.upper() not in ("ALL", ""):
        if str(entry.get("parametricEmbedding") or "").upper() != embedding.upper():
            return False
    if b0 is not None:
        try:
            if abs(float(entry.get("B0")) - float(b0)) > 1e-12:
                return False
        except (TypeError, ValueError):
            return False
    if variant and variant.upper() not in ("ALL", ""):
        if str(entry.get("variant") or "").upper() != variant.upper():
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build ruben_knot_data.js from E010 Ruban XYZ seeds."
    )
    parser.add_argument(
        "--e010-root",
        type=Path,
        default=DEFAULT_E010,
        help="E010_Ruban_Torus_Dynamics_Family_v0.3.5-outputs directory",
    )
    parser.add_argument(
        "--family-index",
        type=Path,
        default=None,
        help="FAMILY_INDEX.json (default: <e010-root>/FAMILY_INDEX.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ruben_knot_data.js"),
        help="generated JS catalog",
    )
    parser.add_argument(
        "--max-harmonic",
        default="full",
        help="'full' for exact discrete interpolation, or an integer cutoff",
    )
    parser.add_argument(
        "--link-subdivisions",
        type=int,
        default=4,
        help="subdivisions per polygon segment for Gauss linking (unused for 1-comp)",
    )
    parser.add_argument(
        "--compact",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="compact JSON in JS output (default: off; pretty indent=2)",
    )
    parser.add_argument("--dry-run", action="store_true", help="validate without writing")
    args = parser.parse_args()

    root = args.e010_root
    if not root.is_dir():
        raise FileNotFoundError(f"E010 root not found: {root}")

    family_index_path = args.family_index or (root / "FAMILY_INDEX.json")
    family_by_seed = load_family_index(family_index_path)

    if str(args.max_harmonic).lower() == "full":
        max_harmonic = None
    else:
        max_harmonic = int(args.max_harmonic)
        if max_harmonic < 0:
            parser.error("--max-harmonic must be non-negative")

    inputs = collect_xyz_inputs(root)
    if not inputs:
        raise FileNotFoundError(f"no XYZ under {root}/seeds or seeds_perturbed")

    database: dict = {}
    for path in inputs:
        catalog_id, entry = build_entry(
            path,
            max_harmonic=max_harmonic,
            linking_subdivisions=args.link_subdivisions,
            family_by_seed=family_by_seed,
            outputs_root=root,
        )
        database[catalog_id] = entry
        print(
            f"added: {catalog_id} <- {path.name}; "
            f"N={entry['resolutionN']}; B0={entry['B0']}; "
            f"variant={entry['variant']}; L={entry['L']:.12g}"
        )

    if args.dry_run:
        print(f"dry run: would write {len(database)} entries to {args.output}")
        return 0

    write_javascript(args.output, database, args.compact)
    print(f"wrote {args.output} with {len(database)} entries")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
