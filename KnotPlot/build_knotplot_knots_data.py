#!/usr/bin/env python3
"""
Build or update knotplot_knots_data.js from KnotPlot plain-text XYZ exports.

Expected input format
---------------------
- One "x y z" vertex per line.
- Blank lines separate link components.
- Closed components are implicit: the last vertex connects to the first.

Recommended filename convention
-------------------------------
Tlink_<p>_<q>_<normalization>_<checkpoint>k.txt

Examples:
    Tlink_6_9_D1_040k.txt
    Tlink_3_3_D1_080k.txt
    Tlink_2_4_raw_020k.txt

Default behaviour
-----------------
- Uses a stable canonical catalog key such as "Tlink_6_9".
- A later checkpoint replaces an older checkpoint for the same canonical key.
- Converts each polygonal component to a discrete Fourier representation.
- Preserves all harmonics by default, including the Nyquist term.
- Computes geometry metadata and an approximate Gauss linking matrix.
- Merges/upserts into an existing generated JS file.

This is a candidate-geometry converter. It does not certify a global ideal or
ropelength-minimizing embedding.
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
    suffix = re.search(
        r"_(?P<normalization>D\d+(?:[p.]\d+)?|raw)_(?P<checkpoint>\d+)k$",
        stem,
        flags=re.IGNORECASE,
    )

    normalization = None
    checkpoint_steps = None
    base = stem

    if suffix:
        normalization = suffix.group("normalization")
        checkpoint_steps = int(suffix.group("checkpoint")) * 1000
        base = stem[: suffix.start()]

    torus = re.fullmatch(
        r"(?P<kind>Tlink|TorusLink|TorusKnot|T)_(?P<p>\d+)_(?P<q>\d+)",
        base,
        flags=re.IGNORECASE,
    )

    metadata = {
        "canonical_id": base,
        "normalization_label": normalization,
        "checkpoint_steps": checkpoint_steps,
        "torus": None,
    }

    if torus:
        p = int(torus.group("p"))
        q = int(torus.group("q"))
        d = math.gcd(p, q)
        canonical_id = f"Tlink_{p}_{q}" if d > 1 else f"Tknot_{p}_{q}"
        component_p = p // d
        component_q = q // d
        component_type = f"T({component_p},{component_q})"
        if {component_p, component_q} == {2, 3}:
            component_type += " / 3_1 trefoil"

        metadata["canonical_id"] = canonical_id
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
        raise ValueError(
            f"{path}: filename predicts {torus['componentCountExpected']} components, "
            f"but the file contains {len(components)}"
        )

    normalization_label = name_metadata["normalization_label"]
    checkpoint_steps = name_metadata["checkpoint_steps"]
    checkpoint_label = (
        f"{checkpoint_steps // 1000}k" if checkpoint_steps is not None else "unspecified"
    )

    if torus:
        label = (
            f"T({torus['p']},{torus['q']}) · KnotPlot "
            f"{checkpoint_label} · {normalization_label or 'unscaled'}"
        )
        family = "torus-link" if len(components) > 1 else "torus-knot"
    else:
        label = f"{catalog_id} · KnotPlot {checkpoint_label}"
        family = "knotplot-relaxed"

    d_value = name_metadata["D"]
    normalization = {
        "label": normalization_label,
        "D": d_value,
        "method": (
            f"KnotPlot fitto mindist {d_value:g}"
            if d_value is not None
            else "not encoded in filename"
        ),
        "note": (
            "KnotPlot mindist normalization; this metadata does not independently "
            "certify a canonical tube diameter or a global ropelength minimum."
        ),
    }

    linking = linking_metadata(components, linking_subdivisions)

    entry = {
        "knotId": catalog_id,
        "label": label,
        "sourceFile": path.name,
        "sourceSha256": sha256_file(path),
        "source": "KnotPlot plain-text centerline converted to discrete Fourier series",
        "sourceFormat": "XYZ vertices; blank lines separate closed components",
        "generator": "build_knotplot_knots_data.py",
        "ideal": False,
        "status": "relaxed-candidate",
        "warning": (
            "KnotPlot-relaxed candidate; not certified as a global ideal/tight "
            "or ropelength-minimizing embedding."
        ),
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build/update knotplot_knots_data.js from KnotPlot XYZ exports."
    )
    parser.add_argument("inputs", nargs="*", type=Path, help="KnotPlot .txt exports")
    parser.add_argument("--scan", type=Path, help="scan this directory")
    parser.add_argument(
        "--glob",
        default="*_D1_*k.txt",
        help="glob used with --scan (default: *_D1_*k.txt)",
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
        "--force",
        action="store_true",
        help="replace an existing canonical entry even with an older/unknown checkpoint",
    )
    parser.add_argument("--compact", action="store_true", help="compact JSON in JS output")
    parser.add_argument("--dry-run", action="store_true", help="validate without writing")

    args = parser.parse_args()
    inputs = collect_inputs(args.inputs, args.scan, args.glob)
    if not inputs:
        parser.error("provide input files or use --scan")
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

    database = read_existing_database(args.output)
    changed = 0

    for input_path in inputs:
        if not input_path.exists():
            raise FileNotFoundError(input_path)

        id_override = args.id_override
        if args.keep_checkpoints:
            id_override = input_path.stem

        catalog_id, entry = build_entry(
            input_path,
            max_harmonic=max_harmonic,
            linking_subdivisions=args.link_subdivisions,
            id_override=id_override,
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
