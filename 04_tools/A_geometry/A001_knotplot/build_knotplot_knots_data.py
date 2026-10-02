#!/usr/bin/env python3
"""
Build or update knotplot_knots_data.js from VortexLab-uniform XYZ exports
(and optional legacy KnotPlot plain-text XYZ).

Preferred pipeline
------------------
    run_build.cmd knot_3.1 -rr
    → *_polish_uniform_N300.txt
    → build_knotplot_knots_data.py --from-rr-outdir knots/knot_3.1

Canonical IDs are folder names: knot_3.1, torus_6.9, link_0.2.1.
Legacy Tlink_* catalog IDs are dropped (use torus_p.q).

Status comes from catalog_status.json when present
(relaxed-seed | stalled-not-converged | near-ideal-candidate |
 converged-local-candidate | near-ideal).
"""

from __future__ import annotations

from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json
import math
import re
import sys

import numpy as np


DB_MARKER = "const KNOTPLOT_KNOT_DB = "
IDS_MARKER = "const KNOTPLOT_KNOT_IDS = "


def parse_xyz_components(path: Path) -> list[np.ndarray]:
    """Read components separated by blank lines."""
    components: list[np.ndarray] = []
    current: list[list[float]] = []

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            if current:
                components.append(np.asarray(current, dtype=float))
                current = []
            continue

        fields = stripped.replace(",", " ").split()
        if len(fields) < 3:
            # Ignore harmless non-coordinate lines, but reject ambiguous numeric data.
            continue
        try:
            xyz = [float(fields[0]), float(fields[1]), float(fields[2])]
        except ValueError:
            continue
        if not all(math.isfinite(v) for v in xyz):
            raise ValueError(f"{path}:{line_number}: non-finite coordinate")
        current.append(xyz)

    if current:
        components.append(np.asarray(current, dtype=float))

    if not components:
        raise ValueError(f"{path}: no XYZ components found")
    for index, component in enumerate(components, 1):
        if len(component) < 4:
            raise ValueError(f"{path}: component {index} has fewer than four vertices")
    return components


def parse_source_name(path: Path) -> dict:
    stem = path.stem
    # Strip RR / uniform suffixes for id guessing
    base_stem = re.sub(
        r"_rr_.*$",
        "",
        stem,
        flags=re.IGNORECASE,
    )
    base_stem = re.sub(
        r"_uniform_N\d+.*$",
        "",
        base_stem,
        flags=re.IGNORECASE,
    )
    base_stem = re.sub(
        r"_trial_\d+k$",
        "",
        base_stem,
        flags=re.IGNORECASE,
    )
    base_stem = re.sub(
        r"_analytic_D\d+$",
        "",
        base_stem,
        flags=re.IGNORECASE,
    )

    suffix = re.search(
        r"_(?P<normalization>D\d+(?:[p.]\d+)?|raw)_(?P<checkpoint>\d+)k$",
        stem,
        flags=re.IGNORECASE,
    )

    normalization = None
    checkpoint_steps = None
    base = base_stem

    if suffix:
        normalization = suffix.group("normalization")
        checkpoint_steps = int(suffix.group("checkpoint")) * 1000
        base = stem[: suffix.start()]

    # Prefer parent folder name for knot_/torus_/link_ pipelines
    parent = path.parent.name
    folder_id = None
    for prefix in ("knot_", "torus_", "link_"):
        if parent.lower().startswith(prefix):
            folder_id = parent
            break
        if base.lower().startswith(prefix):
            # e.g. knot_3.1_... already stripped to knot_3.1
            m = re.match(
                rf"({prefix}[\d.]+(?:\.[\d.]+)*)",
                base,
                flags=re.IGNORECASE,
            )
            if m:
                folder_id = m.group(1)
            else:
                folder_id = base
            break

    metadata = {
        "canonical_id": folder_id or base,
        "normalization_label": normalization,
        "checkpoint_steps": checkpoint_steps,
        "torus": None,
        "family_hint": None,
    }

    # torus_6.9 / torus_2.3 folder → torus metadata (never remap to Tlink_*)
    tm = re.fullmatch(
        r"torus_(?P<p>\d+)[._](?P<q>\d+)",
        (folder_id or base),
        flags=re.IGNORECASE,
    )
    if tm:
        p = int(tm.group("p"))
        q = int(tm.group("q"))
        d = math.gcd(p, q)
        metadata["canonical_id"] = f"torus_{p}.{q}"
        metadata["family_hint"] = "torus-knot" if d == 1 else "torus-link"
        metadata["torus"] = {
            "p": p,
            "q": q,
            "componentCountExpected": d,
            "componentType": f"T({p // d},{q // d})" if d > 1 else f"T({p},{q})",
            "expectedPairwiseLinkingAbs": (p * q) // (d * d) if d > 1 else 0,
        }
        metadata["D"] = None
        return metadata

    if folder_id and folder_id.lower().startswith("knot_"):
        metadata["canonical_id"] = folder_id
        metadata["family_hint"] = "classic-knot"
        metadata["D"] = None
        return metadata

    if folder_id and folder_id.lower().startswith("link_"):
        metadata["canonical_id"] = folder_id
        metadata["family_hint"] = "link"
        metadata["D"] = None
        return metadata
    # Legacy Tlink_p_q filenames only (not used for new torus_* pipeline)
    torus = re.fullmatch(
        r"(?P<kind>Tlink|TorusLink|TorusKnot|T)_(?P<p>\d+)_(?P<q>\d+)",
        base,
        flags=re.IGNORECASE,
    )
    if torus:
        p = int(torus.group("p"))
        q = int(torus.group("q"))
        d = math.gcd(p, q)
        # Prefer torus_p.q naming; do not emit Tlink_* as catalog id
        metadata["canonical_id"] = f"torus_{p}.{q}"
        component_p = p // d
        component_q = q // d
        component_type = f"T({component_p},{component_q})"
        if {component_p, component_q} == {2, 3}:
            component_type += " / 3_1 trefoil"
        metadata["family_hint"] = "torus-link" if d > 1 else "torus-knot"
        metadata["torus"] = {
            "p": p,
            "q": q,
            "componentCountExpected": d,
            "componentType": component_type,
            "expectedPairwiseLinkingAbs": (p * q) // (d * d) if d > 1 else 0,
        }

    d_value = None
    if normalization and normalization.lower().startswith("d"):
        raw = normalization[1:].replace("p", ".")
        try:
            d_value = float(raw)
        except ValueError:
            d_value = None
    metadata["D"] = d_value
    return metadata


def closed_edges(points: np.ndarray) -> np.ndarray:
    return np.roll(points, -1, axis=0) - points


def component_length(points: np.ndarray) -> float:
    return float(np.linalg.norm(closed_edges(points), axis=1).sum())


def dft_coefficients(points: np.ndarray, max_harmonic: int | None) -> tuple[list[dict], dict]:
    """
    Convert periodic samples to:
        r(t) = sum_I A_I cos(I t) + B_I sin(I t)

    With full harmonics, reconstruction at the original bead parameters is
    exact to floating-point precision.
    """
    n = len(points)
    spectrum = np.fft.rfft(points, axis=0)
    full_max = n // 2
    hmax = full_max if max_harmonic is None else min(max_harmonic, full_max)

    coeffs: list[dict] = []
    for harmonic in range(hmax + 1):
        if harmonic == 0:
            a = spectrum[harmonic].real / n
            b = np.zeros(3)
        elif n % 2 == 0 and harmonic == n // 2:
            a = spectrum[harmonic].real / n
            b = np.zeros(3)
        else:
            a = 2.0 * spectrum[harmonic].real / n
            b = -2.0 * spectrum[harmonic].imag / n

        a[np.abs(a) < 5e-16] = 0.0
        b[np.abs(b) < 5e-16] = 0.0
        coeffs.append({
            "I": harmonic,
            "A": [float(v) for v in a],
            "B": [float(v) for v in b],
        })

    # Validate the representation at the original periodic sample parameters.
    t = 2.0 * np.pi * np.arange(n) / n
    reconstructed = np.zeros_like(points)
    for row in coeffs:
        harmonic = row["I"]
        reconstructed += (
            np.cos(harmonic * t)[:, None] * np.asarray(row["A"])[None, :]
            + np.sin(harmonic * t)[:, None] * np.asarray(row["B"])[None, :]
        )
    error = np.linalg.norm(reconstructed - points, axis=1)

    return coeffs, {
        "harmonicMax": hmax,
        "fullHarmonicMax": full_max,
        "maxNodeReconstructionError": float(error.max()),
        "rmsNodeReconstructionError": float(np.sqrt(np.mean(error * error))),
    }


def subdivide_polygon(points: np.ndarray, factor: int) -> np.ndarray:
    if factor <= 1:
        return points.copy()
    nxt = np.roll(points, -1, axis=0)
    chunks = [
        points + (k / factor) * (nxt - points)
        for k in range(factor)
    ]
    # Interleave subdivision points segment-by-segment.
    return np.stack(chunks, axis=1).reshape(-1, 3)


def gauss_linking_midpoint(
    a: np.ndarray,
    b: np.ndarray,
    subdivisions: int = 4,
    batch_size: int = 192,
) -> float:
    """
    Numerically approximate the Gauss linking integral.

    Polygon segments are subdivided before midpoint quadrature. The rounded
    integer is the useful invariant; the residual is retained as a diagnostic.
    """
    aa = subdivide_polygon(a, subdivisions)
    bb = subdivide_polygon(b, subdivisions)

    da = closed_edges(aa)
    db = closed_edges(bb)
    ma = 0.5 * (aa + np.roll(aa, -1, axis=0))
    mb = 0.5 * (bb + np.roll(bb, -1, axis=0))

    total = 0.0
    for start in range(0, len(aa), batch_size):
        ma_batch = ma[start : start + batch_size]
        da_batch = da[start : start + batch_size]
        difference = ma_batch[:, None, :] - mb[None, :, :]
        cross = np.cross(da_batch[:, None, :], db[None, :, :])
        radius = np.linalg.norm(difference, axis=2)
        denominator = np.maximum(radius, 1e-15) ** 3
        numerator = np.einsum("ijk,ijk->ij", cross, difference)
        total += float(np.sum(numerator / denominator))

    return total / (4.0 * np.pi)


def linking_metadata(components: list[np.ndarray], subdivisions: int) -> dict:
    count = len(components)
    approximate = [[0.0 for _ in range(count)] for _ in range(count)]
    rounded = [[0 for _ in range(count)] for _ in range(count)]
    residual = 0.0

    for i in range(count):
        for j in range(i + 1, count):
            value = gauss_linking_midpoint(
                components[i],
                components[j],
                subdivisions=subdivisions,
            )
            integer = int(round(value))
            approximate[i][j] = approximate[j][i] = value
            rounded[i][j] = rounded[j][i] = integer
            residual = max(residual, abs(value - integer))

    return {
        "method": f"Gauss midpoint quadrature; {subdivisions} subdivisions/segment",
        "approximateMatrix": approximate,
        "roundedMatrix": rounded,
        "maxIntegerResidual": residual,
    }


def geometry_metadata(components: list[np.ndarray]) -> dict:
    component_lengths = [component_length(c) for c in components]
    all_points = np.concatenate(components, axis=0)
    edge_lengths = np.concatenate(
        [np.linalg.norm(closed_edges(c), axis=1) for c in components]
    )

    minimum = all_points.min(axis=0)
    maximum = all_points.max(axis=0)
    mean_edge = float(edge_lengths.mean())

    return {
        "componentLengths": component_lengths,
        "totalLength": float(sum(component_lengths)),
        "edgeLength": {
            "min": float(edge_lengths.min()),
            "max": float(edge_lengths.max()),
            "mean": mean_edge,
            "maxMinRatio": float(edge_lengths.max() / edge_lengths.min()),
            "coefficientOfVariation": float(edge_lengths.std() / mean_edge),
        },
        "boundingBox": {
            "min": [float(v) for v in minimum],
            "max": [float(v) for v in maximum],
            "extent": [float(v) for v in maximum - minimum],
        },
        "centroid": [float(v) for v in all_points.mean(axis=0)],
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_entry(
    path: Path,
    *,
    max_harmonic: int | None,
    linking_subdivisions: int,
    id_override: str | None = None,
    status: str = "relaxed-seed",
    catalog_status: dict | None = None,
    polish_audit: str | None = None,
) -> tuple[str, dict]:
    components = parse_xyz_components(path)
    name_metadata = parse_source_name(path)
    catalog_id = id_override or name_metadata["canonical_id"]
    geometry = geometry_metadata(components)

    component_rows = []
    reconstruction_max = 0.0
    reconstruction_rms = 0.0
    for index, points in enumerate(components, 1):
        coeffs, validation = dft_coefficients(points, max_harmonic)
        reconstruction_max = max(
            reconstruction_max,
            validation["maxNodeReconstructionError"],
        )
        reconstruction_rms = max(
            reconstruction_rms,
            validation["rmsNodeReconstructionError"],
        )
        component_rows.append({
            "I": index,
            "L": component_length(points),
            "pointCount": len(points),
            "harmonicMax": validation["harmonicMax"],
            "coeffs": coeffs,
        })

    torus = name_metadata["torus"]
    if torus and torus["componentCountExpected"] != len(components):
        # Soft: VortexLab uniform may still be valid if KnotPlot bead rule differs
        if torus["componentCountExpected"] > 1 and len(components) == 1:
            pass  # single-comp torus knot OK
        elif len(components) != torus["componentCountExpected"]:
            raise ValueError(
                f"{path}: filename predicts {torus['componentCountExpected']} "
                f"components, but the file contains {len(components)}"
            )

    normalization_label = name_metadata["normalization_label"]
    checkpoint_steps = name_metadata["checkpoint_steps"]
    checkpoint_label = (
        f"{checkpoint_steps // 1000}k" if checkpoint_steps is not None else "unspecified"
    )

    family = name_metadata.get("family_hint") or "knotplot-relaxed"
    if torus:
        label = (
            f"T({torus['p']},{torus['q']}) / {catalog_id} / "
            f"{checkpoint_label} / {normalization_label or 'RR/VortexLab'}"
        )
        if not name_metadata.get("family_hint"):
            family = "torus-link" if len(components) > 1 else "torus-knot"
    else:
        label = f"{catalog_id} / VortexLab uniform N300"

    status_val = status
    warning = (
        "Not certified as a global ideal/tight or ropelength-minimizing embedding."
    )
    ideal = False
    extra_diag: dict = {}
    if catalog_status:
        status_val = catalog_status.get("status", status_val)
        ideal = bool(catalog_status.get("ideal", False))
        # Never promote to certified-ideal automatically
        if status_val == "certified-ideal":
            status_val = "near-ideal"
            ideal = False
        reasons = catalog_status.get("reason") or []
        if reasons:
            warning = "; ".join(reasons[:6])
        extra_diag["catalogStatus"] = {
            "strict_near_ideal": catalog_status.get("strict_near_ideal"),
            "epsilon_R": catalog_status.get("epsilon_R"),
            "reference": catalog_status.get("reference"),
            "campaign_reference": catalog_status.get("campaign_reference"),
            "checks": catalog_status.get("checks"),
            "chirality": catalog_status.get("chirality"),
            "catalog_aliases": catalog_status.get("catalog_aliases"),
            "dowker_code": catalog_status.get("dowker_code"),
            "equivalent_group": catalog_status.get("equivalent_group"),
        }

    d_value = name_metadata.get("D")
    if d_value is None:
        d_value = 1.0
    normalization = {
        "label": normalization_label or "uniform-N300",
        "D": d_value,
        "method": "ridgerunner polish + arc-length uniform resample N=300",
        "note": (
            "VortexLab discrete centerline; Ridgerunner polish remains the audit "
            "geometry. Do not re-run Ridgerunner on this uniform file."
        ),
    }

    linking = linking_metadata(components, linking_subdivisions)

    entry = {
        "knotId": catalog_id,
        "label": label,
        "sourceFile": path.name,
        "sourceSha256": sha256_file(path),
        "source": (
            "Ridgerunner polish → uniform arc-length XYZ converted to "
            "discrete Fourier series"
        ),
        "sourceFormat": "XYZ vertices; blank lines separate closed components",
        "sourceRole": "vortexlab-uniform-N300",
        "polishAudit": polish_audit,
        "generator": "build_knotplot_knots_data.py",
        "ideal": ideal,
        "status": status_val,
        "warning": warning,
        "family": family,
        "checkpointSteps": checkpoint_steps,
        "normalization": normalization,
        "D": d_value,
        "L": geometry["totalLength"],
        "componentCount": len(components),
        "pointCount": int(sum(len(c) for c in components)),
        "pointsPerComponent": [int(len(c)) for c in components],
        "torus": torus,
        "pairwiseLinking": linking,
        "diagnostics": {
            **geometry,
            "fourier": {
                "maxNodeReconstructionError": reconstruction_max,
                "maxRmsNodeReconstructionError": reconstruction_rms,
                "fullSpectrum": max_harmonic is None,
            },
            **extra_diag,
        },
        "components": component_rows,
    }
    return catalog_id, entry


def read_existing_database(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    marker_index = text.find(DB_MARKER)
    if marker_index < 0:
        raise ValueError(
            f"{path}: existing file does not contain a generated "
            "KNOTPLOT_KNOT_DB declaration"
        )
    json_start = marker_index + len(DB_MARKER)
    decoder = json.JSONDecoder()
    database, _ = decoder.raw_decode(text[json_start:].lstrip())
    if not isinstance(database, dict):
        raise ValueError(f"{path}: KNOTPLOT_KNOT_DB is not an object")
    return database


def write_javascript(path: Path, database: dict, compact: bool) -> None:
    ids = sorted(database)
    if compact:
        ids_json = json.dumps(ids, ensure_ascii=False, separators=(",", ":"))
        db_json = json.dumps(database, ensure_ascii=False, separators=(",", ":"))
    else:
        ids_json = json.dumps(ids, ensure_ascii=False, indent=2)
        db_json = json.dumps(database, ensure_ascii=False, indent=2)

    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()
    content = f"""// Generated by build_knotplot_knots_data.py; do not hand-edit.
// KnotPlot relaxed/tight candidates converted from polygonal XYZ centerlines.
// Generated at: {generated_at}
const KNOTPLOT_KNOT_IDS = {ids_json};
const KNOTPLOT_KNOT_DB = {db_json};

if (typeof window !== "undefined") {{
  window.KNOTPLOT_KNOT_IDS = KNOTPLOT_KNOT_IDS;
  window.KNOTPLOT_KNOT_DB = KNOTPLOT_KNOT_DB;
}}
"""
    path.write_text(content, encoding="utf-8")


def collect_inputs(positional: list[Path], scan: Path | None, glob_pattern: str) -> list[Path]:
    candidates = list(positional)
    if scan is not None:
        candidates.extend(sorted(scan.glob(glob_pattern)))

    unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(candidate)
    return unique


def resolve_rr_outdir_inputs(outdir: Path) -> tuple[Path, dict | None, str | None]:
    """Return (uniform TXT, catalog_status, polish_audit_path)."""
    outdir = outdir.resolve()
    uniforms = sorted(outdir.glob("*_polish_uniform_N*.txt"))
    if not uniforms:
        uniforms = sorted(outdir.glob("*_uniform_N*.txt"))
    if not uniforms:
        raise FileNotFoundError(
            f"{outdir}: no *_polish_uniform_N*.txt (run three-stage + resample first)"
        )
    # Prefer uniform matching seed_selection / newest polish
    status = None
    status_path = outdir / "catalog_status.json"
    if status_path.is_file():
        status = json.loads(status_path.read_text(encoding="utf-8"))
    primary = None
    if status and status.get("primary_polish"):
        pp = Path(status["primary_polish"]).name
        if pp.endswith(".metrics.json"):
            polish_base = pp[: -len(".metrics.json")]
        elif pp.endswith(".txt"):
            polish_base = pp[: -len(".txt")]
        else:
            polish_base = Path(status["primary_polish"]).stem.replace(".metrics", "")
        # Match any uniform sibling of this polish stem
        for u in uniforms:
            if u.name.startswith(polish_base + "_uniform_N") or (
                polish_base and polish_base in u.stem
            ):
                primary = u
                break
    if primary is None:
        # Prefer selected seed stem
        sel_path = outdir / "seed_selection.json"
        if sel_path.is_file():
            sel = json.loads(sel_path.read_text(encoding="utf-8"))
            selected = sel.get("selected")
            if selected:
                stem = Path(selected).stem
                for u in uniforms:
                    if stem in u.name:
                        primary = u
                        break
    if primary is None:
        primary = uniforms[-1]

    polish_audit = None
    # Sibling polish without uniform: ..._polish_uniform_N300.txt → ..._polish.txt
    name = primary.name
    marker = "_uniform_N"
    if marker in name:
        polish_name = name[: name.index(marker)] + ".txt"
        audit = primary.with_name(polish_name)
        if audit.is_file():
            polish_audit = str(audit)
    # Prefer explicit final snapshot as audit pointer when present
    if status and status.get("final_snapshot"):
        fin = Path(status["final_snapshot"])
        if fin.is_file():
            polish_audit = str(fin)
    return primary, status, polish_audit


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build/update knotplot_knots_data.js from KnotPlot/VortexLab XYZ exports."
    )
    parser.add_argument("inputs", nargs="*", type=Path, help="KnotPlot .txt exports")
    parser.add_argument("--scan", type=Path, help="scan this directory")
    parser.add_argument(
        "--glob",
        default="*_polish_uniform_N300.txt",
        help="glob used with --scan (default: *_polish_uniform_N300.txt)",
    )
    parser.add_argument(
        "--from-rr-outdir",
        type=Path,
        default=None,
        help="knots/<id> folder: pick *_polish_uniform_N300.txt + catalog_status.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("knotplot_knots_data.js"),
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
        help="subdivisions per polygon segment for Gauss linking quadrature",
    )
    parser.add_argument(
        "--keep-checkpoints",
        action="store_true",
        help="use the complete filename stem as catalog ID instead of updating a canonical ID",
    )
    parser.add_argument(
        "--id",
        dest="id_override",
        help="catalog ID override; valid only with one input",
    )
    parser.add_argument(
        "--status",
        default=None,
        help="override status (relaxed-seed|stalled-not-converged|near-ideal-candidate|converged-local-candidate|near-ideal)",
    )
    parser.add_argument(
        "--catalog-status-json",
        type=Path,
        default=None,
        help="optional catalog_status.json (else read from --from-rr-outdir)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing canonical entry even with an older/unknown checkpoint",
    )
    parser.add_argument(
        "--drop-ids",
        default="Tlink_6_9,Tknot_6_9",
        help="comma-separated catalog IDs to remove from the DB (default drops legacy Tlink_6_9)",
    )
    parser.add_argument("--compact", action="store_true", help="compact JSON in JS output")
    parser.add_argument("--dry-run", action="store_true", help="validate without writing")

    args = parser.parse_args()
    inputs = collect_inputs(args.inputs, args.scan, args.glob)
    catalog_status = None
    polish_audit = None
    if args.from_rr_outdir is not None:
        uni, catalog_status, polish_audit = resolve_rr_outdir_inputs(args.from_rr_outdir)
        inputs = [uni] + inputs
    if args.catalog_status_json is not None:
        catalog_status = json.loads(
            args.catalog_status_json.read_text(encoding="utf-8")
        )
    if not inputs and not args.drop_ids:
        parser.error("provide input files, --scan, or --from-rr-outdir")
    if args.id_override and len(inputs) != 1:
        parser.error("--id is valid only with exactly one input")
    if args.link_subdivisions < 1:
        parser.error("--link-subdivisions must be at least 1")

    if str(args.max_harmonic).lower() == "full":
        max_harmonic = None
    else:
        try:
            max_harmonic = int(args.max_harmonic)
        except ValueError:
            parser.error("--max-harmonic must be 'full' or a non-negative integer")
        if max_harmonic < 0:
            parser.error("--max-harmonic must be non-negative")

    database = read_existing_database(args.output) if args.output.exists() else {}
    # Always drop legacy bad IDs
    for bad in [x.strip() for x in (args.drop_ids or "").split(",") if x.strip()]:
        if bad in database:
            del database[bad]
            print(f"removed legacy catalog id: {bad}")

    changed = 0
    default_status = args.status or "relaxed-seed"

    for input_path in inputs:
        if not input_path.exists():
            raise FileNotFoundError(input_path)

        id_override = args.id_override
        if args.keep_checkpoints:
            id_override = input_path.stem
        # Prefer folder name when from-rr-outdir
        if args.from_rr_outdir is not None and id_override is None:
            id_override = args.from_rr_outdir.resolve().name

        status = default_status
        if catalog_status and catalog_status.get("status"):
            status = catalog_status["status"]

        catalog_id, entry = build_entry(
            input_path,
            max_harmonic=max_harmonic,
            linking_subdivisions=args.link_subdivisions,
            id_override=id_override,
            status=status,
            catalog_status=catalog_status,
            polish_audit=polish_audit,
        )

        existing = database.get(catalog_id)
        old_steps = existing.get("checkpointSteps") if isinstance(existing, dict) else None
        new_steps = entry.get("checkpointSteps")

        should_replace = (
            existing is None
            or args.force
            or old_steps is None
            or (new_steps is not None and new_steps >= old_steps)
        )

        if should_replace:
            database[catalog_id] = entry
            changed += 1
            action = "added" if existing is None else "updated"
        else:
            action = "skipped older checkpoint"

        link_matrix = entry["pairwiseLinking"]["roundedMatrix"]
        print(
            f"{action}: {catalog_id} <- {input_path.name}; "
            f"status={entry['status']}; "
            f"{entry['componentCount']} components; "
            f"L={entry['L']:.12g}; linking={link_matrix}"
        )

    if args.dry_run:
        print(f"dry run: {changed} catalog entries would change")
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
