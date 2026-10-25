#!/usr/bin/env python3
"""
Build or update twist_knot_data.js from A006 RoundFolded Twist Knot Family XYZ.

Expected input format
---------------------
- One "x y z" vertex per line.
- Blank lines separate link components.
- Closed components are implicit: the last vertex connects to the first.

Filename conventions
--------------------
KNOT_<topology>_N<NNNN>_<ORIG|MIRROR>.xyz
KNOT_<topology>_N<NNNN>_<ORIG|MIRROR>_<ROUND|TIKZ_NATIVE>.xyz   (A006-v0.5.0/SEEDS)
LINK_<topology>_<FLAT|SOFT|BALANCED|TIGHT>_N<NNNN>_<ORIG|MIRROR>_<CPFIXED61|CPCENTER>.xyz
<topology>_N<NNNN>.xyz   (legacy Output/Seeds; treated as KNOT / ORIG)

Examples:
    KNOT_3_1_N1024_ORIG.xyz
    KNOT_4_1_N1024_ORIG_ROUND.xyz
    KNOT_10_1_N0512_MIRROR_TIKZ_NATIVE.xyz
    LINK_5_5_6_BALANCED_N1024_ORIG_CPFIXED61.xyz
    3_1_N1024.xyz

Component separators
--------------------
- Blank lines separate closed components, or
- Lines matching "Component <n>:" (qualification XYZ dumps).

Default behaviour
-----------------
- Catalog ID is the full filename stem (no collapse across N/chirality/profile).
- Converts each polygonal component to a discrete Fourier representation.
- Preserves all harmonics by default, including the Nyquist term.
- Emits filter metadata: kind, topology, profile, resolutionN, chirality, cpMode.
- Writes pretty-printed JS by default (KnotPlot-style indent=2; use --compact to minify).
- Non-matching stems can be ingested with --id plus metadata CLI overrides.

This is a static/candidate-geometry converter. It does not certify a global
ideal or ropelength-minimizing embedding.
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
from typing import Any

import numpy as np


DB_MARKER = "const TWIST_KNOT_DB = "
IDS_MARKER = "const TWIST_KNOT_IDS = "

PROFILES = ("FLAT", "SOFT", "BALANCED", "TIGHT")
CHIRALITIES = ("ORIG", "MIRROR")
CP_MODES = ("CPFIXED61", "CPCENTER")
KINDS = ("KNOT", "LINK")
SEED_VARIANTS = ("ROUND", "TIKZ_NATIVE")

# Default thin-catalog policy for VortexLab shipping copies (<50 MB).
DEFAULT_LINK_PROFILES = ("FLAT", "SOFT")
DEFAULT_LINK_RESOLUTIONS = (512, 1024)
EXCLUDED_LINK_PROFILES = ("BALANCED", "TIGHT")

TORUS_KNOT_TOPOLOGIES: dict[str, dict[str, int]] = {
    "3_1": {"p": 2, "q": 3},
    "5_1": {"p": 2, "q": 5},
    "7_1": {"p": 2, "q": 7},
    "9_1": {"p": 2, "q": 9},
    "11a367": {},
}

_COMPONENT_HEADER_RE = re.compile(r"^Component\s+\d+\s*:?\s*$", flags=re.IGNORECASE)

_KNOT_VARIANT_RE = re.compile(
    r"^(?P<kind>KNOT)_(?P<topology>.+)_N(?P<n>\d+)_(?P<chirality>ORIG|MIRROR)_"
    r"(?P<variant>ROUND|TIKZ_NATIVE)$",
    flags=re.IGNORECASE,
)
_KNOT_RE = re.compile(
    r"^(?P<kind>KNOT)_(?P<topology>.+)_N(?P<n>\d+)_(?P<chirality>ORIG|MIRROR)$",
    flags=re.IGNORECASE,
)
_LINK_RE = re.compile(
    r"^(?P<kind>LINK)_(?P<topology>.+)_"
    r"(?P<profile>FLAT|SOFT|BALANCED|TIGHT)_"
    r"N(?P<n>\d+)_(?P<chirality>ORIG|MIRROR)_"
    r"(?P<cp>CPFIXED61|CPCENTER)$",
    flags=re.IGNORECASE,
)
_SEED_RE = re.compile(
    r"^(?P<topology>\d+_\d+|\d+[a-z]+\d+)_N(?P<n>\d+)$",
    flags=re.IGNORECASE,
)


def torus_info(topology: str | None) -> dict | None:
    if not topology or topology not in TORUS_KNOT_TOPOLOGIES:
        return None
    params = TORUS_KNOT_TOPOLOGIES[topology]
    info: dict[str, Any] = {"class": "torus-knot"}
    if "p" in params and "q" in params:
        info["p"] = int(params["p"])
        info["q"] = int(params["q"])
        info["notation"] = f"T({info['p']},{info['q']})"
    return info


def selector_label_for(
    topology: str,
    torus: dict | None = None,
    seed_variant: str | None = None,
) -> str:
    parts: list[str] = [topology]
    if torus:
        notation = torus.get("notation")
        if notation:
            parts.append(str(notation))
        parts.append("torusknoop")
    if seed_variant:
        parts.append(str(seed_variant))
    return " · ".join(parts)


def apply_torus_labels(database: dict) -> int:
    changed = 0
    for entry in database.values():
        if not isinstance(entry, dict):
            continue
        topology = str(entry.get("topology") or "")
        info = torus_info(topology)
        if info is None:
            continue
        variant = entry.get("seedVariant")
        selector = selector_label_for(topology, info, variant)
        new_label = entry.get("label") or ""
        if "torusknoop" not in str(new_label):
            if info.get("notation"):
                new_label = f"{new_label} · {info['notation']} torusknoop".strip(" ·")
            else:
                new_label = f"{new_label} · torusknoop".strip(" ·")
        updates = {
            "torus": info,
            "selectorLabel": selector,
            "label": new_label,
        }
        if entry.get("kind") == "KNOT" and entry.get("family") in (None, "classic-knot"):
            updates["family"] = "torus-knot"
        if any(entry.get(key) != value for key, value in updates.items()):
            entry.update(updates)
            changed += 1
    return changed


def prune_superseded_knot_entries(database: dict, topologies: set[str]) -> list[str]:
    removed: list[str] = []
    legacy_knot = re.compile(
        r"^KNOT_(?P<topology>.+)_N\d+_(?:ORIG|MIRROR)$",
        flags=re.IGNORECASE,
    )
    legacy_short = re.compile(
        r"^(?P<topology>\d+_\d+|\d+[a-z]+\d+)_N\d+$",
        flags=re.IGNORECASE,
    )
    for catalog_id in list(database):
        knot = legacy_knot.fullmatch(catalog_id)
        short = legacy_short.fullmatch(catalog_id)
        topology = None
        if knot:
            topology = knot.group("topology")
        elif short:
            topology = short.group("topology")
        if topology and topology in topologies:
            del database[catalog_id]
            removed.append(catalog_id)
    return removed


def parse_xyz_components(path: Path) -> list[np.ndarray]:
    """Read components separated by blank lines or 'Component N:' headers."""
    components: list[np.ndarray] = []
    current: list[list[float]] = []

    def flush() -> None:
        nonlocal current
        if current:
            components.append(np.asarray(current, dtype=float))
            current = []

    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or _COMPONENT_HEADER_RE.fullmatch(stripped):
            flush()
            continue

        fields = stripped.replace(",", " ").split()
        if len(fields) < 3:
            continue
        try:
            xyz = [float(fields[0]), float(fields[1]), float(fields[2])]
        except ValueError:
            continue
        if not all(math.isfinite(v) for v in xyz):
            raise ValueError(f"{path}:{line_number}: non-finite coordinate")
        current.append(xyz)

    flush()

    if not components:
        raise ValueError(f"{path}: no XYZ components found")
    for index, component in enumerate(components, 1):
        if len(component) < 4:
            raise ValueError(f"{path}: component {index} has fewer than four vertices")
    return components


def parse_a006_source_name(path: Path) -> dict:
    """Parse A006 geometry or Seeds stem into filter metadata."""
    stem = path.stem
    knot_variant = _KNOT_VARIANT_RE.fullmatch(stem)
    knot = _KNOT_RE.fullmatch(stem)
    link = _LINK_RE.fullmatch(stem)
    seed = _SEED_RE.fullmatch(stem)

    seed_variant = None
    if knot_variant:
        kind = knot_variant.group("kind").upper()
        topology = knot_variant.group("topology")
        resolution_n = int(knot_variant.group("n"))
        chirality = knot_variant.group("chirality").upper()
        profile = None
        cp_mode = None
        seed_variant = knot_variant.group("variant").upper()
        family = "a006-seeds"
        source_kind = "seeds-pack"
    elif knot:
        kind = knot.group("kind").upper()
        topology = knot.group("topology")
        resolution_n = int(knot.group("n"))
        chirality = knot.group("chirality").upper()
        profile = None
        cp_mode = None
        family = "classic-knot"
        source_kind = "geometry"
    elif link:
        kind = link.group("kind").upper()
        topology = link.group("topology")
        resolution_n = int(link.group("n"))
        chirality = link.group("chirality").upper()
        profile = link.group("profile").upper()
        cp_mode = link.group("cp").upper()
        family = "classic-link"
        source_kind = "geometry"
    elif seed:
        kind = "KNOT"
        topology = seed.group("topology")
        resolution_n = int(seed.group("n"))
        chirality = "ORIG"
        profile = None
        cp_mode = None
        family = "a006-seed"
        source_kind = "seed"
    else:
        raise ValueError(
            f"{path.name}: stem does not match A006 KNOT_/LINK_/Seeds geometry pattern"
        )

    if resolution_n < 4:
        raise ValueError(f"{path.name}: resolution N={resolution_n} is too small")

    return {
        "canonical_id": stem,
        "kind": kind,
        "topology": topology,
        "profile": profile,
        "resolutionN": resolution_n,
        "chirality": chirality,
        "cpMode": cp_mode,
        "seedVariant": seed_variant,
        "family": family,
        "checkpoint_steps": resolution_n,
        "source_kind": source_kind,
    }


def resolve_name_metadata(
    path: Path,
    *,
    overrides: dict[str, Any] | None = None,
) -> dict:
    """Parse stem metadata, optionally filled/replaced by CLI overrides."""
    overrides = overrides or {}
    try:
        meta = parse_a006_source_name(path)
    except ValueError:
        if not overrides.get("kind") or not overrides.get("topology"):
            raise
        meta = {
            "canonical_id": path.stem,
            "kind": None,
            "topology": None,
            "profile": None,
            "resolutionN": None,
            "chirality": None,
            "cpMode": None,
            "seedVariant": None,
            "family": "a006-qualification",
            "checkpoint_steps": None,
            "source_kind": "qualification",
        }

    if overrides.get("kind"):
        meta["kind"] = str(overrides["kind"]).upper()
    if overrides.get("topology"):
        meta["topology"] = str(overrides["topology"])
    if "profile" in overrides and overrides["profile"] is not None:
        value = overrides["profile"]
        meta["profile"] = None if str(value).upper() in ("", "NONE", "NULL") else str(value).upper()
    if overrides.get("chirality"):
        meta["chirality"] = str(overrides["chirality"]).upper()
    if "cp_mode" in overrides and overrides["cp_mode"] is not None:
        value = overrides["cp_mode"]
        meta["cpMode"] = None if str(value).upper() in ("", "NONE", "NULL") else str(value).upper()
    if overrides.get("resolution_n") is not None:
        meta["resolutionN"] = int(overrides["resolution_n"])
        meta["checkpoint_steps"] = int(overrides["resolution_n"])

    if meta["kind"] not in KINDS:
        raise ValueError(f"{path.name}: kind must be KNOT or LINK (got {meta['kind']!r})")
    if not meta["topology"]:
        raise ValueError(f"{path.name}: topology is required")
    if meta["resolutionN"] is None:
        raise ValueError(f"{path.name}: resolution N is required (stem or --resolution-n)")
    if int(meta["resolutionN"]) < 4:
        raise ValueError(f"{path.name}: resolution N={meta['resolutionN']} is too small")
    if meta["chirality"] is None:
        meta["chirality"] = "ORIG"
    if meta.get("source_kind") is None:
        meta["source_kind"] = "geometry"
    if meta.get("family") is None:
        meta["family"] = "classic-knot" if meta["kind"] == "KNOT" else "classic-link"
    if meta.get("checkpoint_steps") is None:
        meta["checkpoint_steps"] = meta["resolutionN"]
    return meta


def entry_matches_filters(
    entry: dict,
    *,
    kind: str = "ALL",
    profile: str = "ALL",
    chirality: str = "ALL",
    resolution_n: int | None = None,
    cp_mode: str = "ALL",
) -> bool:
    """Pure filter predicate used by tests and mirrored in the UI."""
    entry_kind = str(entry.get("kind") or "").upper()
    if kind and kind.upper() not in ("ALL", ""):
        if entry_kind != kind.upper():
            return False

    if chirality and chirality.upper() not in ("ALL", ""):
        if str(entry.get("chirality") or "").upper() != chirality.upper():
            return False

    if resolution_n is not None:
        if int(entry.get("resolutionN") or -1) != int(resolution_n):
            return False

    entry_profile = entry.get("profile")
    if profile and profile.upper() not in ("ALL", ""):
        # Classic KNOT entries have no profile; profile filter applies to LINK only.
        if entry_kind == "LINK":
            if str(entry_profile or "").upper() != profile.upper():
                return False

    entry_cp = entry.get("cpMode")
    if cp_mode and cp_mode.upper() not in ("ALL", ""):
        if entry_kind == "LINK":
            if str(entry_cp or "").upper() != cp_mode.upper():
                return False

    return True


def parse_csv_tokens(raw: str | None) -> list[str]:
    if raw is None or not str(raw).strip():
        return []
    return [part.strip().upper() for part in str(raw).split(",") if part.strip()]


def parse_csv_ints(raw: str | None) -> list[int]:
    tokens = parse_csv_tokens(raw)
    values: list[int] = []
    for token in tokens:
        try:
            values.append(int(token))
        except ValueError as exc:
            raise ValueError(f"invalid integer list token {token!r}") from exc
    return values


def catalog_entry_allowed(
    entry: dict,
    *,
    link_profiles: tuple[str, ...] | list[str] | None = DEFAULT_LINK_PROFILES,
    link_resolutions: tuple[int, ...] | list[int] | None = DEFAULT_LINK_RESOLUTIONS,
) -> bool:
    """
    Shipping-catalog include filter.

    Non-LINK entries (knots, seeds) always pass. Qualification LINKs with a null
    profile also pass. Classic LINKs must match allowed profiles and resolutions.
    """
    if not isinstance(entry, dict):
        return False
    entry_kind = str(entry.get("kind") or "").upper()
    if entry_kind != "LINK":
        return True

    entry_profile = entry.get("profile")
    if entry_profile is None or str(entry_profile).strip() == "":
        # Qualification / no-profile links stay available under UI filter All.
        return True

    profile = str(entry_profile).upper()
    if link_profiles is not None:
        allowed = {str(p).upper() for p in link_profiles}
        if profile not in allowed:
            return False

    if link_resolutions is not None:
        try:
            resolution_n = int(entry.get("resolutionN") or -1)
        except (TypeError, ValueError):
            return False
        allowed_n = {int(n) for n in link_resolutions}
        if resolution_n not in allowed_n:
            return False

    return True


def prune_catalog_entries(
    database: dict,
    *,
    link_profiles: tuple[str, ...] | list[str] | None = DEFAULT_LINK_PROFILES,
    link_resolutions: tuple[int, ...] | list[int] | None = DEFAULT_LINK_RESOLUTIONS,
) -> list[str]:
    removed: list[str] = []
    for catalog_id in list(database):
        entry = database.get(catalog_id)
        if not catalog_entry_allowed(
            entry if isinstance(entry, dict) else {},
            link_profiles=link_profiles,
            link_resolutions=link_resolutions,
        ):
            del database[catalog_id]
            removed.append(catalog_id)
    return removed


def closed_edges(points: np.ndarray) -> np.ndarray:
    return np.roll(points, -1, axis=0) - points


def component_length(points: np.ndarray) -> float:
    return float(np.linalg.norm(closed_edges(points), axis=1).sum())


def dft_coefficients(points: np.ndarray, max_harmonic: int | None) -> tuple[list[dict], dict]:
    """
    Convert periodic samples to:
        r(t) = sum_I A_I cos(I t) + B_I sin(I t)
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
    chunks = [points + (k / factor) * (nxt - points) for k in range(factor)]
    return np.stack(chunks, axis=1).reshape(-1, 3)


def gauss_linking_midpoint(
    a: np.ndarray,
    b: np.ndarray,
    subdivisions: int = 4,
    batch_size: int = 192,
) -> float:
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


def read_sidecar_json(path: Path) -> dict | None:
    sidecar = path.with_suffix(".json")
    if not sidecar.exists():
        return None
    try:
        data = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{sidecar}: invalid sidecar JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{sidecar}: sidecar JSON must be an object")
    return data


def status_from_sidecar(sidecar: dict | None) -> tuple[str, str | None]:
    if not sidecar:
        return "static-candidate", (
            "A006 round-folded twist geometry; not certified as a global "
            "ideal/tight or ropelength-minimizing embedding."
        )
    status = str(sidecar.get("status") or "static-candidate")
    warnings: list[str] = []
    if status.upper() in {"SHARP_TURN_WARNING", "STATIC_CANDIDATE"}:
        warnings.append(f"sidecar status={status}")
    if str(sidecar.get("isotopy") or "").upper() == "UNRESOLVED":
        warnings.append("isotopy UNRESOLVED")
    if str(sidecar.get("KnotPlot") or "").upper() == "NOT_RUN":
        warnings.append("KnotPlot NOT_RUN")
    warning = (
        "; ".join(warnings)
        + ". A006 candidate geometry; not a global ideal/tight certification."
        if warnings
        else (
            "A006 round-folded twist geometry; not certified as a global "
            "ideal/tight or ropelength-minimizing embedding."
        )
    )
    return status, warning


def build_entry(
    path: Path,
    *,
    max_harmonic: int | None,
    linking_subdivisions: int,
    id_override: str | None = None,
    overrides: dict[str, Any] | None = None,
) -> tuple[str, dict]:
    components = parse_xyz_components(path)
    overrides = dict(overrides or {})
    known_stem = (
        _KNOT_VARIANT_RE.fullmatch(path.stem)
        or _KNOT_RE.fullmatch(path.stem)
        or _LINK_RE.fullmatch(path.stem)
        or _SEED_RE.fullmatch(path.stem)
    )
    if overrides.get("resolution_n") is None and not known_stem:
        overrides["resolution_n"] = int(min(len(c) for c in components))

    name_metadata = resolve_name_metadata(path, overrides=overrides)
    catalog_id = id_override or name_metadata["canonical_id"]
    geometry = geometry_metadata(components)
    sidecar = read_sidecar_json(path)
    status, warning = status_from_sidecar(sidecar)

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

    kind = name_metadata["kind"]
    topology = name_metadata["topology"]
    profile = name_metadata["profile"]
    resolution_n = int(name_metadata["resolutionN"])
    chirality = name_metadata["chirality"]
    cp_mode = name_metadata["cpMode"]
    seed_variant = name_metadata.get("seedVariant")
    source_kind = name_metadata.get("source_kind") or "geometry"
    torus = torus_info(topology)
    family = name_metadata["family"]
    if torus is not None and kind == "KNOT" and family == "classic-knot":
        family = "torus-knot"

    if source_kind == "seeds-pack":
        label = f"{catalog_id} / A006 SEEDS {seed_variant} N{resolution_n}"
        source = (
            "A006-v0.5.0/SEEDS polygonal XYZ (ROUND/TIKZ_NATIVE pack) converted "
            "to discrete Fourier series"
        )
        source_role = f"a006-seeds-{str(seed_variant).lower()}-N{resolution_n}"
        source_note = (
            "Static/candidate geometry from A006-v0.5.0/SEEDS. "
            "Coordinates remain in the A006 source frame (not D=1). "
            "Replaces legacy Output/v050/geometry and Output/Seeds for the "
            "same topology where present."
        )
        source_format = "XYZ vertices; blank lines separate closed components"
    elif source_kind == "seed":
        label = f"{catalog_id} / A006 seed N{resolution_n}"
        source = (
            "A006 RoundFolded Twist Knot Family Seeds polygonal XYZ converted "
            "to discrete Fourier series"
        )
        source_role = f"a006-seed-N{resolution_n}"
        source_note = (
            "Static/candidate geometry from A006 v0.5.0 Output/Seeds. "
            "Coordinates remain in the A006 source frame (not D=1). "
            "Filter fields support VortexLab UI selection; this is not an "
            "ideal/tight certificate."
        )
        source_format = "XYZ vertices; blank lines separate closed components"
    elif source_kind == "qualification":
        profile_label = profile or "no-profile"
        cp_label = cp_mode or "no-cp"
        label = (
            f"{catalog_id} / A006 qualification N{resolution_n} "
            f"{profile_label} {chirality} {cp_label}"
        )
        source = (
            "A006 qualification_v050c polygonal XYZ converted to discrete "
            "Fourier series"
        )
        source_role = f"a006-qualification-N{resolution_n}"
        source_note = (
            "Static/candidate geometry from A006 qualification_v050c run export. "
            "Coordinates remain in the A006 source frame (not D=1). "
            "Null profile/CP match only when those UI filters are All."
        )
        source_format = (
            "XYZ vertices; blank lines or 'Component N:' headers separate "
            "closed components"
        )
    elif kind == "KNOT":
        label = f"{catalog_id} / A006 native N{resolution_n}"
        source = (
            "A006 RoundFolded Twist Knot Family polygonal XYZ converted to "
            "discrete Fourier series"
        )
        source_role = f"a006-native-N{resolution_n}"
        source_note = (
            "Static/candidate geometry from A006 v0.5.0 Output/v050/geometry. "
            "Coordinates remain in the A006 source frame (not D=1). "
            "Filter fields support VortexLab UI selection; this is not an "
            "ideal/tight certificate."
        )
        source_format = "XYZ vertices; blank lines separate closed components"
    else:
        label = (
            f"{catalog_id} / A006 native N{resolution_n} "
            f"{profile} {chirality} {cp_mode}"
        )
        source = (
            "A006 RoundFolded Twist Knot Family polygonal XYZ converted to "
            "discrete Fourier series"
        )
        source_role = f"a006-native-N{resolution_n}"
        source_note = (
            "Static/candidate geometry from A006 v0.5.0 Output/v050/geometry. "
            "Coordinates remain in the A006 source frame (not D=1). "
            "Filter fields support VortexLab UI selection; this is not an "
            "ideal/tight certificate."
        )
        source_format = "XYZ vertices; blank lines separate closed components"

    if torus is not None:
        if torus.get("notation"):
            label = f"{label} · {torus['notation']} torusknoop"
        else:
            label = f"{label} · torusknoop"
    selector_label = selector_label_for(str(topology), torus, seed_variant)

    source_sha = None
    if sidecar and isinstance(sidecar.get("sha256"), str):
        source_sha = sidecar["sha256"]
    if not source_sha:
        source_sha = sha256_file(path)

    linking = linking_metadata(components, linking_subdivisions)

    entry = {
        "knotId": catalog_id,
        "label": label,
        "selectorLabel": selector_label,
        "sourceFile": path.name,
        "sourceSha256": source_sha,
        "source": source,
        "sourceFormat": source_format,
        "sourceRole": source_role,
        "sourceMaster": sidecar.get("source_master") if sidecar else None,
        "generator": "build_twist_knot_data.py",
        "ideal": False,
        "status": status,
        "warning": warning,
        "family": family,
        "kind": kind,
        "topology": topology,
        "profile": profile,
        "resolutionN": resolution_n,
        "chirality": chirality,
        "cpMode": cp_mode,
        "seedVariant": seed_variant,
        "checkpointSteps": name_metadata["checkpoint_steps"],
        "normalization": {
            "label": f"native-N{resolution_n}",
            "D": None,
            "method": (
                f"A006 polygonal centerline at native bead count N={resolution_n}; "
                "no VortexLab uniform resample and no D=1 diameter certification"
            ),
            "note": source_note,
        },
        "D": None,
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
            "TWIST_KNOT_DB declaration"
        )
    json_start = marker_index + len(DB_MARKER)
    decoder = json.JSONDecoder()
    database, _ = decoder.raw_decode(text[json_start:].lstrip())
    if not isinstance(database, dict):
        raise ValueError(f"{path}: TWIST_KNOT_DB is not an object")
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
    content = f"""// Generated by build_twist_knot_data.py; do not hand-edit.
// A006 RoundFolded Twist Knot Family polygonal XYZ converted to discrete Fourier series.
// Sources: v050/geometry (KNOT_/LINK_), Output/Seeds, optional qualification XYZ.
// Native A006 bead counts; UI filters (kind/profile/chirality/N/CP) select subsets.
// not VortexLab uniform-N300 / D=1 KnotPlot polish.
// Generated at: {generated_at}
const TWIST_KNOT_IDS = {ids_json};
const TWIST_KNOT_DB = {db_json};

if (typeof window !== "undefined") {{
  window.TWIST_KNOT_IDS = TWIST_KNOT_IDS;
  window.TWIST_KNOT_DB = TWIST_KNOT_DB;
}}
"""
    path.write_text(content, encoding="utf-8")


def collect_inputs(
    positional: list[Path],
    scans: list[Path] | None,
    glob_pattern: str,
) -> list[Path]:
    candidates = list(positional)
    for scan in scans or []:
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
        description="Build/update twist_knot_data.js from A006 geometry XYZ exports."
    )
    parser.add_argument("inputs", nargs="*", type=Path, help="A006 .xyz geometry files")
    parser.add_argument(
        "--scan",
        action="append",
        type=Path,
        help="scan this directory (repeatable)",
    )
    parser.add_argument(
        "--glob",
        default="*.xyz",
        help="glob used with --scan (default: *.xyz)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("twist_knot_data.js"),
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
        "--id",
        dest="id_override",
        help="catalog ID override; valid only with one input",
    )
    parser.add_argument(
        "--kind",
        choices=KINDS,
        help="metadata override: KNOT or LINK (required with non-matching stems)",
    )
    parser.add_argument(
        "--topology",
        help="metadata override: topology token (required with non-matching stems)",
    )
    parser.add_argument(
        "--profile",
        help="metadata override: FLAT|SOFT|BALANCED|TIGHT or NONE",
    )
    parser.add_argument(
        "--chirality",
        choices=CHIRALITIES,
        help="metadata override: ORIG or MIRROR",
    )
    parser.add_argument(
        "--cp-mode",
        dest="cp_mode",
        help="metadata override: CPFIXED61|CPCENTER or NONE",
    )
    parser.add_argument(
        "--resolution-n",
        dest="resolution_n",
        type=int,
        help="metadata override: bead-count filter field N",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing entry even with an older/unknown resolution",
    )
    parser.add_argument(
        "--compact",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="compact JSON in JS output (default: off; pretty indent=2 like KnotPlot)",
    )
    parser.add_argument("--dry-run", action="store_true", help="validate without writing")
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="ignore any existing output database and rebuild from scratch",
    )
    parser.add_argument(
        "--relabel-torus",
        action="store_true",
        help="patch torus-knot labels on the existing catalog; can run with no XYZ",
    )
    parser.add_argument(
        "--prune-replaced-knots",
        action="store_true",
        help=(
            "after ingesting A006-v0.5.0/SEEDS ROUND/TIKZ_NATIVE files, remove "
            "legacy geometry/Output-Seeds IDs for those topologies"
        ),
    )
    parser.add_argument(
        "--prune-catalog",
        action="store_true",
        help=(
            "drop classic LINK entries outside --link-profiles / --link-resolutions "
            "(default FLAT,SOFT and 512,1024); can run with no XYZ"
        ),
    )
    parser.add_argument(
        "--link-profiles",
        default=",".join(DEFAULT_LINK_PROFILES),
        help=(
            "comma-separated classic LINK profiles kept by --prune-catalog / ingest "
            f"filter (default: {','.join(DEFAULT_LINK_PROFILES)})"
        ),
    )
    parser.add_argument(
        "--link-resolutions",
        default=",".join(str(n) for n in DEFAULT_LINK_RESOLUTIONS),
        help=(
            "comma-separated classic LINK N values kept by --prune-catalog / ingest "
            f"filter (default: {','.join(str(n) for n in DEFAULT_LINK_RESOLUTIONS)})"
        ),
    )
    parser.add_argument(
        "--apply-link-catalog-filter",
        action="store_true",
        help=(
            "skip ingesting classic LINK XYZ that fail --link-profiles/--link-resolutions "
            "(also applied automatically with --prune-catalog)"
        ),
    )

    args = parser.parse_args()
    inputs = collect_inputs(args.inputs, args.scan, args.glob)
    if not inputs and not args.relabel_torus and not args.prune_catalog:
        parser.error(
            "provide input files, use --scan, or pass --relabel-torus / --prune-catalog"
        )
    meta_override_used = any(
        getattr(args, name) is not None
        for name in ("kind", "topology", "profile", "chirality", "cp_mode", "resolution_n")
    )
    if args.id_override and len(inputs) != 1:
        parser.error("--id is valid only with exactly one input")
    if meta_override_used and len(inputs) != 1:
        parser.error("metadata overrides are valid only with exactly one input")
    if args.link_subdivisions < 1:
        parser.error("--link-subdivisions must be at least 1")

    try:
        link_profiles = tuple(parse_csv_tokens(args.link_profiles))
        link_resolutions = tuple(parse_csv_ints(args.link_resolutions))
    except ValueError as exc:
        parser.error(str(exc))
    if not link_profiles:
        parser.error("--link-profiles must list at least one profile")
    if not link_resolutions:
        parser.error("--link-resolutions must list at least one N")

    apply_link_filter = bool(args.prune_catalog or args.apply_link_catalog_filter)

    if str(args.max_harmonic).lower() == "full":
        max_harmonic = None
    else:
        try:
            max_harmonic = int(args.max_harmonic)
        except ValueError:
            parser.error("--max-harmonic must be 'full' or a non-negative integer")
        if max_harmonic < 0:
            parser.error("--max-harmonic must be non-negative")

    overrides: dict[str, Any] = {}
    if args.kind is not None:
        overrides["kind"] = args.kind
    if args.topology is not None:
        overrides["topology"] = args.topology
    if args.profile is not None:
        overrides["profile"] = args.profile
    if args.chirality is not None:
        overrides["chirality"] = args.chirality
    if args.cp_mode is not None:
        overrides["cp_mode"] = args.cp_mode
    if args.resolution_n is not None:
        overrides["resolution_n"] = args.resolution_n

    database: dict = {} if args.fresh else read_existing_database(args.output)
    changed = 0
    skipped_link_filter = 0
    seeds_pack_topologies: set[str] = set()

    for input_path in inputs:
        if not input_path.exists():
            raise FileNotFoundError(input_path)

        catalog_id, entry = build_entry(
            input_path,
            max_harmonic=max_harmonic,
            linking_subdivisions=args.link_subdivisions,
            id_override=args.id_override,
            overrides=overrides or None,
        )
        if apply_link_filter and not catalog_entry_allowed(
            entry,
            link_profiles=link_profiles,
            link_resolutions=link_resolutions,
        ):
            skipped_link_filter += 1
            print(
                f"skipped link catalog filter: {catalog_id} <- {input_path.name}; "
                f"profile={entry.get('profile')}; N={entry.get('resolutionN')}"
            )
            continue

        if entry.get("seedVariant") and entry.get("topology"):
            seeds_pack_topologies.add(str(entry["topology"]))

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
            action = "skipped older resolution"

        link_matrix = entry["pairwiseLinking"]["roundedMatrix"]
        print(
            f"{action}: {catalog_id} <- {input_path.name}; "
            f"{entry['componentCount']} components; "
            f"N={entry['resolutionN']}; "
            f"L={entry['L']:.12g}; linking={link_matrix}"
        )

    if args.prune_replaced_knots or seeds_pack_topologies:
        topologies = seeds_pack_topologies
        if args.prune_replaced_knots and not topologies:
            topologies = {
                str(entry.get("topology"))
                for entry in database.values()
                if isinstance(entry, dict) and entry.get("seedVariant")
            }
        removed = prune_superseded_knot_entries(database, topologies)
        if removed:
            print(
                f"pruned {len(removed)} legacy knot IDs for topologies "
                f"{sorted(topologies)}"
            )

    catalog_pruned = 0
    if args.prune_catalog:
        removed = prune_catalog_entries(
            database,
            link_profiles=link_profiles,
            link_resolutions=link_resolutions,
        )
        catalog_pruned = len(removed)
        if removed:
            print(
                f"pruned {catalog_pruned} classic LINK IDs outside profiles "
                f"{list(link_profiles)} N={list(link_resolutions)}"
            )

    relabeled = 0
    if args.relabel_torus or inputs:
        relabeled = apply_torus_labels(database)
        if relabeled:
            print(f"relabeled torus entries: {relabeled}")

    if args.dry_run:
        print(
            f"dry run: {changed} catalog entries would change; "
            f"scanned {len(inputs)}; skipped link filter {skipped_link_filter}; "
            f"catalog prune {catalog_pruned}; torus relabel {relabeled}"
        )
        return 0

    write_javascript(args.output, database, args.compact)
    print(
        f"wrote {args.output} with {len(database)} entries"
        + (f" (skipped link filter {skipped_link_filter})" if skipped_link_filter else "")
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
