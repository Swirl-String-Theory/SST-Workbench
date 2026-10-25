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


# Legacy geometry-export stems (superseded by Output/Seeds for VortexLab merge).
_A006_KNOT_RE = re.compile(
    r"^(?P<kind>KNOT)_(?P<topology>.+)_N(?P<n>\d+)_(?P<chirality>ORIG|MIRROR)$",
    flags=re.IGNORECASE,
)
_A006_LINK_RE = re.compile(
    r"^(?P<kind>LINK)_(?P<topology>.+)_"
    r"(?P<profile>FLAT|SOFT|BALANCED|TIGHT)_"
    r"N(?P<n>\d+)_(?P<chirality>ORIG|MIRROR)_"
    r"(?P<cp>CPFIXED61|CPCENTER)$",
    flags=re.IGNORECASE,
)
# Canonical A006 seed stems: 3_1_N1024, 11a367_N2048, …
_A006_SEED_RE = re.compile(
    r"^(?P<topology>\d+_\d+|\d+[a-z]+\d+)_N(?P<n>\d+)$",
    flags=re.IGNORECASE,
)
# Stage borromean whole exports: Borromean_6_6_5_SOFT_MIN2048_S0800_v042d
_A006_BORROMEAN_RE = re.compile(
    r"^Borromean_(?P<topology>\d+_\d+_\d+)_(?P<profile>FLAT|SOFT|BALANCED|TIGHT)_"
    r"MIN(?P<n>\d+)(?:_S(?P<steps>\d+))?(?:_v(?P<ver>\w+))?$",
    flags=re.IGNORECASE,
)
# Short reference rings: borromean_flat.txt / borromean_balanced.txt
_A006_BORROMEAN_REF_RE = re.compile(
    r"^borromean_(?P<profile>flat|soft|balanced|tight)$",
    flags=re.IGNORECASE,
)


def parse_source_name(path: Path) -> dict:
    stem = path.stem

    a006_borromean = _A006_BORROMEAN_RE.fullmatch(stem)
    a006_borromean_ref = _A006_BORROMEAN_REF_RE.fullmatch(stem)
    a006_seed = _A006_SEED_RE.fullmatch(stem)
    a006_knot = _A006_KNOT_RE.fullmatch(stem)
    a006_link = _A006_LINK_RE.fullmatch(stem)
    if a006_borromean or a006_borromean_ref or a006_seed or a006_knot or a006_link:
        if a006_borromean:
            match = a006_borromean
            resolution_n = int(match.group("n"))
            topology = match.group("topology")
            profile = match.group("profile").upper()
            canonical_id = f"Borromean_{topology}_{profile}_MIN{resolution_n}"
            a006 = {
                "kind": "LINK",
                "topology": topology,
                "profile": profile,
                "resolutionN": resolution_n,
                "chirality": None,
                "cpMode": None,
                "seed": False,
                "borromean": True,
                "reference": False,
            }
        elif a006_borromean_ref:
            match = a006_borromean_ref
            profile = match.group("profile").upper()
            resolution_n = 0  # native short reference; filled from point count later
            canonical_id = f"Borromean_ref_{profile.lower()}"
            a006 = {
                "kind": "LINK",
                "topology": "6^3_2",
                "profile": profile,
                "resolutionN": resolution_n,
                "chirality": None,
                "cpMode": None,
                "seed": False,
                "borromean": True,
                "reference": True,
            }
        elif a006_seed:
            match = a006_seed
            resolution_n = int(match.group("n"))
            canonical_id = stem
            a006 = {
                "kind": "KNOT",
                "topology": match.group("topology"),
                "profile": None,
                "resolutionN": resolution_n,
                "chirality": None,
                "cpMode": None,
                "seed": True,
                "borromean": False,
                "reference": False,
            }
        else:
            match = a006_knot or a006_link
            resolution_n = int(match.group("n"))
            canonical_id = stem
            a006 = {
                "kind": match.group("kind").upper(),
                "topology": match.group("topology"),
                "profile": (
                    match.group("profile").upper()
                    if a006_link
                    else None
                ),
                "resolutionN": resolution_n,
                "chirality": match.group("chirality").upper(),
                "cpMode": match.group("cp").upper() if a006_link else None,
                "seed": False,
                "borromean": False,
                "reference": False,
            }
        return {
            "canonical_id": canonical_id,
            "normalization_label": (
                f"native-N{resolution_n}" if resolution_n else "native-reference"
            ),
            "checkpoint_steps": resolution_n if resolution_n else None,
            "torus": None,
            "D": None,
            "a006": a006,
        }

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
        "a006": None,
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

    a006 = name_metadata.get("a006")
    d_value = name_metadata["D"]

    if a006:
        is_seed = bool(a006.get("seed"))
        is_borromean = bool(a006.get("borromean"))
        is_reference = bool(a006.get("reference"))
        resolution_n = a006["resolutionN"]
        if resolution_n <= 0:
            # Short reference rings: use min component length as native N.
            resolution_n = int(min(len(c) for c in components))
            a006["resolutionN"] = resolution_n

        if is_borromean:
            ref_tag = "reference" if is_reference else "stage"
            label = (
                f"Borromean {a006['topology']} · {a006['profile']} · "
                f"A006 {ref_tag} MIN{resolution_n}"
            )
            family = "a006-borromean"
            source = (
                "A006 RoundFolded Borromean polygonal XYZ converted to "
                "discrete Fourier series"
                + (" (extensions/borromean references)" if is_reference
                   else " (stage output/borromean)")
            )
            source_role = (
                f"a006-borromean-ref-N{resolution_n}"
                if is_reference
                else f"a006-borromean-N{resolution_n}"
            )
            note_extra = (
                " Source: A006 borromean reference TXT."
                if is_reference
                else " Source: A006-v0.5.0 stage output/borromean XYZ."
            )
        elif is_seed:
            label = f"{a006['topology']} / A006 seed N{resolution_n}"
            family = "a006-twist"
            source = (
                "A006 RoundFolded Twist Knot Family polygonal XYZ converted to "
                "discrete Fourier series (Output/Seeds)"
            )
            source_role = f"a006-seed-N{resolution_n}"
            note_extra = " Source: A006-v0.5.0/Output/Seeds."
        else:
            label = f"{a006['topology']} / A006 geometry-export N{resolution_n}"
            family = "a006-twist"
            source = (
                "A006 RoundFolded Twist Knot Family polygonal XYZ converted to "
                "discrete Fourier series (Output/v050/geometry)"
            )
            source_role = f"a006-native-N{resolution_n}"
            note_extra = ""

        status = "static-candidate"
        warning = (
            "A006 static/candidate geometry; not certified as a global ideal/tight "
            "or ropelength-minimizing embedding."
        )
        normalization = {
            "label": normalization_label or f"native-N{resolution_n}",
            "D": None,
            "method": (
                f"A006 polygonal centerline at native bead count N≈{resolution_n}; "
                "no VortexLab uniform resample and no D=1 diameter certification"
            ),
            "note": (
                "Merged into the KnotPlot catalog for VortexLab selection. "
                "Coordinates remain in the A006 source frame."
                + note_extra
            ),
        }
        extra_fields = {
            "sourceRole": source_role,
            "kind": a006["kind"],
            "topology": a006["topology"],
            "profile": a006["profile"],
            "resolutionN": resolution_n,
            "chirality": a006["chirality"],
            "cpMode": a006["cpMode"],
        }
    elif torus:
        label = (
            f"T({torus['p']},{torus['q']}) · KnotPlot "
            f"{checkpoint_label} · {normalization_label or 'unscaled'}"
        )
        family = "torus-link" if len(components) > 1 else "torus-knot"
        source = "KnotPlot plain-text centerline converted to discrete Fourier series"
        status = "relaxed-candidate"
        warning = (
            "KnotPlot-relaxed candidate; not certified as a global ideal/tight "
            "or ropelength-minimizing embedding."
        )
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
        extra_fields = {}
    else:
        label = f"{catalog_id} · KnotPlot {checkpoint_label}"
        family = "knotplot-relaxed"
        source = "KnotPlot plain-text centerline converted to discrete Fourier series"
        status = "relaxed-candidate"
        warning = (
            "KnotPlot-relaxed candidate; not certified as a global ideal/tight "
            "or ropelength-minimizing embedding."
        )
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
        extra_fields = {}

    linking = linking_metadata(components, linking_subdivisions)

    entry = {
        "knotId": catalog_id,
        "label": label,
        "sourceFile": path.name,
        "sourceSha256": sha256_file(path),
        "source": source,
        "sourceFormat": "XYZ vertices; blank lines separate closed components",
        "generator": "build_knotplot_knots_data.py",
        "ideal": False,
        "status": status,
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
        },
        "components": component_rows,
        **extra_fields,
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


def _is_a006_entry(entry: dict) -> bool:
    family = str(entry.get("family") or "")
    role = str(entry.get("sourceRole") or "")
    return family.startswith("a006") or role.startswith("a006")


def _a006_group_rank(entry: dict) -> int:
    """0 = twist seeds/geometry, 1 = borromean, 2 = non-A006."""
    if not isinstance(entry, dict):
        return 2
    family = str(entry.get("family") or "")
    if family.startswith("a006-borromean") or "borromean" in str(entry.get("sourceRole") or ""):
        return 1
    if _is_a006_entry(entry):
        return 0
    return 2


def sort_catalog_ids(database: dict) -> list[str]:
    """A006 seeds first, then borromean, then remaining IDs alphabetically."""
    return sorted(
        database,
        key=lambda cid: (_a006_group_rank(database[cid]), cid),
    )


def write_javascript(path: Path, database: dict, compact: bool) -> None:
    ids = sort_catalog_ids(database)
    if compact:
        ids_json = json.dumps(ids, ensure_ascii=False, separators=(",", ":"))
        db_json = json.dumps(database, ensure_ascii=False, separators=(",", ":"))
    else:
        ids_json = json.dumps(ids, ensure_ascii=False, indent=2)
        db_json = json.dumps(database, ensure_ascii=False, indent=2)

    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()
    content = f"""// Generated by build_knotplot_knots_data.py; do not hand-edit.
// KnotPlot relaxed/tight candidates converted from polygonal XYZ centerlines.
// A006 twist entries (family=a006-twist) are listed first for VortexLab UI grouping.
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
    parser.add_argument(
        "--strip-a006",
        action="store_true",
        help="remove existing family=a006-twist / sourceRole=a006* entries before upsert",
    )

    args = parser.parse_args()
    inputs = collect_inputs(args.inputs, args.scan, args.glob)
    if not inputs and not args.strip_a006:
        parser.error("provide input files or use --scan (or --strip-a006 alone)")
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

    if args.strip_a006:
        before = len(database)
        database = {
            cid: entry
            for cid, entry in database.items()
            if not (isinstance(entry, dict) and _is_a006_entry(entry))
        }
        stripped = before - len(database)
        print(f"stripped {stripped} A006 catalog entries ({len(database)} remain)")
        changed += stripped

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
